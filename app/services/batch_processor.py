"""批量处理引擎"""

from typing import Dict, Any, List, Optional
from app.models.batch_task import BatchTask, QueryResult
from app.services.task_queue import TaskQueue
from app.services.rag_service import RAGService
import asyncio
import logging

logger = logging.getLogger(__name__)


class BatchProcessor:
    """批量处理引擎
    
    处理离线批量任务，支持任务队列管理和并发处理。
    """
    
    def __init__(self, rag_service: RAGService, config: Optional[Dict[str, Any]] = None):
        """初始化批量处理器
        
        Args:
            rag_service: RAG服务实例
            config: 批量处理配置
        """
        self.rag_service = rag_service
        self.config = config or {}
        
        # 任务队列
        max_queue_size = self.config.get("max_queue_size", 1000)
        self.task_queue = TaskQueue(max_size=max_queue_size)
        
        # 并发控制
        self.max_concurrent = self.config.get("max_concurrent", 5)
        self.semaphore = asyncio.Semaphore(self.max_concurrent)
        
        # 处理器状态
        self.is_running = False
        self.worker_task: Optional[asyncio.Task] = None
    
    async def start(self) -> None:
        """启动批量处理器"""
        if self.is_running:
            logger.warning("Batch processor is already running")
            return
        
        self.is_running = True
        self.worker_task = asyncio.create_task(self._worker_loop())
        logger.info("Batch processor started")
    
    async def stop(self) -> None:
        """停止批量处理器"""
        if not self.is_running:
            return
        
        self.is_running = False
        
        if self.worker_task:
            self.worker_task.cancel()
            try:
                await self.worker_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Batch processor stopped")
    
    async def _worker_loop(self) -> None:
        """工作循环，处理队列中的任务"""
        logger.info("Batch processor worker loop started")
        
        while self.is_running:
            try:
                # 获取下一个任务
                task = await self.task_queue.get_next_task()
                
                if task:
                    # 异步处理任务
                    asyncio.create_task(self._process_task(task))
                else:
                    # 没有任务，等待一段时间
                    await asyncio.sleep(1)
                    
            except Exception as e:
                logger.error(f"Error in worker loop: {e}")
                await asyncio.sleep(1)
    
    async def _process_task(self, task: BatchTask) -> None:
        """处理单个任务
        
        Args:
            task: 批量处理任务
        """
        async with self.semaphore:
            try:
                logger.info(f"Processing task: {task.task_id}")
                
                # 开始任务
                task.start()
                
                # 处理所有文本
                results: List[QueryResult] = []
                completed = 0
                failed = 0
                
                # 并发处理文本
                tasks = []
                for text in task.texts:
                    tasks.append(self._process_single_text(text, task.options))
                
                # 等待所有处理完成
                for coro in asyncio.as_completed(tasks):
                    try:
                        result = await coro
                        results.append(result)
                        completed += 1
                    except Exception as e:
                        logger.error(f"Failed to process text: {e}")
                        # 创建错误结果
                        results.append(QueryResult(
                            content=f"处理失败: {str(e)}",
                            metadata={"error": True}
                        ))
                        failed += 1
                    
                    # 更新进度
                    task.update_progress(completed, failed)
                
                # 保存结果
                task.results = results
                task.complete()
                
                # 标记任务完成
                await self.task_queue.complete_task(task.task_id)
                
                logger.info(f"Task completed: {task.task_id}, success: {completed}, failed: {failed}")
                
            except Exception as e:
                logger.error(f"Task processing failed: {task.task_id}, error: {e}")
                await self.task_queue.fail_task(task.task_id, str(e))
    
    async def _process_single_text(self, text: str, options: Dict[str, Any]) -> QueryResult:
        """处理单个文本
        
        Args:
            text: 待处理文本
            options: 处理选项
            
        Returns:
            QueryResult: 处理结果
        """
        # 使用RAG服务处理文本
        return await self.rag_service.query(text, **options)
    
    async def submit_task(self, name: str, texts: List[str], 
                         options: Optional[Dict[str, Any]] = None,
                         description: Optional[str] = None) -> BatchTask:
        """提交批量处理任务
        
        Args:
            name: 任务名称
            texts: 待处理文本列表
            options: 处理选项
            description: 任务描述
            
        Returns:
            BatchTask: 创建的任务
            
        Raises:
            Exception: 如果提交失败
        """
        # 创建任务
        task = BatchTask.create(name, texts, options, description)
        
        # 提交到队列
        await self.task_queue.submit_task(task)
        
        logger.info(f"Task submitted: {task.task_id}, texts count: {len(texts)}")
        
        return task
    
    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务状态
        
        Args:
            task_id: 任务ID
            
        Returns:
            Optional[Dict[str, Any]]: 任务状态，如果不存在返回None
        """
        task = await self.task_queue.get_task(task_id)
        
        if not task:
            return None
        
        return task.to_dict()
    
    async def get_task_results(self, task_id: str, 
                              page: int = 1, size: int = 100) -> Optional[Dict[str, Any]]:
        """获取任务结果
        
        Args:
            task_id: 任务ID
            page: 页码
            size: 每页大小
            
        Returns:
            Optional[Dict[str, Any]]: 任务结果，如果不存在返回None
        """
        task = await self.task_queue.get_task(task_id)
        
        if not task or not task.results:
            return None
        
        # 分页处理
        start = (page - 1) * size
        end = start + size
        page_results = task.results[start:end]
        
        return {
            "task_id": task.task_id,
            "results": [r.to_dict() for r in page_results],
            "total": len(task.results),
            "page": page,
            "size": size
        }
    
    async def cancel_task(self, task_id: str) -> bool:
        """取消任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            bool: 如果成功取消返回True
        """
        return await self.task_queue.cancel_task(task_id)
    
    async def list_tasks(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """列出所有任务
        
        Args:
            status: 可选的状态过滤
            
        Returns:
            List[Dict[str, Any]]: 任务列表
        """
        tasks = await self.task_queue.list_tasks(status)
        return [t.to_dict() for t in tasks]
    
    async def get_status(self) -> Dict[str, Any]:
        """获取批量处理器状态
        
        Returns:
            Dict[str, Any]: 状态信息
        """
        queue_status = await self.task_queue.get_queue_status()
        
        return {
            "is_running": self.is_running,
            "max_concurrent": self.max_concurrent,
            "queue": queue_status
        }


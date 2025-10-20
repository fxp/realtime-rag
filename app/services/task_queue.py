"""任务队列管理"""

from typing import Dict, List, Optional
from app.models.batch_task import BatchTask
import asyncio
import logging
from collections import deque

logger = logging.getLogger(__name__)


class TaskQueue:
    """任务队列管理器
    
    管理批量处理任务的队列，支持任务调度、状态管理和优先级处理。
    当前实现使用内存队列，未来可以扩展为Redis或数据库支持。
    """
    
    def __init__(self, max_size: int = 1000):
        """初始化任务队列
        
        Args:
            max_size: 队列最大大小
        """
        self.max_size = max_size
        self.tasks: Dict[str, BatchTask] = {}
        self.pending_queue: deque = deque()
        self.running_tasks: Dict[str, BatchTask] = {}
        self._lock = asyncio.Lock()
    
    async def submit_task(self, task: BatchTask) -> str:
        """提交任务到队列
        
        Args:
            task: 批量处理任务
            
        Returns:
            str: 任务ID
            
        Raises:
            Exception: 如果队列已满
        """
        async with self._lock:
            # 检查队列大小
            if len(self.tasks) >= self.max_size:
                raise Exception("任务队列已满，请稍后再试")
            
            # 添加任务
            self.tasks[task.task_id] = task
            self.pending_queue.append(task.task_id)
            
            logger.info(f"Task submitted: {task.task_id}, queue size: {len(self.pending_queue)}")
            
            return task.task_id
    
    async def get_next_task(self) -> Optional[BatchTask]:
        """获取下一个待处理任务
        
        Returns:
            Optional[BatchTask]: 下一个任务，如果队列为空返回None
        """
        async with self._lock:
            if not self.pending_queue:
                return None
            
            task_id = self.pending_queue.popleft()
            task = self.tasks.get(task_id)
            
            if task and task.status == "pending":
                self.running_tasks[task_id] = task
                return task
            
            return None
    
    async def complete_task(self, task_id: str) -> None:
        """标记任务为已完成
        
        Args:
            task_id: 任务ID
        """
        async with self._lock:
            if task_id in self.running_tasks:
                del self.running_tasks[task_id]
            
            task = self.tasks.get(task_id)
            if task:
                logger.info(f"Task completed: {task_id}")
    
    async def fail_task(self, task_id: str, error_message: str) -> None:
        """标记任务为失败
        
        Args:
            task_id: 任务ID
            error_message: 错误信息
        """
        async with self._lock:
            if task_id in self.running_tasks:
                del self.running_tasks[task_id]
            
            task = self.tasks.get(task_id)
            if task:
                task.fail(error_message)
                logger.error(f"Task failed: {task_id}, error: {error_message}")
    
    async def cancel_task(self, task_id: str) -> bool:
        """取消任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            bool: 如果成功取消返回True
        """
        async with self._lock:
            task = self.tasks.get(task_id)
            
            if not task:
                return False
            
            # 只能取消pending或running状态的任务
            if task.status not in ["pending", "running"]:
                return False
            
            # 从队列中移除
            if task_id in list(self.pending_queue):
                self.pending_queue.remove(task_id)
            
            # 从运行中任务移除
            if task_id in self.running_tasks:
                del self.running_tasks[task_id]
            
            task.cancel()
            logger.info(f"Task cancelled: {task_id}")
            
            return True
    
    async def get_task(self, task_id: str) -> Optional[BatchTask]:
        """获取任务信息
        
        Args:
            task_id: 任务ID
            
        Returns:
            Optional[BatchTask]: 任务对象，如果不存在返回None
        """
        return self.tasks.get(task_id)
    
    async def list_tasks(self, status: Optional[str] = None) -> List[BatchTask]:
        """列出所有任务
        
        Args:
            status: 可选的状态过滤
            
        Returns:
            List[BatchTask]: 任务列表
        """
        tasks = list(self.tasks.values())
        
        if status:
            tasks = [t for t in tasks if t.status == status]
        
        # 按创建时间倒序排序
        tasks.sort(key=lambda t: t.created_at, reverse=True)
        
        return tasks
    
    async def get_queue_status(self) -> Dict[str, any]:
        """获取队列状态
        
        Returns:
            Dict[str, any]: 队列状态信息
        """
        async with self._lock:
            return {
                "total_tasks": len(self.tasks),
                "pending": len(self.pending_queue),
                "running": len(self.running_tasks),
                "max_size": self.max_size,
                "available_slots": self.max_size - len(self.tasks)
            }
    
    async def cleanup_old_tasks(self, max_age_hours: int = 24) -> int:
        """清理旧任务
        
        Args:
            max_age_hours: 最大保留时间（小时）
            
        Returns:
            int: 清理的任务数量
        """
        from datetime import datetime, timedelta
        
        async with self._lock:
            cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
            to_remove = []
            
            for task_id, task in self.tasks.items():
                # 只清理已完成、失败或取消的旧任务
                if task.status in ["completed", "failed", "cancelled"]:
                    if task.completed_at and task.completed_at < cutoff_time:
                        to_remove.append(task_id)
            
            for task_id in to_remove:
                del self.tasks[task_id]
            
            logger.info(f"Cleaned up {len(to_remove)} old tasks")
            
            return len(to_remove)


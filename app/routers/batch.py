"""批量处理API路由"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from app.services.batch_processor import BatchProcessor

# 创建路由器
router = APIRouter(prefix="/api/batch", tags=["Batch Processing"])

# 全局批量处理器实例（由main.py初始化）
batch_processor: Optional[BatchProcessor] = None


def set_batch_processor(processor: BatchProcessor):
    """设置批量处理器实例
    
    Args:
        processor: 批量处理器实例
    """
    global batch_processor
    batch_processor = processor


# Pydantic模型
class BatchTaskRequest(BaseModel):
    """批量任务请求模型"""
    name: str = Field(..., description="任务名称", max_length=100)
    texts: List[str] = Field(..., description="待处理文本列表", min_items=1, max_items=10000)
    description: Optional[str] = Field(None, description="任务描述", max_length=500)
    options: Optional[Dict[str, Any]] = Field(default_factory=dict, description="处理选项")


class BatchTaskResponse(BaseModel):
    """批量任务响应模型"""
    task_id: str
    status: str
    created_at: str


class ErrorResponse(BaseModel):
    """错误响应模型"""
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None


@router.post("/tasks", response_model=BatchTaskResponse, status_code=201)
async def submit_batch_task(request: BatchTaskRequest):
    """提交批量处理任务
    
    Args:
        request: 批量任务请求
        
    Returns:
        BatchTaskResponse: 任务提交响应
        
    Raises:
        HTTPException: 如果提交失败
    """
    if not batch_processor:
        raise HTTPException(status_code=503, detail="批量处理服务不可用")
    
    try:
        task = await batch_processor.submit_task(
            name=request.name,
            texts=request.texts,
            options=request.options,
            description=request.description
        )
        
        return BatchTaskResponse(
            task_id=task.task_id,
            status=task.status,
            created_at=task.created_at.isoformat()
        )
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/tasks/{task_id}")
async def get_batch_task_status(task_id: str):
    """获取任务状态
    
    Args:
        task_id: 任务ID
        
    Returns:
        Dict: 任务状态信息
        
    Raises:
        HTTPException: 如果任务不存在
    """
    if not batch_processor:
        raise HTTPException(status_code=503, detail="批量处理服务不可用")
    
    status = await batch_processor.get_task_status(task_id)
    
    if not status:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    return status


@router.delete("/tasks/{task_id}")
async def cancel_batch_task(task_id: str):
    """取消任务
    
    Args:
        task_id: 任务ID
        
    Returns:
        Dict: 取消结果
        
    Raises:
        HTTPException: 如果取消失败
    """
    if not batch_processor:
        raise HTTPException(status_code=503, detail="批量处理服务不可用")
    
    success = await batch_processor.cancel_task(task_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="任务不存在或无法取消")
    
    return {"message": "Task cancelled successfully"}


@router.get("/tasks/{task_id}/results")
async def get_batch_task_results(
    task_id: str,
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(100, ge=1, le=1000, description="每页大小")
):
    """获取任务结果
    
    Args:
        task_id: 任务ID
        page: 页码
        size: 每页大小
        
    Returns:
        Dict: 任务结果
        
    Raises:
        HTTPException: 如果任务不存在
    """
    if not batch_processor:
        raise HTTPException(status_code=503, detail="批量处理服务不可用")
    
    results = await batch_processor.get_task_results(task_id, page, size)
    
    if not results:
        raise HTTPException(status_code=404, detail="任务不存在或结果不可用")
    
    return results


@router.get("/tasks")
async def list_batch_tasks(status: Optional[str] = Query(None, description="状态过滤")):
    """列出所有任务
    
    Args:
        status: 可选的状态过滤
        
    Returns:
        Dict: 任务列表
    """
    if not batch_processor:
        raise HTTPException(status_code=503, detail="批量处理服务不可用")
    
    tasks = await batch_processor.list_tasks(status)
    
    return {
        "tasks": tasks,
        "total": len(tasks)
    }


@router.get("/status")
async def get_batch_processor_status():
    """获取批量处理器状态
    
    Returns:
        Dict: 批量处理器状态
    """
    if not batch_processor:
        raise HTTPException(status_code=503, detail="批量处理服务不可用")
    
    return await batch_processor.get_status()

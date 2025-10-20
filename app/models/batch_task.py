"""批量处理任务和查询结果数据模型"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid


@dataclass
class QueryResult:
    """查询结果数据模型
    
    统一的查询结果格式，用于标准化不同提供商的返回结果。
    """
    
    content: str
    """主要回答内容"""
    
    metadata: Optional[Dict[str, Any]] = None
    """元数据信息，如提供商、模型、处理时间等"""
    
    sources: Optional[List[Dict[str, Any]]] = None
    """来源信息列表，包含标题、URL、相关性等"""
    
    usage: Optional[Dict[str, Any]] = None
    """使用统计信息，如token数量、成本等"""
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "content": self.content,
            "metadata": self.metadata,
            "sources": self.sources,
            "usage": self.usage
        }


@dataclass
class BatchTask:
    """批量处理任务数据模型
    
    用于管理离线批量处理任务的完整信息。
    """
    
    task_id: str
    """任务唯一标识符"""
    
    name: str
    """任务名称"""
    
    texts: List[str]
    """待处理文本列表"""
    
    options: Dict[str, Any] = field(default_factory=dict)
    """处理选项，包含提供商、并发数等配置"""
    
    status: str = "pending"
    """任务状态：pending, running, completed, failed, cancelled"""
    
    progress: Dict[str, int] = field(default_factory=lambda: {
        "total": 0,
        "completed": 0,
        "failed": 0
    })
    """进度信息"""
    
    results: Optional[List[QueryResult]] = None
    """处理结果列表"""
    
    created_at: datetime = field(default_factory=datetime.now)
    """创建时间"""
    
    started_at: Optional[datetime] = None
    """开始时间"""
    
    completed_at: Optional[datetime] = None
    """完成时间"""
    
    error_message: Optional[str] = None
    """错误信息"""
    
    description: Optional[str] = None
    """任务描述"""
    
    @classmethod
    def create(cls, name: str, texts: List[str], 
               options: Optional[Dict[str, Any]] = None,
               description: Optional[str] = None) -> "BatchTask":
        """创建新的批量处理任务
        
        Args:
            name: 任务名称
            texts: 待处理文本列表
            options: 处理选项
            description: 任务描述
            
        Returns:
            新创建的BatchTask实例
        """
        task_id = str(uuid.uuid4())
        progress = {
            "total": len(texts),
            "completed": 0,
            "failed": 0
        }
        
        return cls(
            task_id=task_id,
            name=name,
            texts=texts,
            options=options or {},
            progress=progress,
            description=description
        )
    
    def start(self) -> None:
        """开始处理任务"""
        self.status = "running"
        self.started_at = datetime.now()
    
    def complete(self) -> None:
        """完成任务"""
        self.status = "completed"
        self.completed_at = datetime.now()
    
    def fail(self, error_message: str) -> None:
        """任务失败
        
        Args:
            error_message: 错误信息
        """
        self.status = "failed"
        self.error_message = error_message
        self.completed_at = datetime.now()
    
    def cancel(self) -> None:
        """取消任务"""
        self.status = "cancelled"
        self.completed_at = datetime.now()
    
    def update_progress(self, completed: int, failed: int) -> None:
        """更新进度
        
        Args:
            completed: 已完成数量
            failed: 失败数量
        """
        self.progress["completed"] = completed
        self.progress["failed"] = failed
    
    def get_progress_percentage(self) -> float:
        """获取进度百分比
        
        Returns:
            进度百分比（0-100）
        """
        total = self.progress["total"]
        if total == 0:
            return 0.0
        
        completed = self.progress["completed"] + self.progress["failed"]
        return (completed / total) * 100
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "task_id": self.task_id,
            "name": self.name,
            "description": self.description,
            "status": self.status,
            "progress": {
                **self.progress,
                "percentage": self.get_progress_percentage()
            },
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error_message": self.error_message,
            "options": self.options
        }
    
    def __repr__(self) -> str:
        """字符串表示"""
        return (
            f"BatchTask(task_id={self.task_id}, "
            f"name={self.name}, "
            f"status={self.status}, "
            f"progress={self.get_progress_percentage():.1f}%)"
        )


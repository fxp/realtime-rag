"""会话状态数据模型"""

from typing import List, Optional
import asyncio
import re


class SessionState:
    """会话状态数据模型
    
    管理用户连接的完整状态信息，包括ASR文本累积、暂停状态和查询任务。
    """
    
    def __init__(self, session_id: str):
        """初始化会话状态
        
        Args:
            session_id: 会话唯一标识符
        """
        self.session_id: str = session_id
        self.final_chunks: List[str] = []
        self.is_paused: bool = False
        self.last_final_text: Optional[str] = None
        self.current_query_task: Optional[asyncio.Task] = None
    
    def add_chunk(self, text: str, is_final: bool) -> None:
        """添加ASR文本块
        
        Args:
            text: ASR识别的文本
            is_final: 是否为最终化结果
        """
        if is_final and text.strip():
            self.final_chunks.append(text.strip())
            self.last_final_text = text.strip()
    
    @property
    def aggregated_text(self) -> str:
        """获取聚合后的文本
        
        Returns:
            所有最终化文本块的聚合结果
        """
        return " ".join(self.final_chunks)
    
    @property
    def has_active_query(self) -> bool:
        """检查是否有活跃的查询任务
        
        Returns:
            如果当前有正在执行的查询任务，返回True
        """
        return self.current_query_task is not None and not self.current_query_task.done()
    
    def reset(self) -> None:
        """重置会话状态
        
        清除所有最终化文本块，重置为初始状态
        """
        self.final_chunks.clear()
        self.last_final_text = None
        if self.current_query_task and not self.current_query_task.done():
            self.current_query_task.cancel()
        self.current_query_task = None
    
    def looks_like_question(self) -> bool:
        """判断文本是否像问题
        
        使用启发式算法判断聚合文本是否像问题：
        - 包含问号
        - 包含疑问词（中文：吗、呢、什么、怎么、为什么、如何等）
        - 包含英文疑问词（what、how、why、when、where、who等）
        
        Returns:
            如果文本看起来像问题，返回True
        """
        text = self.aggregated_text.lower()
        if not text:
            return False
        
        # 检查问号
        if '?' in text or '？' in text:
            return True
        
        # 中文疑问词
        chinese_question_words = [
            '吗', '呢', '什么', '怎么', '为什么', '如何', '哪里', 
            '哪个', '谁', '几', '多少', '是否', '能否', '可否',
            '干嘛', '咋', '啥'
        ]
        
        # 英文疑问词
        english_question_words = [
            'what', 'how', 'why', 'when', 'where', 'who', 
            'which', 'whom', 'whose', 'can', 'could', 'would',
            'should', 'is', 'are', 'do', 'does', 'did'
        ]
        
        # 检查中文疑问词
        for word in chinese_question_words:
            if word in text:
                return True
        
        # 检查英文疑问词（单词边界）
        for word in english_question_words:
            pattern = r'\b' + word + r'\b'
            if re.search(pattern, text):
                return True
        
        return False
    
    def __repr__(self) -> str:
        """字符串表示"""
        return (
            f"SessionState(session_id={self.session_id}, "
            f"chunks={len(self.final_chunks)}, "
            f"paused={self.is_paused}, "
            f"has_query={self.has_active_query})"
        )

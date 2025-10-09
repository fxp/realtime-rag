"""会话状态模型"""
from __future__ import annotations
from typing import List

class SessionState:
    QUESTION_HINTS = {"?", "吗", "呢", "怎么", "为何", "为什么", "请问", "多少", "哪", "怎么做"}
    
    def __init__(self, session_id: str) -> None:
        self.session_id = session_id
        self.final_chunks: List[str] = []
        self.is_paused: bool = False
    
    def add_chunk(self, text: str, is_final: bool) -> None:
        if is_final:
            self.final_chunks.append(text.strip())
    
    @property
    def aggregated_text(self) -> str:
        return " ".join(chunk for chunk in self.final_chunks if chunk)
    
    def reset(self) -> None:
        self.final_chunks.clear()
    
    def looks_like_question(self) -> bool:
        text = self.aggregated_text
        if not text:
            return False
        lowered = text.lower()
        if any(token in lowered for token in ("what", "why", "how", "when", "where", "?")):
            return True
        return any(hint in text for hint in self.QUESTION_HINTS)

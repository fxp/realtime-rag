"""会话状态模型"""
from __future__ import annotations

from asyncio import Task
from typing import List, Optional


class SessionState:
    QUESTION_HINTS = {"?", "吗", "呢", "怎么", "为何", "为什么", "请问", "多少", "哪", "怎么做"}

    def __init__(self, session_id: str) -> None:
        self.session_id = session_id
        self.final_chunks: List[str] = []
        self.is_paused: bool = False
        self.last_final_text: Optional[str] = None
        self.current_query_task: Optional[Task] = None

    def add_chunk(self, text: str, is_final: bool) -> None:
        if not is_final:
            return

        normalized = text.strip()
        if not normalized:
            return

        self.last_final_text = normalized
        if self.has_active_query:
            # 在进行中的查询被抢占前，保持最近一次的最终chunk即可
            self.final_chunks = [normalized]
        else:
            self.final_chunks.append(normalized)

    @property
    def aggregated_text(self) -> str:
        return " ".join(chunk for chunk in self.final_chunks if chunk)

    @property
    def has_active_query(self) -> bool:
        return self.current_query_task is not None and not self.current_query_task.done()

    def reset(self) -> None:
        self.final_chunks.clear()
        self.last_final_text = None

    def looks_like_question(self) -> bool:
        text = self.aggregated_text
        if not text:
            return False
        lowered = text.lower()
        if any(token in lowered for token in ("what", "why", "how", "when", "where", "?")):
            return True
        return any(hint in text for hint in self.QUESTION_HINTS)

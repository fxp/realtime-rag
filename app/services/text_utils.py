"""文本处理工具"""
from typing import List

def stream_answer(answer: str, max_chunk_size: int = 120) -> List[str]:
    chunks: List[str] = []
    current = []
    current_len = 0
    
    for part in answer.split():
        part_len = len(part) + 1
        if current_len + part_len > max_chunk_size and current:
            chunks.append(" ".join(current))
            current = [part]
            current_len = len(part)
        else:
            current.append(part)
            current_len += part_len
    
    if current:
        chunks.append(" ".join(current))
    if not chunks:
        chunks.append(answer)
    return chunks

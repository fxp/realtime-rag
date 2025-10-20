"""文本处理工具"""

from typing import List


def split_answer_into_chunks(answer: str, chunk_size: int = 120) -> List[str]:
    """将长答案分割为可管理的块，用于流式传输
    
    Args:
        answer: 完整的答案文本
        chunk_size: 每个块的最大字符数，默认120
        
    Returns:
        List[str]: 答案块列表
        
    示例:
        >>> answer = "这是一个很长的答案，需要分块传输。"
        >>> chunks = split_answer_into_chunks(answer, chunk_size=10)
        >>> print(chunks)
        ['这是一个很长的答', '案，需要分块传输', '。']
    """
    if not answer:
        return []
    
    # 如果答案长度小于块大小，直接返回
    if len(answer) <= chunk_size:
        return [answer]
    
    chunks = []
    start = 0
    
    while start < len(answer):
        # 计算当前块的结束位置
        end = start + chunk_size
        
        # 如果还有剩余文本且不是最后一块
        if end < len(answer):
            # 尝试在句子边界分割（查找句号、问号、感叹号等）
            sentence_end = max(
                answer.rfind('。', start, end),
                answer.rfind('？', start, end),
                answer.rfind('！', start, end),
                answer.rfind('.', start, end),
                answer.rfind('?', start, end),
                answer.rfind('!', start, end)
            )
            
            # 如果找到句子边界，在那里分割
            if sentence_end > start:
                end = sentence_end + 1
            else:
                # 否则尝试在空格处分割
                space_pos = answer.rfind(' ', start, end)
                if space_pos > start:
                    end = space_pos + 1
        
        # 添加当前块
        chunk = answer[start:end].strip()
        if chunk:
            chunks.append(chunk)
        
        start = end
    
    return chunks


def clean_text(text: str) -> str:
    """清理文本，移除多余的空白字符
    
    Args:
        text: 输入文本
        
    Returns:
        str: 清理后的文本
    """
    if not text:
        return ""
    
    # 移除多余的空白字符
    import re
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def truncate_text(text: str, max_length: int = 1000, suffix: str = "...") -> str:
    """截断文本到指定长度
    
    Args:
        text: 输入文本
        max_length: 最大长度
        suffix: 截断后添加的后缀
        
    Returns:
        str: 截断后的文本
    """
    if not text or len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def extract_keywords(text: str, max_keywords: int = 10) -> List[str]:
    """从文本中提取关键词（简单实现）
    
    Args:
        text: 输入文本
        max_keywords: 最大关键词数量
        
    Returns:
        List[str]: 关键词列表
    """
    if not text:
        return []
    
    # 简单实现：按空格分割，过滤停用词
    import re
    
    # 移除标点符号
    text = re.sub(r'[^\w\s]', ' ', text.lower())
    words = text.split()
    
    # 简单的停用词列表
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'be', 'been',
        '的', '了', '和', '是', '在', '有', '我', '你', '他', '她', '它'
    }
    
    # 过滤停用词和短词
    keywords = [w for w in words if len(w) > 2 and w not in stop_words]
    
    # 统计词频
    from collections import Counter
    word_counts = Counter(keywords)
    
    # 返回最常见的关键词
    return [word for word, _ in word_counts.most_common(max_keywords)]


def calculate_similarity(text1: str, text2: str) -> float:
    """计算两个文本的相似度（简单实现）
    
    Args:
        text1: 第一个文本
        text2: 第二个文本
        
    Returns:
        float: 相似度分数（0-1之间）
    """
    if not text1 or not text2:
        return 0.0
    
    # 提取关键词
    keywords1 = set(extract_keywords(text1))
    keywords2 = set(extract_keywords(text2))
    
    if not keywords1 or not keywords2:
        return 0.0
    
    # 计算Jaccard相似度
    intersection = keywords1 & keywords2
    union = keywords1 | keywords2
    
    return len(intersection) / len(union) if union else 0.0

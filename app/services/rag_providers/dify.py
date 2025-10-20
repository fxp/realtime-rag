"""Dify RAG提供商实现"""

import httpx
from typing import Dict, Any, AsyncIterator
from .base import BaseRAGProvider
from app.models.batch_task import QueryResult
import logging
import json

logger = logging.getLogger(__name__)


class DifyProvider(BaseRAGProvider):
    """Dify RAG服务实现
    
    基于Dify Chat API的RAG服务提供商。
    支持对话式问答和流式响应。
    """
    
    def __init__(self, config: Dict[str, Any]):
        """初始化Dify Provider
        
        Args:
            config: 配置，包含api_key、base_url、timeout等
        """
        super().__init__(config)
        self.api_key = config.get("api_key")
        self.base_url = config.get("base_url", "https://api.dify.ai/v1")
        self.timeout = config.get("timeout", 30.0)
        self.user = config.get("user", "default-user")
        self.conversation_id = config.get("conversation_id")  # 可选的会话ID
        
        if not self.api_key:
            raise ValueError("Dify Provider requires api_key in config")
    
    async def query(self, question: str, **kwargs) -> QueryResult:
        """查询Dify
        
        Args:
            question: 用户问题
            **kwargs: 额外参数，如conversation_id、user等
            
        Returns:
            QueryResult: 查询结果
        """
        url = f"{self.base_url}/chat-messages"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "inputs": kwargs.get("inputs", {}),
            "query": question,
            "response_mode": "blocking",  # 阻塞模式，等待完整响应
            "user": kwargs.get("user", self.user),
            "conversation_id": kwargs.get("conversation_id", self.conversation_id) or ""
        }
        
        # 添加可选参数
        if "files" in kwargs:
            payload["files"] = kwargs["files"]
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()
                
                # 提取答案内容
                content = data.get("answer", "")
                
                # 提取来源信息
                sources = []
                if "metadata" in data and "retriever_resources" in data["metadata"]:
                    for resource in data["metadata"]["retriever_resources"]:
                        sources.append({
                            "title": resource.get("document_name", ""),
                            "content": resource.get("content", ""),
                            "score": resource.get("score", 0),
                            "position": resource.get("position", 0)
                        })
                
                return QueryResult(
                    content=content,
                    metadata={
                        "provider": self.name,
                        "conversation_id": data.get("conversation_id"),
                        "message_id": data.get("id"),
                        "created_at": data.get("created_at"),
                        "mode": data.get("mode", "chat")
                    },
                    sources=sources if sources else None,
                    usage={
                        "tokens": data.get("metadata", {}).get("usage", {}).get("total_tokens", 0),
                        "prompt_tokens": data.get("metadata", {}).get("usage", {}).get("prompt_tokens", 0),
                        "completion_tokens": data.get("metadata", {}).get("usage", {}).get("completion_tokens", 0)
                    }
                )
        except httpx.HTTPError as e:
            logger.error(f"Dify query failed: {e}")
            # 尝试解析错误响应
            try:
                error_data = e.response.json() if hasattr(e, 'response') else {}
                error_message = error_data.get("message", str(e))
            except:
                error_message = str(e)
            raise Exception(f"Dify查询失败: {error_message}")
    
    async def stream_query(self, question: str, **kwargs) -> AsyncIterator[str]:
        """流式查询Dify
        
        Args:
            question: 用户问题
            **kwargs: 额外参数
            
        Yields:
            str: 答案片段
        """
        url = f"{self.base_url}/chat-messages"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "text/event-stream"
        }
        
        payload = {
            "inputs": kwargs.get("inputs", {}),
            "query": question,
            "response_mode": "streaming",  # 流式模式
            "user": kwargs.get("user", self.user),
            "conversation_id": kwargs.get("conversation_id", self.conversation_id) or ""
        }
        
        # 添加可选参数
        if "files" in kwargs:
            payload["files"] = kwargs["files"]
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                async with client.stream("POST", url, json=payload, headers=headers) as response:
                    response.raise_for_status()
                    
                    async for line in response.aiter_lines():
                        if not line or not line.strip():
                            continue
                        
                        # Dify使用SSE格式，每行以"data: "开头
                        if line.startswith("data: "):
                            data_str = line[6:]  # 移除"data: "前缀
                            
                            try:
                                data = json.loads(data_str)
                                event = data.get("event")
                                
                                # 处理不同的事件类型
                                if event == "message":
                                    # 消息内容
                                    answer = data.get("answer", "")
                                    if answer:
                                        yield answer
                                
                                elif event == "agent_message":
                                    # Agent消息
                                    answer = data.get("answer", "")
                                    if answer:
                                        yield answer
                                
                                elif event == "message_end":
                                    # 消息结束，可以获取完整的元数据
                                    logger.info(f"Stream ended, conversation_id: {data.get('conversation_id')}")
                                    break
                                
                                elif event == "error":
                                    # 错误事件
                                    error_msg = data.get("message", "Unknown error")
                                    logger.error(f"Dify stream error: {error_msg}")
                                    raise Exception(f"Dify流式查询错误: {error_msg}")
                                
                                # 其他事件类型（workflow_started, node_started等）可以忽略
                                
                            except json.JSONDecodeError as e:
                                logger.warning(f"Failed to parse SSE data: {data_str}, error: {e}")
                                continue
                        
        except httpx.HTTPError as e:
            logger.error(f"Dify stream query failed: {e}")
            raise Exception(f"Dify流式查询失败: {str(e)}")
    
    async def health_check(self) -> bool:
        """健康检查
        
        Returns:
            bool: 服务是否可用
        """
        try:
            # 使用参数列表端点进行健康检查
            url = f"{self.base_url}/parameters"
            headers = {"Authorization": f"Bearer {self.api_key}"}
            
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(url, headers=headers)
                return response.status_code == 200
        except Exception as e:
            logger.error(f"Dify health check failed: {e}")
            return False
    
    @property
    def name(self) -> str:
        """提供商名称"""
        return "DifyProvider"
    
    async def get_conversation_messages(self, conversation_id: str, 
                                       limit: int = 20) -> Dict[str, Any]:
        """获取会话消息历史
        
        Args:
            conversation_id: 会话ID
            limit: 获取消息数量限制
            
        Returns:
            Dict[str, Any]: 会话消息列表
        """
        url = f"{self.base_url}/messages"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        params = {
            "conversation_id": conversation_id,
            "user": self.user,
            "limit": limit
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, headers=headers, params=params)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Failed to get conversation messages: {e}")
            raise Exception(f"获取会话消息失败: {str(e)}")
    
    async def get_conversations(self, limit: int = 20, 
                               last_id: str = None) -> Dict[str, Any]:
        """获取会话列表
        
        Args:
            limit: 获取会话数量限制
            last_id: 上一次请求的最后一个会话ID（用于分页）
            
        Returns:
            Dict[str, Any]: 会话列表
        """
        url = f"{self.base_url}/conversations"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        params = {
            "user": self.user,
            "limit": limit
        }
        
        if last_id:
            params["last_id"] = last_id
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, headers=headers, params=params)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Failed to get conversations: {e}")
            raise Exception(f"获取会话列表失败: {str(e)}")
    
    async def rename_conversation(self, conversation_id: str, 
                                 name: str) -> Dict[str, Any]:
        """重命名会话
        
        Args:
            conversation_id: 会话ID
            name: 新的会话名称
            
        Returns:
            Dict[str, Any]: 更新结果
        """
        url = f"{self.base_url}/conversations/{conversation_id}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "name": name,
            "user": self.user
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Failed to rename conversation: {e}")
            raise Exception(f"重命名会话失败: {str(e)}")
    
    async def delete_conversation(self, conversation_id: str) -> bool:
        """删除会话
        
        Args:
            conversation_id: 会话ID
            
        Returns:
            bool: 是否删除成功
        """
        url = f"{self.base_url}/conversations/{conversation_id}"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        params = {"user": self.user}
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.delete(url, headers=headers, params=params)
                response.raise_for_status()
                return True
        except httpx.HTTPError as e:
            logger.error(f"Failed to delete conversation: {e}")
            return False
    
    async def get_suggested_questions(self, message_id: str) -> Dict[str, Any]:
        """获取建议的下一步问题
        
        Args:
            message_id: 消息ID
            
        Returns:
            Dict[str, Any]: 建议问题列表
        """
        url = f"{self.base_url}/messages/{message_id}/suggested"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        params = {"user": self.user}
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, headers=headers, params=params)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Failed to get suggested questions: {e}")
            raise Exception(f"获取建议问题失败: {str(e)}")
    
    async def stop_message(self, task_id: str) -> bool:
        """停止消息生成
        
        Args:
            task_id: 任务ID
            
        Returns:
            bool: 是否停止成功
        """
        url = f"{self.base_url}/chat-messages/{task_id}/stop"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {"user": self.user}
        
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                return True
        except httpx.HTTPError as e:
            logger.error(f"Failed to stop message: {e}")
            return False
    
    async def send_feedback(self, message_id: str, rating: str, 
                           content: str = None) -> bool:
        """发送消息反馈
        
        Args:
            message_id: 消息ID
            rating: 评分（like 或 dislike）
            content: 反馈内容
            
        Returns:
            bool: 是否发送成功
        """
        url = f"{self.base_url}/messages/{message_id}/feedbacks"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "rating": rating,
            "user": self.user
        }
        
        if content:
            payload["content"] = content
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                return True
        except httpx.HTTPError as e:
            logger.error(f"Failed to send feedback: {e}")
            return False


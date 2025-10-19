"""Dify RAG 提供商实现"""
from __future__ import annotations
from typing import Optional, Dict, Any
import httpx
from .base import BaseRAGProvider, QueryResult


class DifyProvider(BaseRAGProvider):
    """Dify RAG 提供商"""
    
    def _validate_config(self) -> None:
        """验证 Dify 配置"""
        required_fields = ["api_key", "base_url"]
        for field in required_fields:
            if field not in self.config or not self.config[field]:
                raise ValueError(f"Dify configuration missing required field: {field}")
    
    async def query(
        self, 
        text: str, 
        user: str = "default-user",
        conversation_id: Optional[str] = None,
        **kwargs
    ) -> QueryResult:
        """执行 Dify 查询"""
        api_key = self.config["api_key"]
        base_url = self.config["base_url"]
        timeout = self.config.get("timeout", 60.0)
        
        url = f"{base_url}/chat-messages"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "query": text,
            "user": user,
            "response_mode": "blocking",
            "inputs": {}
        }
        
        if conversation_id:
            payload["conversation_id"] = conversation_id
        
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                result = response.json()
                
                if result.get("event") == "message":
                    answer = result.get("answer", "")
                    metadata = result.get("metadata", {})
                    usage = metadata.get("usage", {})
                    
                    return QueryResult(
                        content=answer if answer else "未获取到回答。",
                        metadata=metadata,
                        usage=usage
                    )
                else:
                    return QueryResult(
                        content=f"Dify API 返回了意外的事件类型: {result.get('event')}",
                        metadata={"event": result.get("event")}
                    )
        
        except httpx.TimeoutException as e:
            error_msg = f"请求超时（超过{timeout}秒）"
            raise Exception(f"调用 Dify RAG 服务失败：{error_msg}") from e
        
        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            try:
                error_detail = e.response.text[:200]
            except:
                error_detail = "无法读取错误详情"
            error_msg = f"HTTP {status_code} - {error_detail}"
            raise Exception(f"调用 Dify RAG 服务失败：{error_msg}") from e
        
        except httpx.RequestError as e:
            error_msg = f"网络错误 - {type(e).__name__}: {str(e)[:100]}"
            raise Exception(f"调用 Dify RAG 服务失败：{error_msg}") from e
        
        except Exception as e:
            error_msg = f"未知错误 - {type(e).__name__}: {str(e)[:100]}"
            raise Exception(f"调用 Dify RAG 服务失败：{error_msg}") from e
    
    async def health_check(self) -> bool:
        """Dify 健康检查"""
        try:
            # 执行简单查询测试连接
            await self.query("test", user="health-check")
            return True
        except Exception:
            return False

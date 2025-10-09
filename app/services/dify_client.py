"""Dify API 客户端服务"""
from __future__ import annotations
from typing import Optional
import httpx
from app.config import config

class DifyClient:
    @staticmethod
    async def query(text: str, user: str = "websocket-user", conversation_id: Optional[str] = None) -> str:
        if not config.DIFY_API_KEY:
            return "错误：未配置 DIFY_API_KEY"
        
        url = f"{config.DIFY_BASE_URL}/chat-messages"
        headers = {"Authorization": f"Bearer {config.DIFY_API_KEY}", "Content-Type": "application/json"}
        payload = {"query": text, "user": user, "response_mode": "blocking", "inputs": {}}
        if conversation_id:
            payload["conversation_id"] = conversation_id
        
        try:
            async with httpx.AsyncClient(timeout=config.DIFY_TIMEOUT) as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                result = response.json()
                
                if result.get("event") == "message":
                    answer = result.get("answer", "")
                    metadata = result.get("metadata", {})
                    usage = metadata.get("usage", {})
                    if usage:
                        print(f"[Dify] Tokens: {usage.get('total_tokens', 0)}, Price: {usage.get('total_price', 0)} {usage.get('currency', 'USD')}")
                    return answer if answer else "未获取到回答。"
                else:
                    return f"Dify API 返回了意外的事件类型: {result.get('event')}"
        
        except httpx.TimeoutException as e:
            error_msg = f"请求超时（超过{config.DIFY_TIMEOUT}秒）"
            print(f"[Dify Error] {error_msg} - {type(e).__name__}: {str(e)}")
            return f"调用 RAG 服务失败：{error_msg}"
        
        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            try:
                error_detail = e.response.text[:200]
            except:
                error_detail = "无法读取错误详情"
            error_msg = f"HTTP {status_code} - {error_detail}"
            print(f"[Dify Error] {error_msg}")
            return f"调用 RAG 服务失败：{error_msg}"
        
        except httpx.RequestError as e:
            error_msg = f"网络错误 - {type(e).__name__}: {str(e)[:100]}"
            print(f"[Dify Error] {error_msg}")
            return f"调用 RAG 服务失败：{error_msg}"
        
        except Exception as e:
            error_msg = f"未知错误 - {type(e).__name__}: {str(e)[:100]}"
            print(f"[Dify Error] {error_msg}")
            return f"调用 RAG 服务失败：{error_msg}"

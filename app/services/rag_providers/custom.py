"""自定义 RAG 提供商示例"""
from __future__ import annotations
from typing import Optional, Dict, Any
import httpx
from .base import BaseRAGProvider, QueryResult


class CustomRAGProvider(BaseRAGProvider):
    """自定义 RAG 提供商示例"""
    
    def _validate_config(self) -> None:
        """验证自定义配置"""
        required_fields = ["api_key", "base_url"]
        for field in required_fields:
            if field not in self.config or not self.config[field]:
                raise ValueError(f"Custom RAG configuration missing required field: {field}")
    
    async def query(
        self, 
        text: str, 
        user: str = "default-user",
        conversation_id: Optional[str] = None,
        **kwargs
    ) -> QueryResult:
        """执行自定义 RAG 查询"""
        api_key = self.config["api_key"]
        base_url = self.config["base_url"]
        timeout = self.config.get("timeout", 60.0)
        
        # 自定义 API 端点
        url = f"{base_url}/query"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "question": text,
            "user_id": user,
            "session_id": conversation_id,
            **kwargs  # 支持额外参数
        }
        
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                result = response.json()
                
                # 根据自定义 API 响应格式解析结果
                answer = result.get("answer", "")
                metadata = result.get("metadata", {})
                sources = result.get("sources", [])
                
                return QueryResult(
                    content=answer if answer else "未获取到回答。",
                    metadata=metadata,
                    sources=sources
                )
        
        except httpx.TimeoutException as e:
            error_msg = f"请求超时（超过{timeout}秒）"
            raise Exception(f"调用自定义 RAG 服务失败：{error_msg}") from e
        
        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            try:
                error_detail = e.response.text[:200]
            except:
                error_detail = "无法读取错误详情"
            error_msg = f"HTTP {status_code} - {error_detail}"
            raise Exception(f"调用自定义 RAG 服务失败：{error_msg}") from e
        
        except httpx.RequestError as e:
            error_msg = f"网络错误 - {type(e).__name__}: {str(e)[:100]}"
            raise Exception(f"调用自定义 RAG 服务失败：{error_msg}") from e
        
        except Exception as e:
            error_msg = f"未知错误 - {type(e).__name__}: {str(e)[:100]}"
            raise Exception(f"调用自定义 RAG 服务失败：{error_msg}") from e
    
    async def health_check(self) -> bool:
        """自定义 RAG 健康检查"""
        try:
            # 执行简单查询测试连接
            await self.query("test", user="health-check")
            return True
        except Exception:
            return False


class CustomSearchProvider(BaseSearchProvider):
    """自定义搜索提供商示例"""
    
    def _validate_config(self) -> None:
        """验证自定义搜索配置"""
        required_fields = ["api_key", "base_url"]
        for field in required_fields:
            if field not in self.config or not self.config[field]:
                raise ValueError(f"Custom search configuration missing required field: {field}")
    
    async def search(
        self,
        query: str,
        num_results: int = 10,
        **kwargs
    ) -> QueryResult:
        """执行自定义搜索"""
        api_key = self.config["api_key"]
        base_url = self.config["base_url"]
        timeout = self.config.get("timeout", 30.0)
        
        # 自定义搜索 API 端点
        url = f"{base_url}/search"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "query": query,
            "limit": num_results,
            **kwargs  # 支持额外参数
        }
        
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                result = response.json()
                
                # 根据自定义搜索 API 响应格式解析结果
                results = result.get("results", [])
                
                # 构建回答内容
                content_parts = []
                if results:
                    content_parts.append("**搜索结果:**")
                    for i, item in enumerate(results[:5], 1):
                        title = item.get("title", "")
                        summary = item.get("summary", "")
                        url = item.get("url", "")
                        if title and summary:
                            content_parts.append(f"{i}. **{title}**\n   {summary}\n   {url}")
                
                content = "\n\n".join(content_parts) if content_parts else "未找到相关信息。"
                
                # 构建来源信息
                sources = []
                for item in results:
                    sources.append({
                        "title": item.get("title", ""),
                        "url": item.get("url", ""),
                        "summary": item.get("summary", "")
                    })
                
                return QueryResult(
                    content=content,
                    metadata={"search_results_count": len(results)},
                    sources=sources
                )
        
        except httpx.TimeoutException as e:
            error_msg = f"搜索请求超时（超过{timeout}秒）"
            raise Exception(f"调用自定义搜索服务失败：{error_msg}") from e
        
        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            try:
                error_detail = e.response.text[:200]
            except:
                error_detail = "无法读取错误详情"
            error_msg = f"HTTP {status_code} - {error_detail}"
            raise Exception(f"调用自定义搜索服务失败：{error_msg}") from e
        
        except httpx.RequestError as e:
            error_msg = f"网络错误 - {type(e).__name__}: {str(e)[:100]}"
            raise Exception(f"调用自定义搜索服务失败：{error_msg}") from e
        
        except Exception as e:
            error_msg = f"未知错误 - {type(e).__name__}: {str(e)[:100]}"
            raise Exception(f"调用自定义搜索服务失败：{error_msg}") from e

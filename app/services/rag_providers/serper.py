"""Serper 搜索提供商实现"""
from __future__ import annotations
from typing import Optional, Dict, Any
import httpx
from .base import BaseSearchProvider, QueryResult


class SerperProvider(BaseSearchProvider):
    """Serper 搜索提供商"""
    
    def _validate_config(self) -> None:
        """验证 Serper 配置"""
        required_fields = ["api_key"]
        for field in required_fields:
            if field not in self.config or not self.config[field]:
                raise ValueError(f"Serper configuration missing required field: {field}")
    
    async def search(
        self,
        query: str,
        num_results: int = 10,
        **kwargs
    ) -> QueryResult:
        """执行 Serper 搜索"""
        api_key = self.config["api_key"]
        timeout = self.config.get("timeout", 30.0)
        
        url = "https://google.serper.dev/search"
        headers = {
            "X-API-KEY": api_key,
            "Content-Type": "application/json"
        }
        
        payload = {
            "q": query,
            "num": num_results,
            **kwargs  # 支持额外参数如 country, language 等
        }
        
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                result = response.json()
                
                # 提取搜索结果
                organic_results = result.get("organic", [])
                knowledge_graph = result.get("knowledgeGraph")
                
                # 构建回答内容
                content_parts = []
                
                # 添加知识图谱信息
                if knowledge_graph:
                    title = knowledge_graph.get("title", "")
                    description = knowledge_graph.get("description", "")
                    if title and description:
                        content_parts.append(f"**{title}**\n{description}")
                
                # 添加搜索结果
                if organic_results:
                    content_parts.append("\n**相关搜索结果:**")
                    for i, item in enumerate(organic_results[:5], 1):
                        title = item.get("title", "")
                        snippet = item.get("snippet", "")
                        link = item.get("link", "")
                        if title and snippet:
                            content_parts.append(f"{i}. **{title}**\n   {snippet}\n   {link}")
                
                # 添加答案框信息
                answer_box = result.get("answerBox", {})
                if answer_box:
                    answer = answer_box.get("answer", "")
                    snippet = answer_box.get("snippet", "")
                    if answer:
                        content_parts.insert(0, f"**答案:** {answer}")
                    elif snippet:
                        content_parts.insert(0, f"**信息:** {snippet}")
                
                content = "\n\n".join(content_parts) if content_parts else "未找到相关信息。"
                
                # 构建元数据
                metadata = {
                    "search_results_count": len(organic_results),
                    "has_knowledge_graph": bool(knowledge_graph),
                    "has_answer_box": bool(answer_box),
                    "search_parameters": payload
                }
                
                # 构建来源信息
                sources = []
                for item in organic_results:
                    sources.append({
                        "title": item.get("title", ""),
                        "url": item.get("link", ""),
                        "snippet": item.get("snippet", "")
                    })
                
                return QueryResult(
                    content=content,
                    metadata=metadata,
                    sources=sources
                )
        
        except httpx.TimeoutException as e:
            error_msg = f"搜索请求超时（超过{timeout}秒）"
            raise Exception(f"调用 Serper 搜索服务失败：{error_msg}") from e
        
        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            try:
                error_detail = e.response.text[:200]
            except:
                error_detail = "无法读取错误详情"
            error_msg = f"HTTP {status_code} - {error_detail}"
            raise Exception(f"调用 Serper 搜索服务失败：{error_msg}") from e
        
        except httpx.RequestError as e:
            error_msg = f"网络错误 - {type(e).__name__}: {str(e)[:100]}"
            raise Exception(f"调用 Serper 搜索服务失败：{error_msg}") from e
        
        except Exception as e:
            error_msg = f"未知错误 - {type(e).__name__}: {str(e)[:100]}"
            raise Exception(f"调用 Serper 搜索服务失败：{error_msg}") from e

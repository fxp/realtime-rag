"""配置管理"""

from typing import Dict, Any, Optional
import os
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

# 加载环境变量
load_dotenv()


class Config:
    """应用配置管理类
    
    从环境变量和配置文件中加载应用配置，提供统一的配置访问接口。
    """
    
    def __init__(self):
        """初始化配置"""
        self.app_name = os.getenv("APP_NAME", "Realtime RAG WebSocket Service")
        self.app_version = "2.0.0"
        self.debug = os.getenv("DEBUG", "false").lower() == "true"
        
        # 服务器配置
        self.host = os.getenv("HOST", "0.0.0.0")
        self.port = int(os.getenv("PORT", "8000"))
        
        # WebSocket配置
        self.ws_path = os.getenv("WS_PATH", "/ws/realtime-asr")
        
        # RAG服务配置
        self.rag_config = self._load_rag_config()
        
        # 搜索服务配置
        self.search_config = self._load_search_config()
        
        # 批量处理配置
        self.batch_config = self._load_batch_config()
    
    def _load_rag_config(self) -> Dict[str, Any]:
        """加载RAG服务配置
        
        Returns:
            Dict[str, Any]: RAG服务配置
        """
        provider = os.getenv("RAG_PROVIDER", "").lower()
        
        if not provider:
            logger.warning("RAG_PROVIDER not configured")
            return {}
        
        config = {
            "provider": provider
        }
        
        if provider == "context":
            config.update({
                "api_key": os.getenv("CONTEXT_API_KEY"),
                "base_url": os.getenv("CONTEXT_BASE_URL", "https://api.context.ai"),
                "timeout": float(os.getenv("CONTEXT_TIMEOUT", "30.0"))
            })
        elif provider == "openai":
            config.update({
                "api_key": os.getenv("OPENAI_API_KEY"),
                "base_url": os.getenv("OPENAI_BASE_URL", "https://api.openai.com"),
                "timeout": float(os.getenv("OPENAI_TIMEOUT", "30.0")),
                "model": os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
            })
        elif provider == "custom":
            config.update({
                "api_url": os.getenv("CUSTOM_RAG_API_URL"),
                "api_key": os.getenv("CUSTOM_RAG_API_KEY"),
                "timeout": float(os.getenv("CUSTOM_RAG_TIMEOUT", "30.0"))
            })
        
        return config
    
    def _load_search_config(self) -> Dict[str, Any]:
        """加载搜索服务配置
        
        Returns:
            Dict[str, Any]: 搜索服务配置
        """
        provider = os.getenv("SEARCH_PROVIDER", "").lower()
        
        if not provider:
            logger.warning("SEARCH_PROVIDER not configured")
            return {}
        
        config = {
            "provider": provider
        }
        
        if provider == "serper":
            config.update({
                "api_key": os.getenv("SERPER_API_KEY"),
                "timeout": float(os.getenv("SERPER_TIMEOUT", "10.0"))
            })
        
        return config
    
    def _load_batch_config(self) -> Dict[str, Any]:
        """加载批量处理配置
        
        Returns:
            Dict[str, Any]: 批量处理配置
        """
        return {
            "enabled": os.getenv("BATCH_ENABLED", "true").lower() == "true",
            "max_concurrent": int(os.getenv("BATCH_MAX_CONCURRENT", "5")),
            "max_queue_size": int(os.getenv("BATCH_MAX_QUEUE_SIZE", "1000")),
            "storage_path": os.getenv("BATCH_STORAGE_PATH", "./batch_results")
        }
    
    def validate(self) -> bool:
        """验证配置有效性
        
        Returns:
            bool: 如果配置有效返回True
        """
        # 检查RAG配置
        if self.rag_config:
            provider = self.rag_config.get("provider")
            if provider == "context" and not self.rag_config.get("api_key"):
                logger.error("CONTEXT_API_KEY is required for Context provider")
                return False
            elif provider == "openai" and not self.rag_config.get("api_key"):
                logger.error("OPENAI_API_KEY is required for OpenAI provider")
                return False
            elif provider == "custom" and not self.rag_config.get("api_url"):
                logger.error("CUSTOM_RAG_API_URL is required for Custom provider")
                return False
        
        # 检查搜索配置
        if self.search_config:
            provider = self.search_config.get("provider")
            if provider == "serper" and not self.search_config.get("api_key"):
                logger.error("SERPER_API_KEY is required for Serper provider")
                return False
        
        # 至少需要配置RAG或搜索服务之一
        if not self.rag_config and not self.search_config:
            logger.error("At least one of RAG or Search provider must be configured")
            return False
        
        return True
    
    def get_service_config(self) -> Dict[str, Any]:
        """获取服务配置
        
        Returns:
            Dict[str, Any]: 服务配置字典
        """
        return {
            "rag": self.rag_config,
            "search": self.search_config,
            "batch": self.batch_config
        }
    
    def __repr__(self) -> str:
        """字符串表示"""
        return (
            f"Config(app_name={self.app_name}, "
            f"version={self.app_version}, "
            f"debug={self.debug}, "
            f"rag_provider={self.rag_config.get('provider')}, "
            f"search_provider={self.search_config.get('provider')})"
        )


# 全局配置实例
config = Config()

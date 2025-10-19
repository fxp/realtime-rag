"""应用配置管理"""
import os
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv

env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

class Config:
    # 基础应用配置
    WS_PATH: str = "/ws/realtime-asr"
    APP_TITLE: str = "Realtime RAG"
    APP_VERSION: str = "2.0.0"
    
    # 服务提供商配置
    RAG_PROVIDER: str = os.getenv("RAG_PROVIDER", "dify")
    SEARCH_PROVIDER: str = os.getenv("SEARCH_PROVIDER", "serper")
    
    # Dify 配置 (向后兼容)
    DIFY_API_KEY: str = os.getenv("DIFY_API_KEY", "")
    DIFY_BASE_URL: str = os.getenv("DIFY_BASE_URL", "https://api.dify.ai/v1")
    DIFY_TIMEOUT: float = float(os.getenv("DIFY_TIMEOUT", "60.0"))
    
    # Serper 配置
    SERPER_API_KEY: str = os.getenv("SERPER_API_KEY", "")
    SERPER_TIMEOUT: float = float(os.getenv("SERPER_TIMEOUT", "30.0"))
    
    @classmethod
    def get_rag_config(cls) -> Dict[str, Any]:
        """获取 RAG 服务配置"""
        if cls.RAG_PROVIDER == "dify":
            return {
                "provider": "dify",
                "config": {
                    "api_key": cls.DIFY_API_KEY,
                    "base_url": cls.DIFY_BASE_URL,
                    "timeout": cls.DIFY_TIMEOUT
                }
            }
        else:
            # 可以扩展其他 RAG 提供商
            return {}
    
    @classmethod
    def get_search_config(cls) -> Dict[str, Any]:
        """获取搜索服务配置"""
        if cls.SEARCH_PROVIDER == "serper":
            return {
                "provider": "serper",
                "config": {
                    "api_key": cls.SERPER_API_KEY,
                    "timeout": cls.SERPER_TIMEOUT
                }
            }
        else:
            # 可以扩展其他搜索提供商
            return {}
    
    @classmethod
    def get_service_config(cls) -> Dict[str, Any]:
        """获取完整的服务配置"""
        return {
            "rag": cls.get_rag_config(),
            "search": cls.get_search_config()
        }
    
    @classmethod
    def validate(cls) -> None:
        """验证配置"""
        rag_config = cls.get_rag_config()
        search_config = cls.get_search_config()
        
        print("=== 服务提供商配置 ===")
        
        if rag_config:
            provider = rag_config["provider"]
            print(f"✓ RAG 提供商: {provider}")
            if provider == "dify" and cls.DIFY_API_KEY:
                print(f"  - Dify API 已配置: {cls.DIFY_API_KEY[:10]}...")
                print(f"  - Base URL: {cls.DIFY_BASE_URL}")
            elif provider == "dify":
                print("  ⚠️  警告: DIFY_API_KEY 未配置")
        else:
            print("⚠️  警告: 未配置 RAG 提供商")
        
        if search_config:
            provider = search_config["provider"]
            print(f"✓ 搜索提供商: {provider}")
            if provider == "serper" and cls.SERPER_API_KEY:
                print(f"  - Serper API 已配置: {cls.SERPER_API_KEY[:10]}...")
            elif provider == "serper":
                print("  ⚠️  警告: SERPER_API_KEY 未配置")
        else:
            print("⚠️  警告: 未配置搜索提供商")

config = Config()

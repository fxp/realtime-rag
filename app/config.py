"""应用配置管理"""
import os
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

class Config:
    DIFY_API_KEY: str = os.getenv("DIFY_API_KEY", "")
    DIFY_BASE_URL: str = os.getenv("DIFY_BASE_URL", "https://api.dify.ai/v1")
    DIFY_TIMEOUT: float = float(os.getenv("DIFY_TIMEOUT", "60.0"))
    WS_PATH: str = "/ws/realtime-asr"
    APP_TITLE: str = "Realtime RAG"
    APP_VERSION: str = "2.0.0"
    
    @classmethod
    def validate(cls) -> None:
        if cls.DIFY_API_KEY:
            print(f"✓ Dify API 已配置: {cls.DIFY_API_KEY[:10]}...")
            print(f"✓ Base URL: {cls.DIFY_BASE_URL}")
        else:
            print("⚠️  警告: DIFY_API_KEY 未配置")

config = Config()

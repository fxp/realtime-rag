"""Realtime RAG WebSocket Service - 主应用入口"""

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
import logging
from typing import Dict, Any
import os

from app.config import config
from app.services.rag_service import RAGService
from app.services.batch_processor import BatchProcessor
from app.routers import websocket as ws_router
from app.routers import batch as batch_router

# 配置日志
logging.basicConfig(
    level=logging.INFO if not config.debug else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 全局服务实例
rag_service: RAGService = None
batch_processor: BatchProcessor = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理
    
    在应用启动时初始化服务，在应用关闭时清理资源。
    """
    global rag_service, batch_processor
    
    logger.info("Starting Realtime RAG WebSocket Service...")
    
    # 验证配置
    if not config.validate():
        logger.error("Configuration validation failed")
        raise RuntimeError("Invalid configuration")
    
    # 初始化RAG服务
    try:
        service_config = config.get_service_config()
        rag_service = RAGService(service_config)
        logger.info(f"RAG service initialized: {rag_service.is_available}")
    except Exception as e:
        logger.error(f"Failed to initialize RAG service: {e}")
        raise
    
    # 初始化批量处理器
    if config.batch_config.get("enabled"):
        try:
            batch_processor = BatchProcessor(rag_service, config.batch_config)
            batch_router.set_batch_processor(batch_processor)
            
            # 启动批量处理器
            await batch_processor.start()
            logger.info("Batch processor started")
        except Exception as e:
            logger.error(f"Failed to initialize batch processor: {e}")
    
    logger.info("Application startup complete")
    
    yield
    
    # 关闭批量处理器
    if batch_processor:
        await batch_processor.stop()
        logger.info("Batch processor stopped")
    
    logger.info("Application shutdown complete")


# 创建FastAPI应用
app = FastAPI(
    title=config.app_name,
    version=config.app_version,
    description="基于WebSocket的实时检索增强生成(RAG)服务，支持流式语音识别处理和智能问答",
    lifespan=lifespan
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册批量处理路由
app.include_router(batch_router.router)

# 挂载静态文件
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/")
async def root():
    """根路径 - 返回测试网页"""
    static_index = os.path.join(static_dir, "index.html")
    if os.path.exists(static_index):
        return FileResponse(static_index)
    return {
        "name": config.app_name,
        "version": config.app_version,
        "status": "running"
    }


@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """健康检查端点
    
    Returns:
        Dict[str, Any]: 健康检查结果
    """
    # 检查服务状态
    services_health = await rag_service.health_check() if rag_service else {}
    
    # 检查批量处理器状态
    batch_status = None
    if batch_processor:
        batch_status = await batch_processor.get_status()
    
    # 判断总体状态
    rag_ok = services_health.get("rag", False)
    search_ok = services_health.get("search", False)
    
    if rag_ok or search_ok:
        status = "healthy"
    elif rag_service and rag_service.is_available:
        status = "degraded"
    else:
        status = "unhealthy"
    
    return {
        "status": status,
        "version": config.app_version,
        "services": {
            "rag": rag_ok,
            "search": search_ok,
            "batch_processing": batch_status.get("is_running") if batch_status else False
        },
        "providers": services_health.get("providers", {})
    }


@app.websocket(config.ws_path)
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket端点
    
    处理实时ASR文本和RAG查询的WebSocket连接。
    
    Args:
        websocket: WebSocket连接对象
    """
    if not rag_service:
        await websocket.close(code=1011, reason="RAG service not available")
        return
    
    await ws_router.websocket_endpoint(websocket, rag_service)


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=config.host,
        port=config.port,
        reload=config.debug,
        log_level="debug" if config.debug else "info"
    )

"""Realtime RAG WebSocket 应用"""
from fastapi import FastAPI
from app.config import config
from app.routers import websocket
from app.services.rag_service import initialize_rag_service, get_rag_service

app = FastAPI(
    title=config.APP_TITLE,
    version=config.APP_VERSION,
    description="基于 WebSocket 的实时 RAG 服务，支持多种 RAG 和搜索提供商"
)

app.include_router(websocket.router)

@app.on_event("startup")
async def startup_event():
    config.validate()
    # 初始化 RAG 服务
    service_config = config.get_service_config()
    rag_service = initialize_rag_service(service_config)
    
    # 检查服务可用性
    if not rag_service.is_available():
        print("⚠️  警告: 没有可用的 RAG 或搜索提供商")
    else:
        print("✓ RAG 服务已初始化")
        provider_info = rag_service.get_provider_info()
        for service_type, info in provider_info.items():
            print(f"  - {service_type}: {info['name']} ({info['type']})")

@app.get("/health")
async def health_check():
    rag_service = get_rag_service()
    service_status = {}
    
    if rag_service:
        service_status = await rag_service.health_check()
        provider_info = rag_service.get_provider_info()
    else:
        provider_info = {}
    
    return {
        "status": "healthy",
        "version": config.APP_VERSION,
        "services": service_status,
        "providers": provider_info
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

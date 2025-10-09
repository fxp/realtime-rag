"""Realtime RAG WebSocket 应用"""
from fastapi import FastAPI
from app.config import config
from app.routers import websocket

app = FastAPI(
    title=config.APP_TITLE,
    version=config.APP_VERSION,
    description="基于 WebSocket 的实时 RAG 服务，集成 Dify Chat API"
)

app.include_router(websocket.router)

@app.on_event("startup")
async def startup_event():
    config.validate()

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": config.APP_VERSION,
        "dify_configured": bool(config.DIFY_API_KEY)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

"""WebSocket路由处理"""

from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict
import json
import uuid
import asyncio
import logging
from app.models.session import SessionState
from app.services.rag_service import RAGService
from app.services.text_utils import split_answer_into_chunks

logger = logging.getLogger(__name__)

# 全局会话存储
sessions: Dict[str, SessionState] = {}


async def websocket_endpoint(websocket: WebSocket, rag_service: RAGService):
    """WebSocket端点处理函数
    
    处理WebSocket连接的完整生命周期，包括：
    - 连接建立和会话创建
    - 消息接收和处理
    - 状态更新和答案流式传输
    - 错误处理和连接断开
    
    Args:
        websocket: WebSocket连接对象
        rag_service: RAG服务实例
    """
    # 接受连接
    await websocket.accept()
    
    # 生成会话ID
    session_id = str(uuid.uuid4())
    session = SessionState(session_id)
    sessions[session_id] = session
    
    logger.info(f"WebSocket connected: {session_id}")
    
    # 发送连接确认
    await send_message(websocket, {
        "type": "ack",
        "message": "connected",
        "session_id": session_id
    })
    
    # 发送初始状态
    await send_status(websocket, session_id, "listening", "等待ASR文本输入")
    
    try:
        while True:
            # 接收消息
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                await handle_message(websocket, session, message, rag_service)
            except json.JSONDecodeError:
                await send_error(websocket, session_id, "INVALID_JSON", "无效的JSON格式")
            except Exception as e:
                logger.error(f"Error handling message: {e}")
                await send_error(websocket, session_id, "SERVER_ERROR", str(e))
    
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        # 清理会话
        if session_id in sessions:
            # 取消正在进行的查询
            if session.has_active_query:
                session.current_query_task.cancel()
            del sessions[session_id]
        
        await send_status(websocket, session_id, "closed", "连接已关闭")


async def handle_message(websocket: WebSocket, session: SessionState, 
                        message: Dict, rag_service: RAGService):
    """处理接收到的消息
    
    Args:
        websocket: WebSocket连接对象
        session: 会话状态
        message: 接收到的消息
        rag_service: RAG服务实例
    """
    message_type = message.get("type")
    
    if message_type == "asr_chunk":
        await handle_asr_chunk(websocket, session, message, rag_service)
    elif message_type == "control":
        await handle_control(websocket, session, message, rag_service)
    elif message_type == "keepalive":
        await send_message(websocket, {
            "type": "ack",
            "received_type": "keepalive",
            "session_id": session.session_id
        })
    else:
        await send_error(websocket, session.session_id, 
                        "UNSUPPORTED_TYPE", f"不支持的消息类型: {message_type}")


async def handle_asr_chunk(websocket: WebSocket, session: SessionState,
                          message: Dict, rag_service: RAGService):
    """处理ASR文本块
    
    Args:
        websocket: WebSocket连接对象
        session: 会话状态
        message: ASR消息
        rag_service: RAG服务实例
    """
    text = message.get("text", "").strip()
    is_final = message.get("is_final", False)
    
    if not text:
        return
    
    # 如果会话暂停，确认但不处理
    if session.is_paused:
        await send_message(websocket, {
            "type": "ack",
            "received_type": "asr_chunk",
            "message": "paused",
            "session_id": session.session_id
        })
        return
    
    # 添加文本块
    session.add_chunk(text, is_final)
    
    # 确认接收
    await send_message(websocket, {
        "type": "ack",
        "received_type": "asr_chunk",
        "is_final": is_final,
        "session_id": session.session_id
    })
    
    # 如果是最终化文本，检查是否像问题
    if is_final:
        if session.looks_like_question():
            # 触发RAG查询
            await process_question(websocket, session, rag_service)
        else:
            await send_status(websocket, session.session_id, 
                            "waiting_for_question", "等待完整问题")


async def handle_control(websocket: WebSocket, session: SessionState,
                        message: Dict, rag_service: RAGService):
    """处理控制消息
    
    Args:
        websocket: WebSocket连接对象
        session: 会话状态
        message: 控制消息
        rag_service: RAG服务实例
    """
    action = message.get("action")
    
    if action == "pause":
        session.is_paused = True
        await send_status(websocket, session.session_id, "paused", "会话已暂停")
    
    elif action == "resume":
        session.is_paused = False
        await send_status(websocket, session.session_id, "listening", "会话已恢复")
    
    elif action == "stop":
        # 取消当前查询
        if session.has_active_query:
            session.current_query_task.cancel()
        session.reset()
        await send_status(websocket, session.session_id, "idle", "会话已停止")
    
    elif action == "instant_query":
        # 即时查询，强制查询当前文本
        if session.aggregated_text:
            await send_status(websocket, session.session_id, 
                            "instant_query", "执行即时查询", mode="instant")
            await process_question(websocket, session, rag_service, instant=True)
        else:
            await send_error(websocket, session.session_id, 
                           "NO_FINAL_ASR", "没有可用的最终化ASR文本")
    
    else:
        await send_error(websocket, session.session_id, 
                        "UNKNOWN_ACTION", f"未知的控制动作: {action}")


async def process_question(websocket: WebSocket, session: SessionState,
                          rag_service: RAGService, instant: bool = False):
    """处理问题并查询RAG服务
    
    Args:
        websocket: WebSocket连接对象
        session: 会话状态
        rag_service: RAG服务实例
        instant: 是否为即时查询
    """
    question = session.aggregated_text
    
    if not question:
        await send_error(websocket, session.session_id, 
                        "EMPTY_QUESTION", "问题内容为空")
        return
    
    # 检查是否有正在进行的查询
    if session.has_active_query and not instant:
        logger.warning(f"Query already in progress for session: {session.session_id}")
        return
    
    try:
        # 发送状态更新
        await send_status(websocket, session.session_id, 
                        "analyzing", f"分析问题: {question[:50]}...", 
                        question=question)
        
        await send_status(websocket, session.session_id, 
                        "querying_rag", "正在查询RAG服务",
                        question=question)
        
        # 查询RAG服务
        result = await rag_service.query(question)
        
        # 流式发送答案
        await stream_answer(websocket, session.session_id, result.content)
        
        # 重置会话（准备下一个问题）
        session.reset()
        await send_status(websocket, session.session_id, "idle", "等待新的问题")
        
    except Exception as e:
        logger.error(f"RAG query failed: {e}")
        await send_error(websocket, session.session_id, 
                        "RAG_ERROR", f"RAG查询失败: {str(e)}")
        session.reset()


async def stream_answer(websocket: WebSocket, session_id: str, answer: str):
    """流式发送答案
    
    Args:
        websocket: WebSocket连接对象
        session_id: 会话ID
        answer: 完整答案
    """
    # 分割答案为块
    chunks = split_answer_into_chunks(answer, chunk_size=120)
    
    for idx, chunk in enumerate(chunks):
        is_final = (idx == len(chunks) - 1)
        
        await send_message(websocket, {
            "type": "answer",
            "stream_index": idx,
            "content": chunk,
            "final": is_final,
            "session_id": session_id
        })
        
        # 添加小延迟，模拟流式传输
        if not is_final:
            await asyncio.sleep(0.05)


async def send_message(websocket: WebSocket, message: Dict):
    """发送消息
    
    Args:
        websocket: WebSocket连接对象
        message: 要发送的消息
    """
    try:
        await websocket.send_json(message)
    except Exception as e:
        logger.error(f"Failed to send message: {e}")


async def send_status(websocket: WebSocket, session_id: str, 
                     stage: str, note: str = "", **kwargs):
    """发送状态消息
    
    Args:
        websocket: WebSocket连接对象
        session_id: 会话ID
        stage: 当前阶段
        note: 备注信息
        **kwargs: 额外字段
    """
    await send_message(websocket, {
        "type": "status",
        "session_id": session_id,
        "stage": stage,
        "note": note,
        **kwargs
    })


async def send_error(websocket: WebSocket, session_id: str, 
                    code: str, message: str, **kwargs):
    """发送错误消息
    
    Args:
        websocket: WebSocket连接对象
        session_id: 会话ID
        code: 错误代码
        message: 错误消息
        **kwargs: 额外字段
    """
    await send_message(websocket, {
        "type": "error",
        "session_id": session_id,
        "code": code,
        "message": message,
        **kwargs
    })

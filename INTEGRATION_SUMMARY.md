# WebSocket + Dify RAG 集成总结

## 📋 修改概览

本次更新在 WebSocket 服务端集成了真实的 Dify Chat API 调用，使用**阻塞模式**获取完整答案并通过 WebSocket 返回给客户端。

## ✅ 完成的工作

### 1. 核心功能集成

#### `app/main.py` - WebSocket 服务端

**新增内容**:
- ✅ 导入 `httpx` 和 `os` 模块
- ✅ 环境变量配置（`DIFY_API_KEY`, `DIFY_BASE_URL`, `DIFY_TIMEOUT`）
- ✅ `run_dify_rag()` 函数 - 调用 Dify Chat API（阻塞模式）
- ✅ 完善的错误处理和日志
- ✅ Token 使用统计

**关键代码**:
```python
async def run_dify_rag(
    query: str,
    user: str = "websocket-user",
    conversation_id: Optional[str] = None,
) -> str:
    """调用 Dify Chat API 获取真实的 RAG 回答（阻塞模式）"""
    
    # 准备请求
    url = f"{DIFY_BASE_URL}/chat-messages"
    headers = {
        "Authorization": f"Bearer {DIFY_API_KEY}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "query": query,
        "user": user,
        "response_mode": "blocking",  # 阻塞模式
        "inputs": {},
    }
    
    # 发送请求并提取 answer
    async with httpx.AsyncClient(timeout=DIFY_TIMEOUT) as client:
        response = await client.post(url, headers=headers, json=payload)
        result = response.json()
        return result.get("answer", "")
```

**调用位置** (第 265-269 行):
```python
# 使用真实的 Dify RAG 调用
answer = await run_dify_rag(
    query=question,
    user=f"ws-user-{session.session_id}",
    conversation_id=None,  # 可选：支持多轮对话
)
```

### 2. Dify API 客户端工具

#### `scripts/dify_workflow_client.py`

完整的 Dify Chat API 测试客户端，基于[官方文档](https://docs.dify.ai/api-reference/chat/send-chat-message)。

**主要功能**:
- ✅ 流式响应（SSE 实时推流）
- ✅ 阻塞式响应（等待完整结果）
- ✅ 多轮对话（conversation_id）
- ✅ Vision 模型支持（图片输入）
- ✅ Token 使用统计
- ✅ 检索资源展示（RAG）

**使用示例**:
```bash
# 流式模式
python scripts/dify_workflow_client.py \
  --api-key YOUR_KEY \
  --query "什么是 RAG？"

# 阻塞模式（与 WebSocket 服务端一致）
python scripts/dify_workflow_client.py \
  --api-key YOUR_KEY \
  --query "解释一下" \
  --blocking
```

### 3. 配置文件

#### `env.example`
环境变量配置示例：
```bash
DIFY_API_KEY=app-your-api-key-here
DIFY_BASE_URL=https://api.dify.ai/v1
DIFY_TIMEOUT=60.0
```

### 4. 测试脚本

#### `scripts/test_dify_chat.sh`
Dify API 自动化测试：
- 基本连接测试
- 阻塞模式测试
- 多轮对话测试
- 会话列表测试

#### `scripts/test_websocket_with_dify.sh`
WebSocket + Dify 完整集成测试：
- 启动 WebSocket 服务端
- 运行 WebSocket 客户端
- 自动清理资源

### 5. 完整文档

| 文件 | 用途 |
|------|------|
| `README.md` | 项目总览（已更新为中文） |
| `RUN_SERVER.md` | WebSocket 服务端运行指南 |
| `scripts/README_DIFY.md` | Dify API 完整文档 |
| `scripts/QUICKSTART.md` | 3 分钟快速上手 |
| `CHANGELOG.md` | 更新日志 |
| `INTEGRATION_SUMMARY.md` | 本文档 |

### 6. 依赖更新

#### `requirements.txt`
新增：
```
httpx==0.27.0
```

## 🚀 快速开始

### 步骤 1: 安装依赖

```bash
pip install -r requirements.txt
```

### 步骤 2: 配置环境

```bash
# 方法 1: 环境变量
export DIFY_API_KEY="app-your-api-key-here"

# 方法 2: 创建 .env 文件
cp env.example .env
# 编辑 .env 文件
```

### 步骤 3: 启动服务

```bash
# 开发模式（推荐）
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 生产模式
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 步骤 4: 测试

```bash
# WebSocket 测试
python scripts/ws_client.py

# 完整集成测试（推荐）
./scripts/test_websocket_with_dify.sh YOUR_API_KEY
```

## 📊 数据流

```
┌─────────────┐         ┌─────────────────┐         ┌──────────────┐
│  WebSocket  │         │   FastAPI       │         │   Dify       │
│   客户端    │────────>│   服务端        │────────>│   Chat API   │
│             │  ASR文本 │                 │  阻塞调用 │              │
└─────────────┘         └─────────────────┘         └──────────────┘
       ↑                        │                           │
       │                        │   提取 answer             │
       │                        │<──────────────────────────┤
       │    流式返回             │                           │
       │    (分块)              │                           │
       └────────────────────────┘
```

## 🔧 核心实现细节

### WebSocket 消息流程

1. **接收 ASR 文本**
   ```json
   {
     "type": "asr_chunk",
     "text": "什么是 RAG？",
     "is_final": true
   }
   ```

2. **问题检测**
   - 检查是否包含问题标识（`?`, `吗`, `怎么` 等）
   - 英文关键词（`what`, `how`, `why` 等）

3. **调用 Dify API**
   ```python
   answer = await run_dify_rag(query=question, user="ws-user-xxx")
   ```

4. **分块返回**
   ```json
   {
     "type": "answer",
     "stream_index": 0,
     "content": "RAG（检索增强生成）是...",
     "final": false
   }
   ```

### Dify API 调用（阻塞模式）

**请求**:
```json
{
  "query": "什么是 RAG？",
  "user": "ws-user-session-123",
  "response_mode": "blocking",
  "inputs": {}
}
```

**响应**:
```json
{
  "event": "message",
  "message_id": "9da23599-e713-...",
  "conversation_id": "45701982-8118-...",
  "answer": "RAG（检索增强生成）是一种...",
  "metadata": {
    "usage": {
      "total_tokens": 157,
      "total_price": "0.000123",
      "currency": "USD"
    }
  }
}
```

## 🎯 关键特性

### 1. 阻塞模式的优势
- ✅ 获取完整答案，无需处理流式数据
- ✅ 代码简单，易于维护
- ✅ 适合 WebSocket 场景（自带流式传输）
- ✅ 错误处理更直观

### 2. 错误处理
- ✅ API Key 未配置 → 返回友好提示
- ✅ HTTP 错误 → 记录日志并返回错误信息
- ✅ 网络超时 → 可配置超时时间
- ✅ 异常捕获 → 防止服务崩溃

### 3. 日志和监控
```
[Dify RAG] Tokens: 157, Price: 0.000123 USD
[Dify RAG Error] Dify API HTTP 错误 401: ...
```

## ⚙️ 配置选项

### 环境变量

| 变量 | 说明 | 必需 | 默认值 |
|------|------|------|--------|
| `DIFY_API_KEY` | Dify API 密钥 | ✅ | - |
| `DIFY_BASE_URL` | API 基础 URL | ❌ | `https://api.dify.ai/v1` |
| `DIFY_TIMEOUT` | 请求超时（秒） | ❌ | `60.0` |

### 切换模拟/真实 RAG

编辑 `app/main.py` 第 265 行：

```python
# 真实 API
answer = await run_dify_rag(query=question, ...)

# 模拟 API（测试用）
answer = await run_mock_rag(question)
```

## 🧪 测试指南

### 1. 单独测试 Dify API

```bash
# 基本测试
python scripts/dify_workflow_client.py \
  --api-key YOUR_KEY \
  --query "你好"

# 完整测试套件
./scripts/test_dify_chat.sh YOUR_API_KEY
```

### 2. 测试 WebSocket 集成

```bash
# 启动服务端
export DIFY_API_KEY="your-key"
uvicorn app.main:app --reload

# 在另一个终端运行客户端
python scripts/ws_client.py
```

### 3. 自动化集成测试

```bash
./scripts/test_websocket_with_dify.sh YOUR_API_KEY
```

## 🐛 故障排除

### 问题 1: `错误：未配置 DIFY_API_KEY`

**原因**: 环境变量未设置

**解决方案**:
```bash
export DIFY_API_KEY="app-your-key"
# 或者创建 .env 文件
```

### 问题 2: `HTTP 错误 401`

**原因**: API 密钥无效

**解决方案**: 
- 检查密钥是否正确
- 确认是 Chat 应用的密钥
- 验证格式：`app-xxxxx...`

### 问题 3: `HTTP 错误 404`

**原因**: API 端点不正确

**解决方案**:
```bash
# 确保包含 /v1
export DIFY_BASE_URL="https://api.dify.ai/v1"
# 自部署
export DIFY_BASE_URL="http://localhost/v1"
```

### 问题 4: 连接超时

**原因**: 网络问题或响应时间过长

**解决方案**:
```bash
# 增加超时时间
export DIFY_TIMEOUT="120.0"
```

## 📈 性能考虑

### 阻塞模式 vs 流式模式

| 特性 | 阻塞模式 | 流式模式 |
|------|----------|----------|
| 响应速度 | 完成后返回 | 实时推送 |
| 实现复杂度 | ⭐ 简单 | ⭐⭐⭐ 复杂 |
| 适用场景 | WebSocket | Web 页面 |
| Token 统计 | ✅ 准确 | ⚠️ 需累加 |
| 错误处理 | ✅ 简单 | ⚠️ 需状态机 |

**为什么选择阻塞模式？**
- WebSocket 本身就是实时连接
- 服务端可以自行分块流式返回
- 实现简单，错误处理清晰
- 完整的 metadata 和使用统计

### 优化建议

1. **连接复用**: httpx AsyncClient 自动处理
2. **超时设置**: 根据实际情况调整 `DIFY_TIMEOUT`
3. **多进程**: `uvicorn --workers 4`
4. **多轮对话**: 传入 `conversation_id` 减少上下文传输

## 🔒 安全建议

1. ✅ **API Key 保护**: 使用环境变量，不要硬编码
2. ✅ **HTTPS/WSS**: 生产环境使用加密连接
3. ✅ **认证机制**: 添加 WebSocket 认证
4. ✅ **频率限制**: 防止 API 滥用
5. ✅ **日志脱敏**: 不记录敏感信息

## 📚 参考资源

- [Dify 官方文档](https://docs.dify.ai/)
- [Chat API 文档](https://docs.dify.ai/api-reference/chat/send-chat-message)
- [FastAPI WebSocket](https://fastapi.tiangolo.com/advanced/websockets/)
- [httpx 文档](https://www.python-httpx.org/)

## 🎉 总结

本次集成实现了：
- ✅ WebSocket 服务端调用真实 Dify RAG
- ✅ 使用阻塞模式获取完整答案
- ✅ 完善的错误处理和日志
- ✅ 丰富的测试工具和文档
- ✅ 灵活的配置选项

**下一步建议**:
- 添加会话管理和持久化
- 实现 WebSocket 认证
- 添加监控和指标
- 部署到生产环境

---

**如有问题，请查看相关文档或提 Issue！**

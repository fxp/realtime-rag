# WebSocket 服务端运行指南

本项目的 WebSocket 服务端已集成真实的 Dify Chat API 调用，用于提供实时 RAG 功能。

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

创建 `.env` 文件（或直接设置环境变量）：

```bash
# 复制示例配置文件
cp .env.example .env

# 编辑 .env 文件，填入你的 Dify API 密钥
# DIFY_API_KEY=app-your-api-key-here
```

或者直接在命令行设置：

```bash
export DIFY_API_KEY="app-your-api-key-here"
export DIFY_BASE_URL="https://api.dify.ai/v1"  # 可选
export DIFY_TIMEOUT="60.0"  # 可选
```

### 3. 启动服务

```bash
# 方法 1: 使用 Python 直接运行
python -m app.main

# 方法 2: 使用 uvicorn（推荐，支持热加载）
USE_MOCK_RAG=1 uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 方法 3: 生产环境（多进程）
USE_MOCK_RAG=0 uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

服务将在 `http://localhost:8000` 启动。

### 4. 测试连接

使用提供的测试客户端：

```bash
python scripts/ws_client.py

### 5. 健康检查

```bash
curl -s http://localhost:8000/healthz
```
```

## 📡 WebSocket 端点

- **URL**: `ws://localhost:8000/ws/realtime-asr`
- **协议**: JSON over WebSocket

## 🔧 环境变量说明

| 变量名 | 说明 | 必需 | 默认值 |
|--------|------|------|--------|
| `DIFY_API_KEY` | Dify API 密钥 | 是 | - |
| `DIFY_BASE_URL` | Dify API 基础 URL | 否 | `https://api.dify.ai/v1` |
| `DIFY_TIMEOUT` | API 请求超时时间（秒） | 否 | `60.0` |

## 💬 消息协议

### 客户端发送的消息

#### ASR 文本块

```json
{
  "type": "asr_chunk",
  "text": "用户说的文字",
  "is_final": true,
  "session_id": "可选的会话ID"
}
```

#### 控制消息

```json
{
  "type": "control",
  "action": "pause|resume|stop"
}
```

### 服务端返回的消息

#### 状态消息

```json
{
  "type": "status",
  "stage": "listening|analyzing|querying_rag|idle|paused"
}
```

#### 回答消息（分块流式返回）

```json
{
  "type": "answer",
  "stream_index": 0,
  "content": "回答内容的一部分",
  "final": false
}
```

#### 确认消息

```json
{
  "type": "ack",
  "received_type": "asr_chunk",
  "session_id": "会话ID"
}
```

#### 错误消息

```json
{
  "type": "error",
  "code": "ERROR_CODE",
  "message": "错误描述"
}
```

## 🔄 工作流程

1. **建立连接**: 客户端连接到 WebSocket，收到连接确认和会话 ID
2. **监听阶段**: 服务端处于 `listening` 状态，等待 ASR 文本块
3. **接收文本**: 客户端发送 ASR 文本块（`is_final: false` 表示中间结果）
4. **问题检测**: 当收到 `is_final: true` 的文本块时，检查是否包含问题
5. **调用 RAG**: 如果检测到问题，调用 Dify Chat API 获取答案
6. **流式返回**: 将答案分块流式返回给客户端
7. **重置会话**: 完成后重置会话，等待下一个问题

## 🎯 核心功能

### Dify RAG 集成

服务端使用 **阻塞模式** 调用 Dify Chat API：

```python
answer = await run_dify_rag(
    query=question,
    user=f"ws-user-{session.session_id}",
    conversation_id=None,  # 可以传入 session_id 支持多轮对话
)
```

**特性**：
- ✅ 阻塞式调用，确保完整回答
- ✅ 自动错误处理和重试
- ✅ Token 使用统计（在日志中）
- ✅ 支持多轮对话（可选）
- ✅ 完善的错误提示

### 切换到模拟模式

如果需要测试而不调用真实 API，可以修改 `app/main.py` 第 265 行：

```python
# 真实 Dify API 调用
answer = await run_dify_rag(query=question, ...)

# 改为模拟调用
answer = await run_mock_rag(question)
```

## 🐛 调试

### 查看日志

服务端会在控制台输出调试信息：

```
[Dify RAG] Tokens: 157, Price: 0.000123 USD
```

### 常见问题

#### 1. `错误：未配置 DIFY_API_KEY 环境变量`

**解决方案**: 设置环境变量或创建 `.env` 文件

```bash
export DIFY_API_KEY="app-your-key"
```

#### 2. `Dify API HTTP 错误 401`

**解决方案**: 检查 API 密钥是否正确

#### 3. `Dify API HTTP 错误 404`

**解决方案**: 检查 `DIFY_BASE_URL` 是否正确，确保包含 `/v1`

#### 4. `调用 RAG 服务失败：请求错误`

**解决方案**: 
- 检查网络连接
- 如果是自部署实例，确认服务是否运行
- 增加 `DIFY_TIMEOUT` 值

## 📊 监控和优化

### Token 使用监控

服务端会在每次调用后打印 Token 使用情况：

```
[Dify RAG] Tokens: 1161, Price: 0.001289 USD
```

### 性能优化建议

1. **使用连接池**: httpx 的 AsyncClient 已自动处理
2. **调整超时时间**: 根据实际响应时间调整 `DIFY_TIMEOUT`
3. **启用多轮对话**: 传入 `conversation_id` 可以减少上下文重复传输
4. **监控错误率**: 注意日志中的 `[Dify RAG Error]` 消息

## 🔐 安全建议

1. **保护 API 密钥**: 不要在代码中硬编码，使用环境变量
2. **使用 HTTPS**: 生产环境建议使用 wss:// 而不是 ws://
3. **添加认证**: 在 WebSocket 连接时添加认证机制
4. **限流保护**: 防止滥用，可以添加频率限制
5. **日志脱敏**: 生产环境不要记录敏感信息

## 📚 相关文档

- [WebSocket 客户端文档](./scripts/ws_client.py)
- [Dify Chat API 文档](./scripts/README_DIFY.md)
- [快速开始指南](./scripts/QUICKSTART.md)
- [Dify 官方文档](https://docs.dify.ai/)

## 🚢 生产部署

### 使用 Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV DIFY_API_KEY=""
ENV DIFY_BASE_URL="https://api.dify.ai/v1"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 使用 systemd

```ini
[Unit]
Description=Realtime RAG WebSocket Service
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/realtime-rag
Environment="DIFY_API_KEY=app-your-key"
Environment="DIFY_BASE_URL=https://api.dify.ai/v1"
ExecStart=/usr/bin/python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

### 使用 Nginx 反向代理

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

---

**祝运行顺利！** 有问题欢迎提 Issue。

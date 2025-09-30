# 更新日志

## 2025-09-30 - Dify RAG 集成

### ✨ 新增功能

#### 1. WebSocket 服务端集成 Dify Chat API

- **文件**: `app/main.py`
- **功能**: 添加真实的 Dify RAG 调用，替换原有的模拟实现
- **调用方式**: 阻塞模式（blocking mode）
- **关键改动**:
  - 新增 `run_dify_rag()` 函数，使用 httpx 调用 Dify Chat API
  - 支持环境变量配置（`DIFY_API_KEY`, `DIFY_BASE_URL`, `DIFY_TIMEOUT`）
  - 完善的错误处理和日志记录
  - 保留 `run_mock_rag()` 函数用于测试

```python
# 真实 Dify RAG 调用
answer = await run_dify_rag(
    query=question,
    user=f"ws-user-{session.session_id}",
    conversation_id=None,  # 可选：支持多轮对话
)
```

#### 2. Dify Chat API 客户端

- **文件**: `scripts/dify_workflow_client.py`
- **功能**: 完整的 Dify Chat API 测试客户端
- **基于**: [Dify 官方文档](https://docs.dify.ai/api-reference/chat/send-chat-message)
- **特性**:
  - ✅ 流式响应（SSE）
  - ✅ 阻塞式响应
  - ✅ 多轮对话支持
  - ✅ Vision 模型支持
  - ✅ Token 使用统计
  - ✅ 检索资源展示（RAG）

#### 3. 配置和文档

新增文件：
- `env.example` - 环境变量配置示例
- `RUN_SERVER.md` - WebSocket 服务端运行指南
- `scripts/README_DIFY.md` - Dify API 完整文档
- `scripts/QUICKSTART.md` - 3 分钟快速上手
- `scripts/test_dify_chat.sh` - Dify API 自动测试脚本
- `scripts/test_websocket_with_dify.sh` - WebSocket + Dify 集成测试

更新文件：
- `README.md` - 更新为中文，添加完整功能说明
- `requirements.txt` - 添加 `httpx==0.27.0` 依赖

### 🔧 技术细节

#### WebSocket 服务端集成

**调用流程**:
1. 客户端发送 ASR 文本（`is_final: true`）
2. 服务端检测是否为问题
3. 调用 Dify Chat API（阻塞模式）
4. 提取 `answer` 字段
5. 分块流式返回给客户端

**错误处理**:
- API Key 未配置：返回错误提示
- HTTP 错误：记录日志并返回友好提示
- 网络错误：捕获并返回错误信息
- 超时处理：可通过环境变量调整

**日志示例**:
```
[Dify RAG] Tokens: 157, Price: 0.000123 USD
[Dify RAG Error] Dify API HTTP 错误 401: ...
```

#### Dify API 客户端

**支持的事件类型**（流式模式）:
- `message`: 完整消息
- `message_end`: 消息结束（含元数据）
- `agent_thought`: Agent 思考过程
- `agent_message`: Agent 消息
- `error`: 错误事件
- `ping`: 心跳

**命令行示例**:
```bash
# 流式模式
python scripts/dify_workflow_client.py \
  --api-key YOUR_KEY \
  --query "你好"

# 阻塞模式
python scripts/dify_workflow_client.py \
  --api-key YOUR_KEY \
  --query "什么是 RAG？" \
  --blocking

# 多轮对话
python scripts/dify_workflow_client.py \
  --api-key YOUR_KEY \
  --query "继续" \
  --conversation-id conv-123
```

### 📦 依赖更新

新增：
- `httpx==0.27.0` - 异步 HTTP 客户端

### 🚀 使用方法

#### 1. 配置环境变量

```bash
export DIFY_API_KEY="app-your-api-key-here"
export DIFY_BASE_URL="https://api.dify.ai/v1"  # 可选
export DIFY_TIMEOUT="60.0"  # 可选
```

#### 2. 启动服务

```bash
# 开发模式
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 生产模式
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

#### 3. 测试

```bash
# WebSocket 测试
python scripts/ws_client.py

# Dify API 测试
./scripts/test_dify_chat.sh YOUR_API_KEY

# 完整集成测试
./scripts/test_websocket_with_dify.sh YOUR_API_KEY
```

### 🔄 切换模拟/真实 RAG

在 `app/main.py` 第 265-269 行：

```python
# 使用真实 Dify API
answer = await run_dify_rag(
    query=question,
    user=f"ws-user-{session.session_id}",
    conversation_id=None,
)

# 或者使用模拟调用（测试用）
# answer = await run_mock_rag(question)
```

### 📊 性能和限制

- **阻塞模式**: 等待完整响应，适合 WebSocket 场景
- **超时设置**: 默认 60 秒，可通过 `DIFY_TIMEOUT` 调整
- **Cloudflare 限制**: 最长 100 秒
- **Agent 模式**: 仅支持流式响应

### 🔒 安全建议

1. ✅ API Key 使用环境变量，不要硬编码
2. ✅ 生产环境使用 HTTPS/WSS
3. ✅ 添加 WebSocket 认证机制
4. ✅ 实施请求频率限制
5. ✅ 日志脱敏处理

### 🐛 已知问题

无

### 📝 待办事项

- [ ] 添加会话管理（多轮对话持久化）
- [ ] 添加 WebSocket 认证
- [ ] 添加请求频率限制
- [ ] 添加监控和指标收集
- [ ] 添加单元测试
- [ ] 添加 Docker 配置
- [ ] 添加 CI/CD 配置

### 🙏 致谢

基于 [Dify 官方 API 文档](https://docs.dify.ai/api-reference/chat/send-chat-message)

---

## 版本历史

### v0.2.0 - 2025-09-30
- 集成 Dify Chat API
- 添加完整文档
- 添加测试脚本

### v0.1.0 - 初始版本
- 基础 WebSocket 服务
- 模拟 RAG 实现
- ASR 文本处理

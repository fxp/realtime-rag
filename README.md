# Realtime RAG WebSocket 服务

基于 WebSocket 的实时 RAG（检索增强生成）服务，集成 Dify Chat API。

## ✨ 主要功能

- 🔌 **WebSocket 实时通信**: 支持 ASR 文本流的实时处理
- 🤖 **Dify RAG 集成**: 使用 Dify Chat API 提供智能问答
- 💬 **多轮对话**: 支持会话上下文管理
- 📊 **流式响应**: 分块返回答案，提升用户体验
- 🎯 **问题检测**: 自动识别用户问题
- 🛡️ **错误处理**: 完善的异常处理和错误提示

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置 Dify API

```bash
# 设置环境变量
export DIFY_API_KEY="app-your-api-key-here"

# 或者创建 .env 文件
cp env.example .env
# 编辑 .env 文件，填入你的 API 密钥
```

### 3. 启动服务

```bash
# 开发模式（支持热加载）
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 或者使用 Python 直接运行
python -m app.main
```

### 4. 测试连接

```bash
# 使用 WebSocket 客户端测试
python scripts/ws_client.py

# 或者测试 Dify API 直接调用
python scripts/dify_workflow_client.py --api-key YOUR_KEY --query "你好"
```

## 📚 文档

- 📖 [服务端运行指南](./RUN_SERVER.md) - WebSocket 服务端详细文档
- 🔧 [Dify API 使用指南](./scripts/README_DIFY.md) - Dify Chat API 完整文档
- ⚡ [快速开始](./scripts/QUICKSTART.md) - 3 分钟快速上手
- 📐 [时序图](./sequence_diagram.md) - 系统交互流程

## 🏗️ 项目结构

```
realtime-rag/
├── app/
│   └── main.py              # WebSocket 服务端（含 Dify RAG 集成）
├── scripts/
│   ├── ws_client.py         # WebSocket 测试客户端
│   ├── dify_workflow_client.py  # Dify Chat API 客户端
│   ├── test_dify_chat.sh    # 自动化测试脚本
│   ├── README_DIFY.md       # Dify API 文档
│   └── QUICKSTART.md        # 快速开始指南
├── requirements.txt         # Python 依赖
├── env.example             # 环境变量配置示例
└── RUN_SERVER.md           # 服务端运行文档
```

## 🔧 配置说明

### 环境变量

| 变量名 | 说明 | 必需 | 默认值 |
|--------|------|------|--------|
| `DIFY_API_KEY` | Dify API 密钥 | 是 | - |
| `DIFY_BASE_URL` | Dify API 地址 | 否 | `https://api.dify.ai/v1` |
| `DIFY_TIMEOUT` | 请求超时（秒） | 否 | `60.0` |

### 获取 Dify API 密钥

1. 访问 [Dify Cloud](https://cloud.dify.ai/) 或你的自部署实例
2. 创建或选择一个 **Chat 应用** 或 **Agent 应用**
3. 进入 **API 访问** 页面，复制 API 密钥

## 💡 使用示例

### WebSocket 客户端消息示例

发送 ASR 文本：

```json
{
  "type": "asr_chunk",
  "text": "什么是 RAG？",
  "is_final": true,
  "session_id": "session-123"
}
```

接收回答：

```json
{
  "type": "answer",
  "stream_index": 0,
  "content": "RAG（检索增强生成）是一种...",
  "final": false
}
```

### 直接调用 Dify API

```bash
# 流式模式（推荐）
python scripts/dify_workflow_client.py \
  --api-key YOUR_KEY \
  --query "什么是人工智能？"

# 阻塞模式
python scripts/dify_workflow_client.py \
  --api-key YOUR_KEY \
  --query "解释机器学习" \
  --blocking

# 多轮对话
python scripts/dify_workflow_client.py \
  --api-key YOUR_KEY \
  --query "继续上一个话题" \
  --conversation-id conv-123
```

## 🔄 工作流程

```
客户端 ──────> WebSocket 服务端 ──────> Dify Chat API
         1. 发送 ASR 文本
                        2. 检测问题
                                      3. 调用 RAG
客户端 <────── WebSocket 服务端 <────── Dify Chat API
         6. 流式返回答案
                        5. 分块处理
                                      4. 返回答案
```

详见 [时序图](./sequence_diagram.md)

## 🧪 测试

### 运行 WebSocket 测试

```bash
# 确保服务端已启动
python scripts/ws_client.py
```

### 运行 Dify API 测试

```bash
./scripts/test_dify_chat.sh YOUR_API_KEY
```

## 🐛 故障排除

### WebSocket 连接问题

1. 确认服务端是否启动：`http://localhost:8000`
2. 检查防火墙设置
3. 查看服务端日志

### Dify API 调用问题

1. **401 错误**: 检查 API 密钥是否正确
2. **404 错误**: 确认 `DIFY_BASE_URL` 包含 `/v1`
3. **超时**: 增加 `DIFY_TIMEOUT` 值
4. **未配置**: 设置 `DIFY_API_KEY` 环境变量

详见 [RUN_SERVER.md](./RUN_SERVER.md#-调试)

## 📊 性能优化

- 使用 **阻塞模式** 确保完整答案
- **连接复用**: httpx AsyncClient 自动处理
- **多进程部署**: `uvicorn --workers 4`
- **多轮对话**: 使用 `conversation_id` 减少上下文传输

## 🚢 生产部署

### Docker 部署

```bash
docker build -t realtime-rag .
docker run -e DIFY_API_KEY="your-key" -p 8000:8000 realtime-rag
```

### Nginx 反向代理

详见 [RUN_SERVER.md](./RUN_SERVER.md#-生产部署)

## 🔒 安全建议

1. ✅ 使用环境变量管理 API 密钥
2. ✅ 生产环境使用 HTTPS/WSS
3. ✅ 添加 WebSocket 认证机制
4. ✅ 实施请求频率限制
5. ✅ 日志脱敏处理

## 📖 相关资源

- [Dify 官方文档](https://docs.dify.ai/)
- [Dify Chat API 参考](https://docs.dify.ai/api-reference/chat/send-chat-message)
- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [WebSocket 协议](https://developer.mozilla.org/en-US/docs/Web/API/WebSocket)

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License
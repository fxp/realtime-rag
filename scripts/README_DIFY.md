# Dify Chat API 测试客户端使用指南

这个脚本用于测试和调试 Dify Chat 应用的连接和功能。

**基于官方文档**: [Dify Chat API 文档](https://docs.dify.ai/api-reference/chat/send-chat-message)

## 安装依赖

```bash
pip install -r requirements.txt
```

## 快速开始

### 1. 准备 API 密钥

首先，你需要在 Dify 控制台获取 API 密钥：

1. 登录 Dify 控制台
2. 选择你的 Chat 应用（或 Agent 应用）
3. 在 "API 访问" 部分找到你的 API 密钥

⚠️ **重要**: 强烈建议将 API 密钥存储在服务器端，不要在客户端共享或存储，以避免 API 密钥泄露。

### 2. 基本使用

```bash
# 发送一个简单的查询（流式模式，推荐）
python scripts/dify_workflow_client.py \
  --api-key YOUR_API_KEY \
  --query "你好，请介绍一下自己"

# 使用阻塞模式（非流式）
python scripts/dify_workflow_client.py \
  --api-key YOUR_API_KEY \
  --query "什么是 RAG？" \
  --blocking
```

### 3. 高级用法

#### 连接到自部署的 Dify 实例

```bash
python scripts/dify_workflow_client.py \
  --api-key YOUR_API_KEY \
  --base-url http://localhost/v1 \
  --query "测试连接"
```

#### 传递输入变量

如果你的应用定义了输入变量（在 Dify 中配置的变量）：

```bash
python scripts/dify_workflow_client.py \
  --api-key YOUR_API_KEY \
  --query "分析这段文本" \
  --inputs '{"language": "zh-CN", "style": "formal"}'
```

#### 多轮对话

使用会话 ID 进行多轮对话：

```bash
# 第一轮对话
python scripts/dify_workflow_client.py \
  --api-key YOUR_API_KEY \
  --query "我想了解 Python" \
  --conversation-id my-conversation-123

# 第二轮对话（使用相同的 conversation-id，系统会记住上下文）
python scripts/dify_workflow_client.py \
  --api-key YOUR_API_KEY \
  --query "它有哪些特点？" \
  --conversation-id my-conversation-123
```

#### 使用 Vision 模型（图片）

对于支持 Vision 的模型，可以传递图片文件：

```bash
python scripts/dify_workflow_client.py \
  --api-key YOUR_API_KEY \
  --query "这张图片里有什么？" \
  --files '[{"type": "image", "transfer_method": "remote_url", "url": "https://example.com/image.jpg"}]'
```

#### 查看会话历史

```bash
python scripts/dify_workflow_client.py \
  --api-key YOUR_API_KEY \
  --list-conversations
```

#### 自定义超时时间

```bash
python scripts/dify_workflow_client.py \
  --api-key YOUR_API_KEY \
  --query "这是一个可能需要较长时间的查询" \
  --timeout 120
```

#### 禁用自动生成对话标题

```bash
python scripts/dify_workflow_client.py \
  --api-key YOUR_API_KEY \
  --query "测试" \
  --no-auto-name
```

## 命令行参数

| 参数 | 说明 | 必需 | 默认值 |
|------|------|------|--------|
| `--api-key` | Dify API 密钥 | 是 | - |
| `--query`, `-q` | 要发送的查询文本 | 是* | - |
| `--base-url` | Dify API 基础 URL | 否 | `https://api.dify.ai/v1` |
| `--user` | 用户标识符（应用内唯一） | 否 | `test-user` |
| `--inputs` | 应用定义的输入变量（JSON 格式） | 否 | `{}` |
| `--blocking` | 使用阻塞模式而不是流式模式 | 否 | `false` |
| `--conversation-id` | 会话 ID（用于多轮对话） | 否 | - |
| `--files` | 文件列表（JSON 格式，用于 Vision） | 否 | - |
| `--no-auto-name` | 不自动生成对话标题 | 否 | `false` |
| `--timeout` | 请求超时时间（秒） | 否 | `60.0` |
| `--list-conversations` | 列出会话历史后退出 | 否 | `false` |

\* 除非使用 `--list-conversations`

## 响应格式

### 流式模式（默认，推荐）

流式模式使用 SSE (Server-Sent Events) 实时显示响应过程：

```
============================================================
发送消息到 Dify Chat API
============================================================
查询: 你好
响应模式: streaming
用户: test-user
============================================================

开始接收流式响应...

────────────────────────────────────────────────────────────
你好！我是一个 AI 助手，很高兴为您服务...

────────────────────────────────────────────────────────────
✅ 消息完成

📊 使用统计:
  - 提示词 tokens: 15
  - 完成 tokens: 42
  - 总计 tokens: 57
  - 总价格: 0.000123 USD

────────────────────────────────────────────────────────────
总共接收到 3 个事件
会话ID: 45701982-8118-4bc5-8e9b-64562b4555f2
消息ID: 9da23599-e713-473b-982c-4328d4f5c78a
```

#### 流式事件类型

根据[官方文档](https://docs.dify.ai/api-reference/chat/send-chat-message)，流式响应可能包含以下事件：

- `message`: 完整消息（在 blocking 模式下）
- `message_end`: 消息结束，包含元数据和使用统计
- `agent_thought`: Agent 思考过程
- `agent_message`: Agent 消息或消息替换
- `error`: 错误事件
- `ping`: 心跳事件

### 阻塞模式

阻塞模式会等待整个处理完成后返回完整结果：

```json
{
  "event": "message",
  "task_id": "c3800678-a077-43df-a102-53f23ed20b88",
  "id": "9da23599-e713-473b-982c-4328d4f5c78a",
  "message_id": "9da23599-e713-473b-982c-4328d4f5c78a",
  "conversation_id": "45701982-8118-4bc5-8e9b-64562b4555f2",
  "mode": "chat",
  "answer": "iPhone 13 Pro Max specs are...",
  "metadata": {
    "usage": {
      "prompt_tokens": 1033,
      "completion_tokens": 128,
      "total_tokens": 1161,
      "total_price": "0.0012890",
      "currency": "USD"
    },
    "retriever_resources": [...]
  },
  "created_at": 1705407629
}
```

⚠️ **注意**: 
- 阻塞模式可能会因长时间处理而被中断
- Agent 助手模式不支持阻塞模式
- Cloudflare 超时限制为 100 秒

## 常见问题

### 1. 认证失败 (401/403)

如果收到认证错误：
- 检查 API 密钥是否正确
- 确认 API 密钥有访问该应用的权限
- 确保 Authorization header 格式正确：`Bearer YOUR_API_KEY`

### 2. 连接超时

如果请求超时：
- 检查网络连接
- 如果是自部署实例，确认 URL 是否正确（注意要包含 `/v1` 路径）
- 尝试增加 `--timeout` 参数的值
- 对于长时间运行的查询，建议使用流式模式

### 3. JSON 解析错误

如果 `--inputs` 或 `--files` 参数报错：
- 确保 JSON 格式正确（可以使用在线 JSON 验证工具）
- 在命令行中使用单引号包裹 JSON 字符串
- JSON 中的字符串必须使用双引号，不能用单引号

### 4. 会话不连续

如果多轮对话失败：
- 确保使用相同的 `--conversation-id`
- 确保使用相同的 `--user` 标识符
- 注意：Service API 创建的会话与 WebApp 创建的会话是隔离的

### 5. Vision 模型图片问题

使用 Vision 功能时：
- 确保模型支持 Vision（如 GPT-4 Vision）
- 图片 URL 必须可公开访问
- 支持的格式：`remote_url` 或 `local_file`
- 参考文件格式示例：
  ```json
  {
    "type": "image",
    "transfer_method": "remote_url",
    "url": "https://example.com/image.jpg"
  }
  ```

## 应用类型支持

这个脚本支持以下 Dify 应用类型：

- ✅ **Chat 应用**: 基础对话应用
- ✅ **Agent 应用**: 智能代理应用（仅支持流式模式）
- ❌ **Workflow 应用**: 需要使用不同的 API 端点
- ❌ **Completion 应用**: 需要使用 Completion API

## Python 代码集成示例

你可以在 Python 代码中直接使用 `DifyChatClient` 类：

```python
import asyncio
from scripts.dify_workflow_client import DifyChatClient

async def main():
    # 创建客户端
    client = DifyChatClient(
        api_key="your-api-key",
        base_url="https://api.dify.ai/v1"
    )
    
    # 发送消息（流式）
    await client.send_chat_message(
        query="你好",
        user="user-123",
        response_mode="streaming"
    )
    
    # 多轮对话
    conversation_id = "conv-abc123"
    await client.send_chat_message(
        query="第一个问题",
        user="user-123",
        conversation_id=conversation_id,
        response_mode="streaming"
    )
    
    await client.send_chat_message(
        query="继续问",
        user="user-123",
        conversation_id=conversation_id,
        response_mode="streaming"
    )
    
    # 查看会话列表
    await client.get_conversations(user="user-123")

if __name__ == "__main__":
    asyncio.run(main())
```

## 相关资源

- [Dify 官方文档](https://docs.dify.ai/)
- [Chat API 文档](https://docs.dify.ai/api-reference/chat/send-chat-message)
- [Dify GitHub](https://github.com/langgenius/dify)
- [API 认证说明](https://docs.dify.ai/api-reference/chat/send-chat-message#authorizations)

## 与其他 API 的区别

| 功能 | Chat API | Workflow API | Completion API |
|------|----------|--------------|----------------|
| 多轮对话 | ✅ | ❌ | ❌ |
| 流式输出 | ✅ | ✅ | ✅ |
| Agent 模式 | ✅ | ❌ | ❌ |
| 对话历史 | ✅ | ❌ | ❌ |
| 适用场景 | 聊天、客服 | 工作流自动化 | 文本补全 |

## 调试技巧

1. **查看完整响应**: 脚本会打印所有接收到的事件，有助于调试
2. **测试连接**: 先用简单的 "你好" 测试连接是否正常
3. **检查会话**: 使用 `--list-conversations` 查看是否成功创建会话
4. **使用流式模式**: 流式模式可以实时看到处理进度，便于调试
5. **保存日志**: 可以将输出重定向到文件：`python script.py ... > output.log 2>&1`

## 最佳实践

1. **用户标识**: 为每个真实用户使用唯一的 `user` 标识符
2. **会话管理**: 合理使用 `conversation_id` 维护对话上下文
3. **安全性**: 永远不要在客户端暴露 API 密钥
4. **超时设置**: 根据实际需求调整超时时间
5. **错误处理**: 在生产环境中添加重试逻辑
6. **流式优先**: 除非有特殊需求，优先使用流式模式获得更好的用户体验
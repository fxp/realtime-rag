# Dify Provider 使用指南

## 概述

Dify Provider 是基于 [Dify.AI](https://dify.ai) 的 RAG 服务提供商实现。Dify 是一个开源的 LLM 应用开发平台，提供强大的 RAG（检索增强生成）能力。

## 特性

- ✅ **对话式问答** - 支持多轮对话
- ✅ **流式响应** - 支持流式和阻塞两种响应模式
- ✅ **知识库检索** - 自动从知识库检索相关文档
- ✅ **会话管理** - 支持会话创建、查询、重命名、删除
- ✅ **消息历史** - 获取会话消息历史
- ✅ **建议问题** - 获取下一步建议问题
- ✅ **消息反馈** - 支持对答案进行评价反馈

## 配置

### 1. 获取 API 密钥

1. 访问 [Dify Cloud](https://cloud.dify.ai) 或自部署的 Dify 实例
2. 创建或选择一个应用
3. 在应用设置中找到 API 密钥
4. 复制 API 密钥

### 2. 配置环境变量

在 `.env` 文件中配置：

```bash
# RAG 提供商选择 Dify
RAG_PROVIDER=dify

# Dify API 配置
DIFY_API_KEY=app-xxxxxxxxxxxxxxxxxxxx
DIFY_BASE_URL=https://api.dify.ai/v1
DIFY_TIMEOUT=30.0
DIFY_USER=default-user

# 可选：固定会话ID（用于多轮对话）
# DIFY_CONVERSATION_ID=your-conversation-id
```

### 3. 自部署 Dify 配置

如果使用自部署的 Dify 实例：

```bash
RAG_PROVIDER=dify
DIFY_API_KEY=app-xxxxxxxxxxxxxxxxxxxx
DIFY_BASE_URL=https://your-dify-instance.com/v1
DIFY_TIMEOUT=30.0
DIFY_USER=default-user
```

## 使用方法

### 基本问答

启动服务后，通过 WebSocket 发送问题：

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/realtime-asr');

ws.onopen = () => {
    ws.send(JSON.stringify({
        type: 'asr_chunk',
        text: '什么是人工智能？',
        is_final: true
    }));
};

ws.onmessage = (event) => {
    const message = JSON.parse(event.data);
    console.log(message);
};
```

### 批量处理

使用 REST API 进行批量问答：

```bash
curl -X POST http://localhost:8000/api/batch/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "name": "AI知识问答",
    "texts": [
      "什么是人工智能？",
      "什么是机器学习？",
      "什么是深度学习？"
    ]
  }'
```

## API 功能

### 标准 RAG 查询

DifyProvider 实现了标准的 `BaseRAGProvider` 接口：

```python
from app.services.rag_providers import DifyProvider

# 初始化
provider = DifyProvider({
    "api_key": "app-xxxxxxxxxxxxxxxxxxxx",
    "base_url": "https://api.dify.ai/v1",
    "timeout": 30.0,
    "user": "user-123"
})

# 阻塞式查询
result = await provider.query("什么是人工智能？")
print(result.content)
print(result.metadata)
print(result.sources)

# 流式查询
async for chunk in provider.stream_query("什么是人工智能？"):
    print(chunk, end='', flush=True)
```

### 扩展功能

#### 1. 获取会话列表

```python
conversations = await provider.get_conversations(limit=20)
for conv in conversations['data']:
    print(f"会话ID: {conv['id']}, 名称: {conv['name']}")
```

#### 2. 获取会话消息历史

```python
messages = await provider.get_conversation_messages(
    conversation_id="conv-xxxx",
    limit=20
)
for msg in messages['data']:
    print(f"问题: {msg['query']}")
    print(f"答案: {msg['answer']}")
```

#### 3. 重命名会话

```python
result = await provider.rename_conversation(
    conversation_id="conv-xxxx",
    name="AI基础知识讨论"
)
```

#### 4. 删除会话

```python
success = await provider.delete_conversation("conv-xxxx")
```

#### 5. 获取建议问题

```python
suggestions = await provider.get_suggested_questions("msg-xxxx")
for question in suggestions['data']:
    print(question)
```

#### 6. 停止消息生成

```python
success = await provider.stop_message("task-xxxx")
```

#### 7. 发送消息反馈

```python
# 点赞
success = await provider.send_feedback(
    message_id="msg-xxxx",
    rating="like"
)

# 点踩并提供反馈
success = await provider.send_feedback(
    message_id="msg-xxxx",
    rating="dislike",
    content="答案不够准确"
)
```

## 响应格式

### 查询结果

```python
QueryResult(
    content="人工智能是计算机科学的一个分支...",
    metadata={
        "provider": "DifyProvider",
        "conversation_id": "conv-xxxx",
        "message_id": "msg-xxxx",
        "created_at": 1234567890,
        "mode": "chat"
    },
    sources=[
        {
            "title": "文档名称",
            "content": "文档内容片段",
            "score": 0.95,
            "position": 1
        }
    ],
    usage={
        "tokens": 150,
        "prompt_tokens": 50,
        "completion_tokens": 100
    }
)
```

### 流式响应

流式查询会实时返回答案片段，直到完整答案生成完毕。

## 高级配置

### 多轮对话

要实现多轮对话，需要保持 `conversation_id`：

```python
# 第一次查询
result1 = await provider.query("什么是人工智能？")
conversation_id = result1.metadata['conversation_id']

# 第二次查询，使用相同的conversation_id
result2 = await provider.query(
    "它有哪些应用领域？",
    conversation_id=conversation_id
)
```

### 自定义用户标识

```python
result = await provider.query(
    "什么是人工智能？",
    user="user-123"
)
```

### 传递额外输入

如果 Dify 应用定义了额外的输入变量：

```python
result = await provider.query(
    "推荐相关文档",
    inputs={
        "category": "技术",
        "level": "入门"
    }
)
```

## 错误处理

DifyProvider 会捕获并转换所有 HTTP 错误为友好的错误消息：

```python
try:
    result = await provider.query("问题")
except Exception as e:
    print(f"查询失败: {e}")
    # 输出: "Dify查询失败: API key is invalid"
```

## 性能优化

### 1. 超时设置

根据应用复杂度调整超时时间：

```bash
DIFY_TIMEOUT=60.0  # 复杂应用可能需要更长时间
```

### 2. 使用流式响应

对于长答案，使用流式响应可以提升用户体验：

```python
async for chunk in provider.stream_query(question):
    # 实时显示答案片段
    print(chunk, end='', flush=True)
```

### 3. 会话管理

定期清理不需要的会话以节省资源：

```python
# 获取所有会话
conversations = await provider.get_conversations(limit=100)

# 删除旧会话
for conv in conversations['data']:
    if should_delete(conv):
        await provider.delete_conversation(conv['id'])
```

## 故障排查

### 1. API 密钥错误

**错误**: `Dify查询失败: API key is invalid`

**解决**:
- 检查 `DIFY_API_KEY` 是否正确
- 确认 API 密钥以 `app-` 开头
- 验证密钥是否已激活

### 2. 连接超时

**错误**: `Dify查询失败: Connection timeout`

**解决**:
- 增加 `DIFY_TIMEOUT` 值
- 检查网络连接
- 验证 `DIFY_BASE_URL` 是否正确

### 3. 会话不存在

**错误**: `conversation_id is invalid`

**解决**:
- 不要使用过期的 `conversation_id`
- 每次新对话开始时不传 `conversation_id`
- 从上次查询结果中获取最新的 `conversation_id`

### 4. 流式响应中断

**解决**:
- 确保网络连接稳定
- 增加超时时间
- 检查服务器日志

## 最佳实践

### 1. 会话管理

```python
class DifyConversationManager:
    def __init__(self, provider):
        self.provider = provider
        self.conversations = {}
    
    async def get_or_create_conversation(self, user_id):
        if user_id not in self.conversations:
            # 首次查询会自动创建会话
            result = await self.provider.query(
                "你好",
                user=user_id
            )
            self.conversations[user_id] = result.metadata['conversation_id']
        
        return self.conversations[user_id]
    
    async def query(self, user_id, question):
        conversation_id = await self.get_or_create_conversation(user_id)
        return await self.provider.query(
            question,
            user=user_id,
            conversation_id=conversation_id
        )
```

### 2. 错误重试

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
async def query_with_retry(provider, question):
    return await provider.query(question)
```

### 3. 结果缓存

```python
from functools import lru_cache
import hashlib

class CachedDifyProvider:
    def __init__(self, provider):
        self.provider = provider
        self.cache = {}
    
    def _get_cache_key(self, question):
        return hashlib.md5(question.encode()).hexdigest()
    
    async def query(self, question, use_cache=True):
        cache_key = self._get_cache_key(question)
        
        if use_cache and cache_key in self.cache:
            return self.cache[cache_key]
        
        result = await self.provider.query(question)
        self.cache[cache_key] = result
        
        return result
```

## 相关链接

- [Dify 官方文档](https://docs.dify.ai)
- [Dify API 文档](https://docs.dify.ai/api)
- [Dify GitHub](https://github.com/langgenius/dify)
- [本项目 README](../README.md)
- [API 参考文档](../spec/api-reference.md)

## 支持

如有问题，请：
1. 查看 Dify 官方文档
2. 查看项目 Issues
3. 提交新的 Issue


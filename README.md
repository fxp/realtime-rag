# Realtime RAG WebSocket Service

基于 FastAPI 的实时检索增强生成（RAG）服务，通过 WebSocket 提供流式语音识别（ASR）结果处理、智能问题检测和问答功能。系统支持实时流式处理和离线批量处理两种模式。

## 特性

- ✨ **实时 WebSocket 通信** - 低延迟的双向实时通信
- 🤖 **智能问题检测** - 自动识别用户问题，支持中英文
- 🔄 **流式答案传输** - 分块流式返回答案，提升用户体验
- 🔌 **多提供商支持** - 支持 Dify、Context Provider、OpenAI、Serper 等多种服务
- 📦 **批量处理** - 支持离线批量处理大量文本数据
- ⚙️ **灵活配置** - 基于环境变量的配置管理
- 🎯 **会话管理** - 完整的会话状态跟踪和控制
- 📊 **健康检查** - 完善的健康检查和服务状态监控

## 架构

```
realtime-rag/
├── app/
│   ├── config.py          # 配置管理
│   ├── main.py            # 应用入口
│   ├── models/            # 数据模型
│   │   ├── session.py     # 会话状态
│   │   └── batch_task.py  # 批量任务模型
│   ├── services/          # 业务服务
│   │   ├── rag_service.py # RAG 服务管理器
│   │   ├── batch_processor.py # 批量处理引擎
│   │   ├── task_queue.py  # 任务队列管理
│   │   ├── text_utils.py  # 文本处理工具
│   │   └── rag_providers/ # RAG 提供商抽象层
│   │       ├── base.py    # 基础抽象类
│   │       ├── context.py # Context 提供商
│   │       ├── openai.py  # OpenAI 提供商
│   │       ├── dify.py    # Dify 提供商
│   │       ├── serper.py  # Serper 提供商
│   │       └── custom.py  # 自定义提供商
│   └── routers/           # 路由处理
│       ├── websocket.py   # WebSocket 路由
│       └── batch.py       # 批量处理路由
├── spec/                  # 规范文档
├── requirements.txt       # 依赖管理
└── .env.example          # 配置示例
```

## 快速开始

### 1. 安装依赖

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
# 复制配置示例
cp .env.example .env

# 编辑 .env 文件，配置你的 API 密钥
# 至少需要配置一个 RAG 提供商
```

### 3. 启动服务

```bash
# 开发模式
python -m app.main

# 或使用 uvicorn
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. 验证服务

访问以下端点验证服务状态：

- **API 文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/health
- **WebSocket 端点**: ws://localhost:8000/ws/realtime-asr

## API 使用

### WebSocket 通信

#### 连接 WebSocket

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/realtime-asr');

ws.onopen = () => {
    console.log('Connected');
};

ws.onmessage = (event) => {
    const message = JSON.parse(event.data);
    console.log('Received:', message);
};
```

#### 发送 ASR 文本

```javascript
ws.send(JSON.stringify({
    type: 'asr_chunk',
    text: '什么是人工智能？',
    is_final: true
}));
```

#### 控制消息

```javascript
// 暂停
ws.send(JSON.stringify({
    type: 'control',
    action: 'pause'
}));

// 恢复
ws.send(JSON.stringify({
    type: 'control',
    action: 'resume'
}));

// 即时查询
ws.send(JSON.stringify({
    type: 'control',
    action: 'instant_query'
}));
```

### 批量处理 API

#### 提交批量任务

```bash
curl -X POST http://localhost:8000/api/batch/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "name": "批量问答任务",
    "texts": ["什么是AI?", "什么是机器学习?"],
    "options": {}
  }'
```

#### 查询任务状态

```bash
curl http://localhost:8000/api/batch/tasks/{task_id}
```

#### 获取任务结果

```bash
curl http://localhost:8000/api/batch/tasks/{task_id}/results?page=1&size=100
```

#### 取消任务

```bash
curl -X DELETE http://localhost:8000/api/batch/tasks/{task_id}
```

## 配置说明

### RAG 提供商配置

#### Context Provider

```bash
RAG_PROVIDER=context
CONTEXT_API_KEY=your_api_key
CONTEXT_BASE_URL=https://api.context.ai
CONTEXT_TIMEOUT=30.0
```

#### OpenAI

```bash
RAG_PROVIDER=openai
OPENAI_API_KEY=your_api_key
OPENAI_BASE_URL=https://api.openai.com
OPENAI_MODEL=gpt-3.5-turbo
OPENAI_TIMEOUT=30.0
```

#### Dify (推荐)

```bash
RAG_PROVIDER=dify
DIFY_API_KEY=app-xxxxxxxxxxxxxxxxxxxx
DIFY_BASE_URL=https://api.dify.ai/v1
DIFY_TIMEOUT=30.0
DIFY_USER=default-user
```

> 📖 **详细文档**: [Dify Provider 使用指南](docs/DIFY_PROVIDER.md)

#### 自定义 RAG 服务

```bash
RAG_PROVIDER=custom
CUSTOM_RAG_API_URL=https://your-api.com/query
CUSTOM_RAG_API_KEY=your_api_key
CUSTOM_RAG_TIMEOUT=30.0
```

### 搜索提供商配置

#### Serper

```bash
SEARCH_PROVIDER=serper
SERPER_API_KEY=your_api_key
SERPER_TIMEOUT=10.0
```

### 批量处理配置

```bash
BATCH_ENABLED=true
BATCH_MAX_CONCURRENT=5
BATCH_MAX_QUEUE_SIZE=1000
BATCH_STORAGE_PATH=./batch_results
```

## 消息格式

### 客户端消息

#### ASR 文本块

```json
{
  "type": "asr_chunk",
  "text": "用户说的话",
  "is_final": true,
  "timestamp": 1234567890
}
```

#### 控制消息

```json
{
  "type": "control",
  "action": "pause|resume|stop|instant_query"
}
```

### 服务器消息

#### 状态消息

```json
{
  "type": "status",
  "session_id": "xxx",
  "stage": "listening|analyzing|querying_rag|idle",
  "note": "状态说明"
}
```

#### 答案消息

```json
{
  "type": "answer",
  "session_id": "xxx",
  "stream_index": 0,
  "content": "答案内容",
  "final": false
}
```

#### 错误消息

```json
{
  "type": "error",
  "session_id": "xxx",
  "code": "ERROR_CODE",
  "message": "错误描述"
}
```

## 开发指南

### 添加新的 RAG 提供商

1. 在 `app/services/rag_providers/` 创建新文件
2. 继承 `BaseRAGProvider` 或 `BaseSearchProvider`
3. 实现必需的方法
4. 在 `app/services/rag_service.py` 中注册

示例：

```python
from app.services.rag_providers.base import BaseRAGProvider
from app.models.batch_task import QueryResult

class MyCustomProvider(BaseRAGProvider):
    async def query(self, question: str, **kwargs) -> QueryResult:
        # 实现查询逻辑
        pass
    
    async def stream_query(self, question: str, **kwargs):
        # 实现流式查询逻辑
        pass
    
    async def health_check(self) -> bool:
        # 实现健康检查
        pass
    
    @property
    def name(self) -> str:
        return "MyCustomProvider"
```

## 部署

### Docker 部署

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 生产环境建议

- 使用 HTTPS/WSS 加密传输
- 配置反向代理（Nginx）
- 启用日志记录和监控
- 使用进程管理器（systemd、supervisor）
- 配置环境变量而非硬编码

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！

## 支持

如有问题，请查看 `spec/` 目录下的详细文档或提交 Issue。

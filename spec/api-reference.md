# API 参考文档

## 概述

Realtime RAG 服务提供 REST API 和 WebSocket API 用于实时语音识别和智能问答功能。

## REST API

### 健康检查

检查服务状态和配置。

**端点**: `GET /health`

**响应**:
```json
{
  "status": "healthy",
  "version": "2.0.0",
  "dify_configured": true
}
```

**响应字段**:
- `status`: 服务状态，始终为 "healthy"
- `version`: 应用版本号
- `dify_configured`: 是否已配置 Dify API 密钥

## WebSocket API

### 连接端点

**URL**: `ws://<host>/ws/realtime-asr`

**协议**: WebSocket (JSON 消息)

### 消息格式

所有消息都是 JSON 格式，包含 `type` 字段用于消息类型识别。

#### 客户端消息

##### 1. ASR 文本块 (`asr_chunk`)

发送语音识别的文本片段。

```json
{
  "type": "asr_chunk",
  "text": "什么是人工智能？",
  "is_final": true,
  "session_id": "optional-session-id"
}
```

**字段**:
- `type`: 消息类型，固定为 "asr_chunk"
- `text`: ASR 识别的文本内容
- `is_final`: 是否为最终识别结果
- `session_id`: 可选的会话标识符

##### 2. 控制消息 (`control`)

控制会话状态和流程。

```json
{
  "type": "control",
  "action": "pause",
  "session_id": "optional-session-id"
}
```

**支持的操作**:
- `pause`: 暂停处理 ASR 文本
- `resume`: 恢复处理 ASR 文本
- `stop`: 停止会话并关闭连接
- `instant_query`: 立即查询最新的最终化 ASR 文本

##### 3. 心跳消息 (`keepalive`)

保持连接活跃。

```json
{
  "type": "keepalive",
  "session_id": "optional-session-id"
}
```

#### 服务器消息

##### 1. 确认消息 (`ack`)

确认收到客户端消息。

```json
{
  "type": "ack",
  "message": "connected",
  "session_id": "generated-session-id"
}
```

或

```json
{
  "type": "ack",
  "received_type": "asr_chunk",
  "session_id": "session-id"
}
```

##### 2. 状态消息 (`status`)

报告当前处理状态。

```json
{
  "type": "status",
  "stage": "listening",
  "session_id": "session-id"
}
```

**状态阶段**:
- `listening`: 正在监听 ASR 输入
- `paused`: 已暂停处理
- `waiting_for_question`: 等待问题输入
- `analyzing`: 正在分析问题
- `instant_query`: 执行即时查询
- `querying_rag`: 正在查询 RAG 后端
- `interrupting`: 正在中断当前查询
- `idle`: 空闲状态
- `closed`: 会话已关闭

##### 3. 答案消息 (`answer`)

流式返回 RAG 查询结果。

```json
{
  "type": "answer",
  "stream_index": 0,
  "content": "人工智能是计算机科学的一个分支...",
  "final": false,
  "session_id": "session-id"
}
```

**字段**:
- `stream_index`: 答案片段的索引
- `content`: 答案内容片段
- `final`: 是否为最后一个片段

##### 4. 错误消息 (`error`)

报告错误信息。

```json
{
  "type": "error",
  "code": "INVALID_JSON",
  "message": "Invalid JSON format",
  "session_id": "session-id"
}
```

**错误代码**:
- `INVALID_JSON`: JSON 格式错误
- `INVALID_MESSAGE`: 消息格式错误
- `UNSUPPORTED_TYPE`: 不支持的消息类型
- `UNKNOWN_ACTION`: 未知的控制操作
- `NO_FINAL_ASR`: 没有可用的最终化 ASR 文本
- `EMPTY_QUESTION`: 问题内容为空
- `SERVER_ERROR`: 服务器内部错误

## 使用示例

### 基本对话流程

1. **建立连接**
   ```
   客户端 -> 服务器: WebSocket 连接
   服务器 -> 客户端: {"type": "ack", "message": "connected", "session_id": "abc123"}
   服务器 -> 客户端: {"type": "status", "stage": "listening"}
   ```

2. **发送 ASR 文本**
   ```
   客户端 -> 服务器: {"type": "asr_chunk", "text": "什么是机器学习？", "is_final": true}
   服务器 -> 客户端: {"type": "ack", "received_type": "asr_chunk", "session_id": "abc123"}
   服务器 -> 客户端: {"type": "status", "stage": "analyzing", "question": "什么是机器学习？"}
   服务器 -> 客户端: {"type": "status", "stage": "querying_rag"}
   ```

3. **接收答案**
   ```
   服务器 -> 客户端: {"type": "answer", "stream_index": 0, "content": "机器学习是人工智能的一个分支...", "final": false}
   服务器 -> 客户端: {"type": "answer", "stream_index": 1, "content": "...它使计算机能够从数据中学习...", "final": true}
   服务器 -> 客户端: {"type": "status", "stage": "idle"}
   ```

### 控制操作示例

**暂停处理**:
```
客户端 -> 服务器: {"type": "control", "action": "pause"}
服务器 -> 客户端: {"type": "status", "stage": "paused"}
```

**即时查询**:
```
客户端 -> 服务器: {"type": "control", "action": "instant_query"}
服务器 -> 客户端: {"type": "status", "stage": "instant_query", "question": "什么是深度学习？"}
服务器 -> 客户端: {"type": "status", "stage": "querying_rag", "mode": "instant"}
```

## 错误处理

### 常见错误场景

1. **API 密钥未配置**
   ```
   服务器 -> 客户端: {"type": "answer", "content": "错误：未配置 DIFY_API_KEY"}
   ```

2. **网络超时**
   ```
   服务器 -> 客户端: {"type": "answer", "content": "调用 RAG 服务失败：请求超时"}
   ```

3. **无效消息格式**
   ```
   服务器 -> 客户端: {"type": "error", "code": "INVALID_JSON", "message": "Invalid JSON"}
   ```

## 配置参数

### 服务提供商配置

| 变量名 | 描述 | 必需 | 默认值 |
|--------|------|------|--------|
| `RAG_PROVIDER` | RAG 服务提供商 | 否 | `dify` |
| `SEARCH_PROVIDER` | 搜索服务提供商 | 否 | `serper` |

### Dify 配置

| 变量名 | 描述 | 必需 | 默认值 |
|--------|------|------|--------|
| `DIFY_API_KEY` | Dify API 密钥 | 是* | - |
| `DIFY_BASE_URL` | Dify API 基础 URL | 否 | `https://api.dify.ai/v1` |
| `DIFY_TIMEOUT` | 请求超时时间（秒） | 否 | `60.0` |

*当 `RAG_PROVIDER=dify` 时必需

### Serper 配置

| 变量名 | 描述 | 必需 | 默认值 |
|--------|------|------|--------|
| `SERPER_API_KEY` | Serper API 密钥 | 是* | - |
| `SERPER_TIMEOUT` | 请求超时时间（秒） | 否 | `30.0` |

*当 `SEARCH_PROVIDER=serper` 时必需

### 应用配置

| 配置项 | 描述 | 默认值 |
|--------|------|--------|
| `WS_PATH` | WebSocket 路径 | `/ws/realtime-asr` |
| `APP_TITLE` | 应用标题 | `Realtime RAG` |
| `APP_VERSION` | 应用版本 | `2.0.0` |

## 限制和注意事项

1. **连接限制**: 每个 WebSocket 连接维护独立的会话状态
2. **消息大小**: 建议单个消息不超过 64KB
3. **超时设置**: 默认请求超时 60 秒，可根据需要调整
4. **并发查询**: 每个会话同时只能有一个 RAG 查询
5. **文本长度**: ASR 文本建议不超过 1000 字符

## 最佳实践

1. **会话管理**: 合理使用 `session_id` 进行会话切换
2. **错误处理**: 始终监听 `error` 消息类型
3. **状态监控**: 关注 `status` 消息了解当前处理状态
4. **连接保活**: 定期发送 `keepalive` 消息保持连接
5. **优雅关闭**: 使用 `stop` 控制操作正确关闭连接

# 实时 WebSocket 通信协议

## 端点信息

- **URL**: `wss://<host>/ws/realtime-asr`
- **传输协议**: WebSocket，每条消息使用 JSON 编码
- **认证**: 传输层不处理认证，期望上游基础设施控制访问权限

## 连接生命周期

1. **连接建立** – 客户端打开 WebSocket 连接，必须准备接收初始的 `ack` 和 `status` 消息
2. **流式通信** – 客户端发送 ASR 派生载荷和可选控制命令，同时处理服务器确认和状态消息
3. **连接关闭** – 任一方都可以关闭套接字。当接受 `stop` 控制操作时，服务器通过 `status` 阶段 `closed` 宣布关闭意图

## 消息格式

所有消息都是 JSON 对象，至少包含一个 `type` 字段。其他字段取决于消息类别。

```jsonc
{
  "type": "<message-category>",
  "session_id": "<server-provided session identifier>",
  ... // type-specific fields
}
```

客户端应该回显从服务器收到的最新 `session_id`。服务器将客户端提供的新 `session_id` 视为切换到该标识符的请求。

## 客户端 → 服务器消息

| 类型        | 描述                                   | 必需字段                                           |
| ----------- | --------------------------------------------- | --------------------------------------------------------- |
| `keepalive` | 可选的心跳载荷                   | —                                                         |
| `control`   | 调整会话生命周期                | `action`: `pause`, `resume`, `stop`, `instant_query` 之一 |
| `asr_chunk` | 发送增量 ASR 输出                 | `text`: 字符串, `is_final`: 布尔值                      |

### `control` 控制消息

- `pause`: 服务器转换到 `paused` 阶段，忽略进一步的 `asr_chunk` 载荷直到恢复
- `resume`: 服务器重新进入 `listening` 阶段
- `stop`: 服务器发送 `status` 消息，阶段为 `closed`，然后终止会话循环
- `instant_query`: 立即中断任何正在进行的 RAG 响应，强制后端使用最新的最终化 ASR 文本块

### `asr_chunk` ASR 文本块消息

- `text`: 来自 ASR 的转录片段
- `is_final`: 标记该片段是否为最终化的话语。只有最终文本块会被缓冲用于问题检测

## 服务器 → 客户端消息

| 类型        | 描述                                                                 | 关键字段                                                                                           |
| ----------- | --------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| `ack`       | 确认收到消息或初始连接                        | `message` (连接时) 或 `received_type`, `session_id`                                             |
| `status`    | 通信状态机阶段                                       | `stage`: `listening`, `paused`, `waiting_for_question`, `analyzing`, `instant_query`, `querying_rag`, `interrupting`, `idle`, `closed`; 可选 `note`, `question`, `mode` |
| `answer`    | 将生成的答案流式传输回客户端                               | `stream_index`: 整数, `content`: 字符串块, `final`: 布尔值                                  |
| `error`     | 表示格式错误的输入或操作失败                           | `code`: 字符串, `message`: 人类可读的描述, 可选诊断字段                   |

## 问题检测流程

1. 客户端发送 `asr_chunk` 消息，直到带有 `is_final: true` 的消息到达
2. 服务器聚合所有最终化的文本块，通过 `SessionState.looks_like_question()` 应用启发式算法
3. 如果聚合文本不被认为是问题，服务器回复 `status` 阶段 `waiting_for_question`
4. 如果被识别为问题，服务器发送 `status` 阶段 `analyzing` 和 `querying_rag` 并将文本转发给 Dify API
5. 答案文本使用 `stream_answer` 分块，作为有序的 `answer` 消息返回
6. 结束的 `status` 阶段 `idle` 表示准备接收进一步输入

## 即时查询控制流程

当客户端在至少一个最终化 ASR 文本块已交付后发出 `{"type": "control", "action": "instant_query"}` 时，服务器执行强制查询：

1. 如果 RAG 查询已经在进行中，服务器发送 `status` 阶段 `interrupting` 并取消挂起的任务
2. 不运行 `SessionState.looks_like_question()`，服务器发送 `status` 阶段 `instant_query` 回显最后一个最终化的 ASR 文本块，然后发送 `status` 阶段 `querying_rag` 并带有 `mode: "instant"`
3. 答案块通过 `answer` 消息正常流式传输
4. 完成通过 `status` 阶段 `idle` 确认

如果没有可用的最终化 ASR 文本块，服务器使用代码 `NO_FINAL_ASR` 回复 `error` 消息。

## 错误条件

- **无效 JSON**: 服务器回复 `error` 代码 `INVALID_JSON` 并忽略载荷
- **缺失或无效字段**: 对于缺失的 `type`, `text` 或类型不当，回复 `error` 代码 `INVALID_MESSAGE`
- **不支持的类型**: 当 `type` 不被识别时，回复 `error` 代码 `UNSUPPORTED_TYPE`
- **未知控制操作**: 当 `action` 超出支持集合时，回复 `error` 代码 `UNKNOWN_ACTION`
- **无最终化 ASR**: 当在任何最终 ASR 文本块存储之前发出 `instant_query` 时，回复 `error` 代码 `NO_FINAL_ASR`
- **空问题载荷**: 当最终 ASR 文本块解析为空字符串时，回复 `error` 代码 `EMPTY_QUESTION`
- **后端失败**: 当 Dify API 失败时，服务器返回包含描述性错误字符串的 `answer`，后跟 `status` 阶段 `idle`

## 会话管理

- 初始 `ack` 传递服务器生成的权威 `session_id`
- 客户端可以通过包含不同的 `session_id` 请求会话切换；服务器将通过创建新的 `SessionState` 实例来支持
- 暂停的会话维护累积的文本但在恢复之前跳过处理新的文本块

## 时间与重试

- 如果客户端需要明确的活动保证，应该使用自己的心跳逻辑（例如，定期 `keepalive`）；服务器只是确认这些而不产生进一步的副作用
- 重连应该由客户端在传输层处理。重连后，将发出新的会话

## 安全考虑

- Dify 访问的密钥通过环境变量注入，绝不通过 WebSocket 传输
- 消费者应该在 TLS 终止后面运行服务以保护 ASR 内容

## Flow Diagram

```mermaid
flowchart TD
    connect[Client opens WebSocket to /ws/realtime-asr] --> ack[Server sends ack with session_id]
    ack --> listen_status[Server broadcasts status:listening]
    listen_status --> input_choice{Client message}
    input_choice -->|keepalive| ack_keepalive[Server ack keepalive]
    input_choice -->|control:pause| status_paused[Server status:paused]
    status_paused -->|control:resume| listen_status
    input_choice -->|control:stop| status_closed[Server status:closed then closes socket]
    input_choice -->|control:instant_query| interrupting[Server status:interrupting]
    interrupting --> instant_status[Server status:instant_query]
    instant_status --> instant_querying[Server status:querying_rag (mode: instant)]
    instant_querying --> rag_call
    input_choice -->|asr_chunk (is_final=false)| buffer_partial[Server buffers interim text]
    input_choice -->|asr_chunk (is_final=true)| check_question{Looks like question?}
    check_question -->|No| status_wait[Server status:waiting_for_question]
    status_wait --> listen_status
    check_question -->|Yes| status_analyzing[Server status:analyzing]
    status_analyzing --> status_query[Server status:querying_rag]
    status_query --> rag_call[Server sends text to RAG backend]
    rag_call --> answer_stream[Server streams answer chunks]
    answer_stream --> status_idle[Server status:idle]
    status_idle --> listen_status
```

The diagram captures the nominal streaming loop, highlighting how control commands influence the session stage and how final ASR
chunks trigger question analysis, RAG querying, and answer streaming before returning to the listening state.

# 架构文档

## 概述

Realtime RAG 是一个基于 FastAPI 的实时检索增强生成（RAG）服务，通过 WebSocket 提供流式语音识别（ASR）结果处理、问题检测和智能问答功能。系统集成了 Dify Chat API，提供低延迟的双向通信，同时保持无状态的后端架构。

## 系统目标

- 提供稳定的 WebSocket 服务，处理流式语音识别转录文本
- 智能检测用户问题并路由到检索增强生成（RAG）后端
- 以分块流式方式返回响应，提供流畅的用户体验
- 提供完善的错误处理和第三方 API 调用监控

## 架构组件图

```
┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐
│   WebSocket     │         │   FastAPI       │         │   Dify Chat     │
│   客户端        │────────>│   应用服务      │────────>│   API           │
│                 │  ASR文本 │                 │ HTTP调用 │                 │
└─────────────────┘         └─────────────────┘         └─────────────────┘
         ▲                          │                           │
         │                          │                           │
         │    流式响应               │    提取答案                │
         │    (分块)                │<──────────────────────────┤
         │                          │                           │
         │                          │  SessionState             │
         │                          │  Text Utils               │
         └──────────────────────────┘
```

## 核心组件

### FastAPI 应用 (`app/main.py`)
- 配置 FastAPI 实例，包含元数据和健康检查路由
- 启动时验证环境配置
- 注册 WebSocket 路由处理器

### WebSocket 路由 (`app/routers/websocket.py`)
- 管理 WebSocket 生命周期：连接接受、消息确认和断开处理
- 为每个客户端维护 `SessionState` 实例，累积 ASR 文本块和控制状态
- 当最终 ASR 文本形成问题时，委托给 `DifyClient` 进行问答
- 向客户端流式发送状态更新、确认消息、部分答案和错误信息

### 会话状态模型 (`app/models/session.py`)
- 表示每个连接的状态机
- 缓冲最终化的 ASR 文本并提供启发式算法判断文本是否像问题
- 提供在答案发送后重置状态的辅助方法

### RAG 服务管理器 (`app/services/rag_service.py`)
- 统一的 RAG 和搜索服务管理接口
- 支持多种服务提供商（Dify、Serper、自定义等）
- 提供统一的查询接口和健康检查机制

### RAG 提供商抽象层 (`app/services/rag_providers/`)
- **基础抽象类** (`base.py`): 定义 RAG 和搜索提供商的标准接口
- **Dify 提供商** (`dify.py`): Dify Chat API 的具体实现
- **Serper 提供商** (`serper.py`): Serper 搜索 API 的具体实现
- **自定义提供商** (`custom.py`): 自定义 RAG/搜索服务的示例实现

### 文本工具 (`app/services/text_utils.py`)
- 将长的 Dify 答案切片为可管理的块，用于流式传输给客户端

### 配置管理 (`app/config.py`)
- 统一管理环境变量和配置参数
- 提供配置验证和默认值设置

## 运行时行为

1. **连接建立**: 客户端连接到 `/ws/realtime-asr` 端点，服务器确认连接并分配会话标识符，进入 `listening` 阶段
2. **ASR 流处理**: 客户端通过 `asr_chunk` 消息流式发送 ASR 文本，最终文本块在 `SessionState` 中累积
3. **问题检测**: 当最终文本块到达且聚合文本类似问题时，路由器转换到 `analyzing`/`querying_rag` 阶段并调用 `DifyClient.query`
4. **答案流式传输**: Dify 的响应通过 `stream_answer` 分割为片段，作为 `answer` 消息发送直到完成
5. **状态重置**: 答案发送后，会话恢复到 `idle` 阶段，等待额外的最终文本块或控制消息。控制操作（`pause`, `resume`, `stop`）调整状态转换

## 配置管理

- 通过 `.env` 文件控制 API 凭据、端点基础 URL、超时时间、WebSocket 路径和元数据
- API 凭据缺失时，服务会返回明确的错误消息而不是静默失败

## 错误处理与容错

- JSON 解析错误和不受支持的消息类型会产生结构化的错误载荷
- 暂停的会话会明确确认被忽略的文本块，保持客户端 UI 同步
- Dify 请求错误会被记录并转换为文本响应，确保 WebSocket 流保持一致性

## 扩展性考虑

### 服务提供商扩展
- **RAG 提供商**: 通过实现 `BaseRAGProvider` 接口轻松添加新的 RAG 服务
- **搜索提供商**: 通过实现 `BaseSearchProvider` 接口集成新的搜索服务
- **提供商工厂**: 使用 `RAGProviderFactory` 注册和管理提供商

### 协议扩展
- 可以通过扩展 WebSocket 路由器的分发逻辑引入额外的消息类型，同时保持向后兼容性
- 支持动态切换服务提供商和配置参数

### 认证和权限
- 可以通过在接受连接时将会话 ID 与上游凭据关联来添加多租户认证
- 支持基于用户或会话的提供商选择

## 项目结构

```
realtime-rag/
├── app/                    # 应用核心代码
│   ├── config.py          # 配置管理
│   ├── main.py            # 应用入口 (25行)
│   ├── models/            # 数据模型
│   │   └── session.py     # 会话状态
│   ├── services/          # 业务服务
│   │   ├── rag_service.py # RAG 服务管理器
│   │   ├── text_utils.py  # 文本处理工具
│   │   └── rag_providers/ # RAG 提供商抽象层
│   │       ├── base.py    # 基础抽象类
│   │       ├── dify.py    # Dify 提供商
│   │       ├── serper.py  # Serper 提供商
│   │       └── custom.py  # 自定义提供商
│   └── routers/           # 路由处理
│       └── websocket.py   # WebSocket 路由
├── tests/                 # 测试代码
├── tools/                 # 工具脚本
├── spec/                  # 规范文档
└── requirements.txt       # 依赖管理
```

## 技术栈

- **Web 框架**: FastAPI 0.111.0
- **WebSocket 支持**: uvicorn[standard] 0.30.1
- **HTTP 客户端**: httpx 0.27.0
- **配置管理**: python-dotenv
- **RAG 后端**: Dify Chat API

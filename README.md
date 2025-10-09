# Realtime RAG WebSocket 服务

基于 WebSocket 的实时 RAG（检索增强生成）服务，集成 Dify Chat API。

## ✨ 特性

- 🔌 WebSocket 实时通信
- 🤖 Dify RAG 集成
- 💬 多轮对话支持
- 📊 流式响应
- 🎯 智能问题检测

## 🚀 快速开始

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 配置环境
```bash
cp .env.example .env
# 编辑 .env 文件，填入 Dify API 密钥
```

### 3. 启动服务
```bash
python run.py
# 或
python -m uvicorn app.main:app --reload
```

### 4. 测试
```bash
python tests/ws_test_client.py
```

## 📁 项目结构

```
realtime-rag/
├── app/                    # 应用核心代码 (重构后模块化)
│   ├── config.py          # 配置管理
│   ├── main.py            # 应用入口 (25行)
│   ├── models/            # 数据模型
│   │   └── session.py     # 会话状态
│   ├── services/          # 业务服务
│   │   ├── dify_client.py # Dify API 客户端
│   │   └── text_utils.py  # 文本处理工具
│   └── routers/           # 路由处理
│       └── websocket.py   # WebSocket 路由
├── tests/                 # 测试代码
│   └── ws_test_client.py  # WebSocket 测试客户端
├── tools/                 # 工具脚本
│   └── dify_cli.py        # Dify 命令行工具
├── .env.example          # 环境变量示例
├── requirements.txt      # 依赖
└── run.py               # 快速启动脚本
```

## 🎯 重构改进

- ✅ 代码模块化 (301行 -> 8个清晰模块)
- ✅ 职责分离 (配置、模型、服务、路由)
- ✅ 易于测试和维护
- ✅ 符合最佳实践

## 📚 API 端点

- `GET /health` - 健康检查
- `WS /ws/realtime-asr` - WebSocket 连接

## 📄 许可证

MIT License

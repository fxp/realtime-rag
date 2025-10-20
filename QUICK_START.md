# 快速启动指南

## 一键启动（推荐）

### Linux/Mac
```bash
./run.sh
```

该脚本会自动：
1. 检查Python环境
2. 创建虚拟环境（如果不存在）
3. 安装依赖
4. 检查配置文件
5. 启动服务

## 手动启动

### 1. 创建虚拟环境
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows
```

### 2. 安装依赖
```bash
pip install -r requirements.txt
```

### 3. 配置环境变量
```bash
cp .env.example .env
# 编辑 .env 文件，至少配置一个RAG提供商
```

### 4. 启动服务
```bash
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## 验证服务

服务启动后，访问以下地址：

- **API文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/health
- **根路径**: http://localhost:8000/

## 配置提供商

### 使用 Context Provider
```bash
# 在 .env 文件中配置
RAG_PROVIDER=context
CONTEXT_API_KEY=your_api_key_here
```

### 使用 OpenAI
```bash
# 在 .env 文件中配置
RAG_PROVIDER=openai
OPENAI_API_KEY=your_api_key_here
```

### 使用 Serper 搜索
```bash
# 在 .env 文件中配置
SEARCH_PROVIDER=serper
SERPER_API_KEY=your_api_key_here
```

## 测试 WebSocket

### 使用浏览器控制台
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/realtime-asr');

ws.onopen = () => {
    console.log('Connected');
    // 发送测试问题
    ws.send(JSON.stringify({
        type: 'asr_chunk',
        text: '什么是人工智能？',
        is_final: true
    }));
};

ws.onmessage = (event) => {
    console.log('Received:', JSON.parse(event.data));
};
```

### 使用 curl 测试健康检查
```bash
curl http://localhost:8000/health
```

### 测试批量处理
```bash
curl -X POST http://localhost:8000/api/batch/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "name": "测试任务",
    "texts": ["什么是AI?", "什么是机器学习?"]
  }'
```

## 常见问题

### Q: 启动失败，提示配置错误
A: 检查 `.env` 文件，确保至少配置了一个RAG提供商的API密钥。

### Q: WebSocket连接失败
A: 
1. 检查服务是否正在运行
2. 确认端口8000没有被占用
3. 检查防火墙设置

### Q: RAG查询失败
A:
1. 检查API密钥是否正确
2. 检查网络连接
3. 查看服务日志了解详细错误

## 停止服务

在终端中按 `Ctrl+C` 停止服务。

## 生产环境部署

参考 [README.md](README.md) 中的"部署"章节。

## 更多帮助

- 查看完整文档: [README.md](README.md)
- 查看规范文档: [spec/](spec/)
- 查看API文档: http://localhost:8000/docs


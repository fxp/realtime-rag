# Dify Chat API 快速开始

## 🚀 3 分钟快速测试

### 步骤 1: 安装依赖

```bash
pip install -r requirements.txt
```

### 步骤 2: 获取 API 密钥

1. 访问 [Dify Cloud](https://cloud.dify.ai/) 或你的自部署实例
2. 选择一个 **Chat 应用** 或 **Agent 应用**
3. 进入 **API 访问** 页面
4. 复制你的 API 密钥（格式：`app-xxxxx`）

### 步骤 3: 发送第一个消息

```bash
python scripts/dify_workflow_client.py \
  --api-key app-YOUR-KEY-HERE \
  --query "你好，请介绍一下自己"
```

**成功！** 🎉 你应该能看到 AI 的流式响应。

---

## 📚 常用命令

### 基础对话

```bash
# 流式响应（推荐）
python scripts/dify_workflow_client.py \
  --api-key YOUR_KEY \
  --query "什么是 RAG？"

# 阻塞响应
python scripts/dify_workflow_client.py \
  --api-key YOUR_KEY \
  --query "解释机器学习" \
  --blocking
```

### 多轮对话

```bash
# 第一轮
python scripts/dify_workflow_client.py \
  --api-key YOUR_KEY \
  --query "我叫张三" \
  --conversation-id conv-123

# 第二轮（会记住上下文）
python scripts/dify_workflow_client.py \
  --api-key YOUR_KEY \
  --query "我叫什么名字？" \
  --conversation-id conv-123
```

### 使用输入变量

如果你的 Dify 应用定义了输入变量：

```bash
python scripts/dify_workflow_client.py \
  --api-key YOUR_KEY \
  --query "帮我写一篇文章" \
  --inputs '{"topic": "人工智能", "length": "500字"}'
```

### 自部署实例

```bash
python scripts/dify_workflow_client.py \
  --api-key YOUR_KEY \
  --base-url http://localhost/v1 \
  --query "测试连接"
```

---

## 🧪 运行完整测试

我们提供了一个自动测试脚本：

```bash
./scripts/test_dify_chat.sh YOUR_API_KEY
```

这将运行：
1. ✅ 基本连接测试
2. ✅ 阻塞模式测试
3. ✅ 多轮对话测试
4. ✅ 会话列表测试

---

## 🔧 故障排除

### 问题 1: `401 Unauthorized`

**原因**: API 密钥无效或格式错误

**解决方案**:
- 检查 API 密钥是否正确复制
- 确保使用的是 Chat 应用的 API 密钥
- 验证密钥格式：`app-xxxxx...`

### 问题 2: `404 Not Found`

**原因**: API 端点不正确

**解决方案**:
- 确保 `--base-url` 包含 `/v1` 路径
- 云服务应该是: `https://api.dify.ai/v1`
- 自部署应该是: `http://your-domain/v1`

### 问题 3: 连接超时

**原因**: 网络问题或请求时间过长

**解决方案**:
```bash
# 增加超时时间
python scripts/dify_workflow_client.py \
  --api-key YOUR_KEY \
  --query "你的问题" \
  --timeout 120
```

### 问题 4: `ModuleNotFoundError`

**原因**: 缺少依赖

**解决方案**:
```bash
pip install -r requirements.txt
```

---

## 📖 进阶使用

查看完整文档: [README_DIFY.md](./README_DIFY.md)

包含：
- 完整 API 参数说明
- Vision 模型使用（图片输入）
- Python 代码集成示例
- 最佳实践建议
- 更多故障排除方案

---

## 💡 提示

1. **流式 vs 阻塞**: 推荐使用流式模式，用户体验更好
2. **用户标识**: 为每个真实用户使用唯一的 `--user` 参数
3. **会话 ID**: 多轮对话必须使用相同的 `--conversation-id`
4. **安全性**: 永远不要在客户端代码中硬编码 API 密钥
5. **超时设置**: Agent 应用可能需要更长的超时时间

---

## 🔗 相关链接

- [Dify 官方文档](https://docs.dify.ai/)
- [Chat API 文档](https://docs.dify.ai/api-reference/chat/send-chat-message)
- [Dify GitHub](https://github.com/langgenius/dify)

---

**祝使用愉快！** 有问题欢迎提 Issue。

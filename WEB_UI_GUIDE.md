# 实时问答网页使用指南

## 概述

这是一个基于 WebSocket 的实时问答测试网页，用户可以在网页中实时提问，系统会立即返回答案并显示。

## 功能特性

### ✨ 核心功能
- 🌐 **实时WebSocket连接** - 与后端保持持久连接，实现真正的实时通信
- 💬 **实时问答** - 输入问题后立即获得流式答案
- 📊 **状态可视化** - 实时显示系统处理状态（监听、分析、查询等）
- 🎛️ **控制面板** - 暂停、恢复、停止、即时查询等控制功能
- 📈 **统计信息** - 显示问题数、回答数等统计数据
- 🎨 **现代化UI** - 美观的渐变设计和流畅的动画效果

### 🎯 界面元素

1. **连接状态指示器**
   - 🟢 已连接 - 正常工作
   - 🟡 正在连接 - 建立连接中
   - 🔴 未连接 - 连接断开

2. **聊天区域**
   - 显示用户问题（紫色气泡）
   - 显示系统回答（白色气泡，蓝色边框）
   - 显示系统消息（黄色气泡）
   - 实时流式显示答案

3. **系统状态**
   - listening - 正在监听
   - analyzing - 正在分析问题
   - querying_rag - 正在查询知识库
   - idle - 空闲状态
   - paused - 暂停状态

4. **控制面板**
   - ⏸️ 暂停 - 暂停接收新问题
   - ▶️ 恢复 - 恢复监听状态
   - ⏹️ 停止 - 停止当前会话
   - ⚡ 即时查询 - 强制立即查询最后的问题

## 使用方法

### 1. 启动服务器

```bash
# 确保已配置环境变量（.env文件）
# 需要配置 RAG_PROVIDER 或 SEARCH_PROVIDER

# 启动服务器
./run.sh

# 或者
python -m app.main
```

服务器默认运行在 `http://localhost:8000`

### 2. 访问网页

打开浏览器，访问：

```
http://localhost:8000
```

网页会自动连接到 WebSocket 服务器。

### 3. 开始提问

1. 等待连接状态显示 "已连接" （绿色）
2. 在底部输入框输入你的问题
3. 点击 "发送 📤" 按钮或按 Enter 键
4. 观察系统状态变化和实时答案流式显示

### 4. 使用控制功能

- **暂停/恢复**：临时暂停接收新问题
- **停止**：终止当前会话，返回空闲状态
- **即时查询**：不等待问题检测，直接查询最后输入的文本

## WebSocket 协议

网页使用以下 WebSocket 协议与后端通信：

### 客户端发送的消息

```javascript
// 发送问题
{
  "type": "asr_chunk",
  "text": "什么是机器学习？",
  "is_final": true
}

// 控制命令
{
  "type": "control",
  "action": "pause|resume|stop|instant_query"
}

// 心跳
{
  "type": "keepalive"
}
```

### 服务器返回的消息

```javascript
// 确认消息
{
  "type": "ack",
  "session_id": "xxx-xxx-xxx",
  "received_type": "asr_chunk"
}

// 状态更新
{
  "type": "status",
  "stage": "listening|analyzing|querying_rag|idle|...",
  "session_id": "xxx-xxx-xxx"
}

// 答案流
{
  "type": "answer",
  "stream_index": 0,
  "content": "答案的一部分...",
  "final": false
}

// 错误消息
{
  "type": "error",
  "code": "ERROR_CODE",
  "message": "错误描述"
}
```

## 技术栈

- **前端**：原生 HTML5 + CSS3 + JavaScript (无框架依赖)
- **通信**：WebSocket API
- **后端**：FastAPI + WebSocket
- **样式**：CSS Grid + Flexbox + 渐变动画

## 浏览器兼容性

支持所有现代浏览器：
- ✅ Chrome/Edge 88+
- ✅ Firefox 85+
- ✅ Safari 14+
- ✅ Opera 74+

## 常见问题

### Q: 无法连接到服务器？
**A:** 检查以下几点：
1. 确保后端服务器正在运行
2. 检查端口 8000 是否被占用
3. 查看浏览器控制台是否有错误信息

### Q: 发送问题后没有回答？
**A:** 可能的原因：
1. 检查环境变量配置（RAG_PROVIDER 等）
2. 查看服务器日志了解错误信息
3. 确认输入的文本被识别为问题

### Q: 如何调试问题？
**A:** 
1. 打开浏览器开发者工具（F12）
2. 查看 Console 标签页的日志
3. 查看 Network → WS 标签页的 WebSocket 消息
4. 查看服务器终端的日志输出

## 自定义配置

### 修改 WebSocket 地址

编辑 `static/index.html`，找到以下行：

```javascript
const WS_URL = `ws://${window.location.hostname}:8000/ws/realtime-asr`;
```

修改为你的服务器地址和端口。

### 修改样式

所有样式都在 `<style>` 标签中，你可以自由修改：
- 颜色主题（修改 `#667eea` 和 `#764ba2`）
- 布局（修改 grid 和 flexbox 属性）
- 动画效果（修改 `@keyframes` 规则）

## 相关文档

- [WebSocket 协议规范](spec/protocols/realtime-websocket.md)
- [协议测试脚本](tests/test_websocket_protocol.py)
- [快速开始指南](QUICK_START.md)

## 开发建议

### 添加新功能

1. **语音输入**：集成 Web Speech API
2. **历史记录**：保存对话历史到 localStorage
3. **多会话**：支持切换不同的对话会话
4. **导出功能**：导出对话记录为文本或PDF
5. **主题切换**：添加深色/浅色主题切换

### 性能优化

- 使用虚拟滚动处理大量消息
- 实现消息分页加载
- 添加消息搜索功能
- 优化移动端体验

## 反馈与支持

如有问题或建议，请：
1. 查看项目文档
2. 运行协议测试：`python tests/test_websocket_protocol.py`
3. 查看服务器健康状态：`http://localhost:8000/health`

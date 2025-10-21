# WebSocket 测试套件

## 概述

这是一个完整的 WebSocket 场景测试套件，用于验证 Realtime RAG WebSocket 服务的所有功能。

## 测试场景

测试套件包含 12 个测试场景，覆盖了 spec 文档中定义的所有功能：

### 基础功能测试

1. **场景1: 连接和初始确认**
   - 测试 WebSocket 连接建立
   - 验证初始 `ack` 消息
   - 验证 `session_id` 分配
   - 验证初始 `listening` 状态

2. **场景2: 心跳消息**
   - 测试 `keepalive` 消息
   - 验证服务器确认

3. **场景3: 非最终化 ASR 文本块**
   - 测试 `is_final: false` 的 ASR 文本块
   - 验证服务器缓冲行为

### 问题检测和 RAG 功能

4. **场景4: 问题检测和 RAG 查询**
   - 测试完整的问题识别流程
   - 验证状态转换（`analyzing` → `querying_rag`）
   - 验证答案流式传输
   - 验证返回 `idle` 状态

5. **场景5: 非问题文本**
   - 测试非问题文本的处理
   - 验证 `waiting_for_question` 状态

### 控制功能

6. **场景6: 暂停和恢复**
   - 测试 `pause` 控制消息
   - 验证暂停状态下的行为
   - 测试 `resume` 控制消息
   - 验证状态恢复

7. **场景7: 即时查询**
   - 测试 `instant_query` 功能
   - 验证强制查询流程
   - 验证 `mode: instant` 标记

8. **场景8: 无最终化文本的即时查询**
   - 测试错误处理
   - 验证 `NO_FINAL_ASR` 错误代码

9. **场景9: 停止命令**
   - 测试 `stop` 控制消息
   - 验证会话终止

### 错误处理

10. **场景10: 无效消息**
    - 测试无效 JSON 处理
    - 验证 `INVALID_JSON` 错误代码

11. **场景11: 不支持的消息类型**
    - 测试未知消息类型处理
    - 验证 `UNSUPPORTED_TYPE` 错误代码

### 高级功能

12. **场景12: 多轮对话**
    - 测试连续多个问题
    - 验证会话状态保持
    - 验证多次查询流程

## 安装依赖

### 方式1: 使用 pip

```bash
# 安装测试依赖
pip install -r requirements-test.txt
```

### 方式2: 单独安装

```bash
pip install websockets colorama
```

## 运行测试

### 1. 启动服务器

首先确保 WebSocket 服务器正在运行：

```bash
# 方式1: 使用启动脚本
./run.sh

# 方式2: 直接运行
python -m uvicorn app.main:app --reload
```

### 2. 运行测试套件

在另一个终端中运行测试：

```bash
# 运行完整测试套件
python tests/test_websocket_scenarios.py

# 或使用 pytest
pytest tests/test_websocket_scenarios.py -v

# 或直接执行
./tests/test_websocket_scenarios.py
```

## 配置

### 修改 WebSocket URL

如果服务器运行在不同的地址或端口，可以修改测试脚本中的配置：

```python
# 在 test_websocket_scenarios.py 中修改
WS_URL = "ws://localhost:8000/ws/realtime-asr"  # 修改为你的地址
TIMEOUT = 30  # 修改超时时间
```

### 环境变量配置

也可以通过环境变量配置：

```bash
export WS_TEST_URL="ws://your-server:8000/ws/realtime-asr"
export WS_TEST_TIMEOUT=60
python tests/test_websocket_scenarios.py
```

## 测试输出

### 正常输出

测试运行时会显示彩色输出，包括：

- 🟢 绿色: 成功的操作
- 🔵 蓝色: 发送的消息
- 🟡 黄色: 接收的消息
- 🔴 红色: 错误或失败

示例输出：

```
============================================================
测试: 场景4: 问题检测和 RAG 查询
============================================================
✓ 连接成功: ws://localhost:8000/ws/realtime-asr
→ 发送: {"type": "asr_chunk", "text": "什么是人工智能？", "is_final": true}
← 接收: {"type": "ack", "received_type": "asr_chunk", "session_id": "..."}
← 接收: {"type": "status", "stage": "analyzing", "session_id": "..."}
← 接收: {"type": "status", "stage": "querying_rag", "session_id": "..."}
← 接收: {"type": "answer", "content": "人工智能是...", "final": false}
...
✓ 测试通过 (5.23秒)
```

### 测试摘要

测试完成后会显示摘要：

```
============================================================
测试摘要
============================================================

✓ 场景1: 连接和初始确认: 测试通过 (0.15秒)
✓ 场景2: 心跳消息: 测试通过 (0.12秒)
✓ 场景3: 非最终化 ASR 文本块: 测试通过 (0.10秒)
✓ 场景4: 问题检测和 RAG 查询: 测试通过 (5.23秒)
...

总计: 12 个测试
通过: 12
失败: 0
耗时: 35.67秒

============================================================
所有测试通过! 🎉
============================================================
```

## 故障排查

### 连接失败

**错误**: `✗ 连接失败: [Errno 111] Connection refused`

**解决**:
1. 确认服务器正在运行
2. 检查端口是否正确（默认 8000）
3. 检查防火墙设置

### 测试超时

**错误**: `✗ 接收超时`

**解决**:
1. 检查服务器是否配置了 RAG 提供商
2. 确认 API 密钥配置正确
3. 增加超时时间（修改 `TIMEOUT` 变量）

### RAG 查询失败

**错误**: 测试场景4失败

**解决**:
1. 检查 `.env` 文件配置
2. 验证 RAG 提供商 API 密钥
3. 查看服务器日志了解详细错误

### 导入错误

**错误**: `ModuleNotFoundError: No module named 'websockets'`

**解决**:
```bash
pip install -r requirements-test.txt
```

## 自定义测试

### 添加新的测试场景

```python
async def test_my_custom_scenario():
    """自定义测试场景"""
    client = WebSocketTestClient()
    
    # 1. 连接
    if not await client.connect():
        return False
    
    # 2. 跳过初始消息
    await client.wait_for_message_type("ack")
    await client.wait_for_status("listening")
    
    # 3. 执行你的测试逻辑
    await client.send_message({
        "type": "asr_chunk",
        "text": "你的测试文本",
        "is_final": True
    })
    
    # 4. 验证结果
    # ...
    
    # 5. 断开连接
    await client.disconnect()
    return True

# 在 main() 函数中添加
await tester.run_test("自定义场景", test_my_custom_scenario)
```

### 查看消息日志

在测试函数中调用 `client.print_message_log()` 可以查看完整的消息交互历史。

## 持续集成

### GitHub Actions

```yaml
name: WebSocket Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-test.txt
      - name: Start server
        run: |
          python -m uvicorn app.main:app &
          sleep 5
      - name: Run tests
        run: python tests/test_websocket_scenarios.py
```

## 性能基准

### 预期性能指标

- 连接建立: < 100ms
- 心跳响应: < 50ms
- 问题检测: < 50ms
- RAG 查询: 2-5秒（取决于提供商）
- 答案流式传输: < 100ms/块

### 监控性能

测试结果会显示每个场景的执行时间，可以用于监控性能变化。

## 贡献

欢迎贡献新的测试场景！请确保：

1. 测试场景有清晰的描述
2. 包含完整的验证逻辑
3. 正确处理错误情况
4. 遵循现有的代码风格

## 相关文档

- [WebSocket 协议规范](../spec/protocols/realtime-websocket.md)
- [API 参考文档](../spec/api-reference.md)
- [项目 README](../README.md)

## 许可证

MIT License



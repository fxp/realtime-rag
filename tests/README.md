# 测试脚本使用指南

## 概述

本目录包含 WebSocket 协议测试脚本，支持灵活的配置选项，可以测试不同主机、端口和路径的服务器。

## 快速开始

### 1. 基本测试（使用默认配置）
```bash
./run_protocol_tests.sh
```

### 2. 测试远程服务器
```bash
./run_protocol_tests.sh --host 192.168.1.100 --port 9000
```

### 3. 使用环境变量
```bash
TEST_HOST=192.168.1.100 TEST_PORT=9000 ./run_protocol_tests.sh
```

## 配置选项

### 命令行参数

| 参数 | 说明 | 默认值 | 示例 |
|------|------|--------|------|
| `--host` | 服务器主机地址 | localhost | `--host 192.168.1.100` |
| `--port` | 服务器端口 | 8000 | `--port 9000` |
| `--timeout` | 测试超时时间（秒） | 30 | `--timeout 60` |
| `--path` | WebSocket 路径 | /ws/realtime-asr | `--path /ws/custom` |
| `--help` | 显示帮助信息 | - | `--help` |

### 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `TEST_HOST` | 默认主机地址 | localhost |
| `TEST_PORT` | 默认端口 | 8000 |
| `TEST_TIMEOUT` | 默认超时时间 | 30 |

## 使用示例

### 1. 测试本地开发服务器
```bash
# 默认配置
./run_protocol_tests.sh

# 指定端口
./run_protocol_tests.sh --port 8001
```

### 2. 测试远程服务器
```bash
# 测试远程API服务器
./run_protocol_tests.sh --host api.example.com --port 443

# 测试内网服务器
./run_protocol_tests.sh --host 192.168.1.100 --port 8080
```

### 3. 测试Docker容器
```bash
# 测试Docker容器中的服务
./run_protocol_tests.sh --host localhost --port 8080
```

### 4. 长时间测试
```bash
# 增加超时时间
./run_protocol_tests.sh --timeout 120
```

### 5. 自定义WebSocket路径
```bash
# 测试不同的WebSocket路径
./run_protocol_tests.sh --path /ws/custom-asr
```

## 直接使用Python脚本

```bash
# 基本用法
python3 tests/test_websocket_protocol.py

# 指定配置
python3 tests/test_websocket_protocol.py --host 192.168.1.100 --port 9000

# 查看帮助
python3 tests/test_websocket_protocol.py --help
```

## 配置文件

创建 `.env.test` 文件来设置默认配置：

```bash
# .env.test
TEST_HOST=192.168.1.100
TEST_PORT=9000
TEST_TIMEOUT=60
```

然后运行：
```bash
source .env.test
./run_protocol_tests.sh
```

## 故障排除

### 连接失败
1. 检查服务器是否运行
2. 验证主机和端口是否正确
3. 检查防火墙设置
4. 确认网络连接

### 超时问题
1. 增加超时时间：`--timeout 120`
2. 检查网络延迟
3. 验证服务器响应时间

### 路径错误
1. 确认WebSocket路径正确
2. 检查服务器路由配置
3. 验证路径是否可访问

## 测试结果

测试脚本会显示详细的测试结果，包括：
- 连接状态
- 消息格式验证
- 协议合规性检查
- 错误处理测试
- 性能指标

## 支持的协议特性

- ✅ 连接生命周期管理
- ✅ 心跳消息处理
- ✅ ASR 文本块处理
- ✅ 问题检测和RAG查询
- ✅ 控制命令（暂停、恢复、停止、即时查询）
- ✅ 错误处理
- ✅ 多轮对话
- ✅ 会话管理
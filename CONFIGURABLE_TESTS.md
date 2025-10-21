# 可配置测试脚本更新

## 更新概述

已成功为 WebSocket 协议测试脚本添加了灵活的配置功能，支持通过命令行参数、环境变量等方式指定测试目标。

## 主要改进

### 1. 支持的命令行参数

- `--host HOST` - 指定测试服务器主机地址
- `--port PORT` - 指定测试服务器端口
- `--timeout SECONDS` - 指定测试超时时间
- `--path PATH` - 指定 WebSocket 路径
- `--help` - 显示帮助信息

### 2. 支持的环境变量

- `TEST_HOST` - 默认主机地址
- `TEST_PORT` - 默认端口
- `TEST_TIMEOUT` - 默认超时时间

### 3. 增强的测试脚本

- `run_protocol_tests.sh` - 支持参数传递的测试运行脚本
- `test_websocket_protocol.py` - 支持配置的 Python 测试脚本

## 使用示例

### 基本用法
```bash
# 使用默认配置
./run_protocol_tests.sh

# 指定主机和端口
./run_protocol_tests.sh --host 192.168.1.100 --port 9000

# 使用环境变量
TEST_HOST=192.168.1.100 TEST_PORT=9000 ./run_protocol_tests.sh
```

### 高级用法
```bash
# 完整配置
./run_protocol_tests.sh \
  --host api.example.com \
  --port 443 \
  --timeout 120 \
  --path /ws/realtime-asr

# 直接使用 Python 脚本
python3 tests/test_websocket_protocol.py --host 192.168.1.100 --port 9000
```

## 新增文件

1. **tests/README.md** - 详细的使用指南
2. **tests/test_config_examples.md** - 配置示例文档
3. **tests/test_config.py** - 配置功能验证脚本

## 兼容性

- ✅ 向后兼容 - 默认配置保持不变
- ✅ 环境变量支持 - 可通过环境变量设置默认值
- ✅ 命令行参数 - 支持运行时指定配置
- ✅ 帮助信息 - 提供完整的使用说明

## 测试验证

配置功能已通过测试验证：
- ✅ 默认配置正确
- ✅ 环境变量支持
- ✅ 命令行参数解析
- ✅ 帮助信息显示
- ✅ URL 构建正确

## 使用场景

1. **本地开发** - 测试本地开发服务器
2. **远程测试** - 测试远程 API 服务器
3. **Docker 测试** - 测试容器化服务
4. **CI/CD 集成** - 自动化测试流程
5. **多环境测试** - 测试不同环境的服务

## 下一步

- 可以考虑添加更多配置选项（如认证信息）
- 支持配置文件（JSON/YAML）
- 添加测试报告生成功能
- 支持并行测试多个服务器

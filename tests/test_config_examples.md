# 测试配置示例

## 基本用法

### 1. 使用默认配置
```bash
./run_protocol_tests.sh
```

### 2. 指定主机和端口
```bash
./run_protocol_tests.sh --host 192.168.1.100 --port 9000
```

### 3. 使用环境变量
```bash
TEST_HOST=192.168.1.100 TEST_PORT=9000 ./run_protocol_tests.sh
```

### 4. 直接运行Python脚本
```bash
python3 tests/test_websocket_protocol.py --host 192.168.1.100 --port 9000
```

## 高级配置

### 1. 自定义超时时间
```bash
./run_protocol_tests.sh --timeout 60
```

### 2. 自定义WebSocket路径
```bash
./run_protocol_tests.sh --path /ws/custom-asr
```

### 3. 完整配置示例
```bash
./run_protocol_tests.sh \
  --host 192.168.1.100 \
  --port 9000 \
  --timeout 60 \
  --path /ws/realtime-asr
```

## 环境变量配置

创建 `.env.test` 文件：
```bash
# 测试配置
TEST_HOST=192.168.1.100
TEST_PORT=9000
TEST_TIMEOUT=60
```

然后运行：
```bash
source .env.test
./run_protocol_tests.sh
```

## 远程测试

### 测试远程服务器
```bash
./run_protocol_tests.sh --host api.example.com --port 443
```

### 测试Docker容器
```bash
./run_protocol_tests.sh --host localhost --port 8080
```

## 帮助信息

查看所有可用选项：
```bash
./run_protocol_tests.sh --help
```

## 故障排除

### 1. 连接失败
- 检查服务器是否运行
- 验证主机和端口是否正确
- 检查防火墙设置

### 2. 超时问题
- 增加超时时间：`--timeout 120`
- 检查网络连接
- 验证服务器响应时间

### 3. 路径错误
- 确认WebSocket路径正确
- 检查服务器路由配置

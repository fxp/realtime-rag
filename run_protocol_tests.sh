#!/bin/bash
# WebSocket 协议测试运行脚本

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}WebSocket 协议测试${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# 显示使用帮助
show_help() {
    echo -e "${BLUE}用法: $0 [选项]${NC}"
    echo ""
    echo -e "${BLUE}选项:${NC}"
    echo "  --host HOST        测试服务器主机地址 (默认: localhost)"
    echo "  --port PORT        测试服务器端口 (默认: 8000)"
    echo "  --timeout SECONDS  测试超时时间（秒）(默认: 30)"
    echo "  --path PATH        WebSocket 路径 (默认: /ws/realtime-asr)"
    echo "  -h, --help         显示此帮助信息"
    echo ""
    echo -e "${BLUE}环境变量:${NC}"
    echo "  TEST_HOST          默认主机地址"
    echo "  TEST_PORT          默认端口"
    echo "  TEST_TIMEOUT       默认超时时间"
    echo ""
    echo -e "${BLUE}示例:${NC}"
    echo "  $0                                    # 使用默认配置"
    echo "  $0 --host 192.168.1.100 --port 9000  # 指定主机和端口"
    echo "  TEST_HOST=192.168.1.100 $0           # 使用环境变量"
}

# 解析命令行参数
TEST_ARGS=""
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        --host)
            TEST_ARGS="$TEST_ARGS --host $2"
            shift 2
            ;;
        --port)
            TEST_ARGS="$TEST_ARGS --port $2"
            shift 2
            ;;
        --timeout)
            TEST_ARGS="$TEST_ARGS --timeout $2"
            shift 2
            ;;
        --path)
            TEST_ARGS="$TEST_ARGS --path $2"
            shift 2
            ;;
        *)
            echo -e "${RED}未知参数: $1${NC}"
            echo "使用 $0 --help 查看帮助信息"
            exit 1
            ;;
    esac
done

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}错误: 未找到 Python3${NC}"
    exit 1
fi

echo -e "${GREEN}✓${NC} Python 版本: $(python3 --version)"

# 检查测试依赖
echo -e "${YELLOW}→${NC} 检查测试依赖..."
python3 -c "import websockets, colorama" 2>/dev/null
if [ $? -ne 0 ]; then
    echo -e "${YELLOW}! 测试依赖未安装，正在安装...${NC}"
    pip install -r requirements-test.txt
    if [ $? -ne 0 ]; then
        echo -e "${RED}✗ 依赖安装失败${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓${NC} 依赖安装完成"
else
    echo -e "${GREEN}✓${NC} 测试依赖已安装"
fi

# 显示当前配置
echo -e "${BLUE}当前测试配置:${NC}"
echo -e "${BLUE}  主机: ${TEST_HOST:-localhost}${NC}"
echo -e "${BLUE}  端口: ${TEST_PORT:-8000}${NC}"
echo -e "${BLUE}  超时: ${TEST_TIMEOUT:-30}秒${NC}"
echo ""

# 检查服务器是否运行
echo -e "${YELLOW}→${NC} 检查服务器状态..."
HOST=${TEST_HOST:-localhost}
PORT=${TEST_PORT:-8000}
python3 -c "
import asyncio
import websockets
import sys

async def check():
    try:
        async with websockets.connect(f'ws://$HOST:$PORT/ws/realtime-asr', timeout=3):
            return True
    except:
        return False

result = asyncio.run(check())
exit(0 if result else 1)
" 2>/dev/null

if [ $? -ne 0 ]; then
    echo -e "${RED}✗ WebSocket 服务器未运行${NC}"
    echo -e "${YELLOW}! 请先启动服务器: ./run.sh${NC}"
    echo -e "${YELLOW}! 或检查服务器是否在 $HOST:$PORT 上运行${NC}"
    exit 1
fi

echo -e "${GREEN}✓${NC} 服务器运行正常"
echo ""

# 运行协议测试
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}开始运行协议测试...${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

python3 tests/test_websocket_protocol.py $TEST_ARGS

# 检查测试结果
if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}协议测试完成! ✓${NC}"
    echo -e "${GREEN}========================================${NC}"
    exit 0
else
    echo ""
    echo -e "${RED}========================================${NC}"
    echo -e "${RED}协议测试失败! ✗${NC}"
    echo -e "${RED}========================================${NC}"
    exit 1
fi

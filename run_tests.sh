#!/bin/bash
# WebSocket 测试运行脚本

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}WebSocket 场景测试${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

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

# 检查服务器是否运行
echo -e "${YELLOW}→${NC} 检查服务器状态..."
python3 -c "
import asyncio
import websockets

async def check():
    try:
        async with websockets.connect('ws://localhost:8000/ws/realtime-asr', timeout=3):
            return True
    except:
        return False

result = asyncio.run(check())
exit(0 if result else 1)
" 2>/dev/null

if [ $? -ne 0 ]; then
    echo -e "${RED}✗ WebSocket 服务器未运行${NC}"
    echo -e "${YELLOW}! 请先启动服务器: ./run.sh${NC}"
    exit 1
fi

echo -e "${GREEN}✓${NC} 服务器运行正常"
echo ""

# 运行测试
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}开始运行测试...${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

python3 tests/test_websocket_scenarios.py

# 检查测试结果
if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}测试完成! ✓${NC}"
    echo -e "${GREEN}========================================${NC}"
    exit 0
else
    echo ""
    echo -e "${RED}========================================${NC}"
    echo -e "${RED}测试失败! ✗${NC}"
    echo -e "${RED}========================================${NC}"
    exit 1
fi



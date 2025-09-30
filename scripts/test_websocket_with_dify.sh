#!/bin/bash
# WebSocket + Dify RAG 集成测试脚本
# 用法: ./scripts/test_websocket_with_dify.sh YOUR_DIFY_API_KEY

set -e

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

API_KEY="${1:-}"

if [ -z "$API_KEY" ]; then
    echo -e "${YELLOW}用法: $0 YOUR_DIFY_API_KEY${NC}"
    echo ""
    echo "示例: $0 app-abc123xyz"
    echo ""
    echo "这将启动 WebSocket 服务并运行测试客户端"
    exit 1
fi

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}WebSocket + Dify RAG 集成测试${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 设置环境变量
export DIFY_API_KEY="$API_KEY"
export DIFY_BASE_URL="${DIFY_BASE_URL:-https://api.dify.ai/v1}"
export DIFY_TIMEOUT="${DIFY_TIMEOUT:-60.0}"

echo -e "${GREEN}步骤 1: 检查依赖${NC}"
if ! python -c "import fastapi, uvicorn, httpx, websockets" 2>/dev/null; then
    echo -e "${RED}错误: 缺少依赖。请运行: pip install -r requirements.txt${NC}"
    exit 1
fi
echo -e "${GREEN}✓ 依赖检查通过${NC}"
echo ""

echo -e "${GREEN}步骤 2: 启动 WebSocket 服务端（后台）${NC}"
echo "API Key: ${API_KEY:0:10}..."
echo "Base URL: $DIFY_BASE_URL"
echo ""

# 启动服务端（后台运行）
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 > /tmp/realtime-rag-server.log 2>&1 &
SERVER_PID=$!

# 等待服务启动
echo "等待服务启动..."
sleep 3

# 检查服务是否启动成功
if ! ps -p $SERVER_PID > /dev/null; then
    echo -e "${RED}错误: 服务启动失败${NC}"
    cat /tmp/realtime-rag-server.log
    exit 1
fi

echo -e "${GREEN}✓ 服务已启动 (PID: $SERVER_PID)${NC}"
echo ""

# 定义清理函数
cleanup() {
    echo ""
    echo -e "${YELLOW}清理中...${NC}"
    if ps -p $SERVER_PID > /dev/null; then
        kill $SERVER_PID 2>/dev/null || true
        wait $SERVER_PID 2>/dev/null || true
    fi
    echo -e "${GREEN}✓ 服务已停止${NC}"
}

# 设置退出时清理
trap cleanup EXIT INT TERM

echo -e "${GREEN}步骤 3: 运行 WebSocket 测试客户端${NC}"
echo "发送测试问题到服务端..."
echo ""
echo -e "${BLUE}----------------------------------------${NC}"

# 运行测试客户端
if python scripts/ws_client.py --uri ws://127.0.0.1:8000/ws/realtime-asr; then
    echo -e "${BLUE}----------------------------------------${NC}"
    echo ""
    echo -e "${GREEN}✓ 测试完成${NC}"
else
    echo -e "${BLUE}----------------------------------------${NC}"
    echo ""
    echo -e "${RED}✗ 测试失败${NC}"
    echo ""
    echo "查看服务端日志:"
    cat /tmp/realtime-rag-server.log
    exit 1
fi

echo ""
echo -e "${GREEN}步骤 4: 查看服务端日志${NC}"
echo ""
tail -20 /tmp/realtime-rag-server.log

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}测试完成！${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo "提示:"
echo "  - 服务端日志: /tmp/realtime-rag-server.log"
echo "  - 查看完整日志: cat /tmp/realtime-rag-server.log"
echo ""

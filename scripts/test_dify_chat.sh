#!/bin/bash
# Dify Chat API 快速测试脚本
# 用法: ./scripts/test_dify_chat.sh YOUR_API_KEY

set -e

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

API_KEY="${1:-}"

if [ -z "$API_KEY" ]; then
    echo -e "${YELLOW}用法: $0 YOUR_API_KEY${NC}"
    echo "示例: $0 app-abc123xyz"
    exit 1
fi

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Dify Chat API 测试${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 测试 1: 基本连接测试
echo -e "${GREEN}测试 1: 基本连接（流式模式）${NC}"
python scripts/dify_workflow_client.py \
    --api-key "$API_KEY" \
    --query "你好"

echo ""
echo -e "${GREEN}✓ 测试 1 完成${NC}"
echo ""

# 测试 2: 阻塞模式
echo -e "${GREEN}测试 2: 阻塞模式${NC}"
python scripts/dify_workflow_client.py \
    --api-key "$API_KEY" \
    --query "什么是AI？" \
    --blocking

echo ""
echo -e "${GREEN}✓ 测试 2 完成${NC}"
echo ""

# 测试 3: 多轮对话
echo -e "${GREEN}测试 3: 多轮对话${NC}"
CONV_ID="test-conversation-$(date +%s)"

echo "第一轮对话..."
python scripts/dify_workflow_client.py \
    --api-key "$API_KEY" \
    --query "我的名字是小明" \
    --conversation-id "$CONV_ID"

echo ""
echo "第二轮对话（应该记得名字）..."
python scripts/dify_workflow_client.py \
    --api-key "$API_KEY" \
    --query "你还记得我的名字吗？" \
    --conversation-id "$CONV_ID"

echo ""
echo -e "${GREEN}✓ 测试 3 完成${NC}"
echo ""

# 测试 4: 列出会话
echo -e "${GREEN}测试 4: 列出会话历史${NC}"
python scripts/dify_workflow_client.py \
    --api-key "$API_KEY" \
    --list-conversations

echo ""
echo -e "${GREEN}✓ 测试 4 完成${NC}"
echo ""

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}所有测试完成！${NC}"
echo -e "${BLUE}========================================${NC}"

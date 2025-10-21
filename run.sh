#!/bin/bash
# Realtime RAG WebSocket Service 启动脚本

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Realtime RAG WebSocket Service${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# 检查Python版本
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}错误: 未找到Python3${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo -e "${GREEN}✓${NC} Python版本: $PYTHON_VERSION"

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}! 虚拟环境不存在，正在创建...${NC}"
    python3 -m venv venv
    echo -e "${GREEN}✓${NC} 虚拟环境创建成功"
fi

# 激活虚拟环境
echo -e "${YELLOW}→${NC} 激活虚拟环境..."
source venv/bin/activate

# 安装依赖
if [ ! -f "venv/.installed" ]; then
    echo -e "${YELLOW}→${NC} 安装依赖..."
    pip install --upgrade pip
    pip install -r requirements.txt
    touch venv/.installed
    echo -e "${GREEN}✓${NC} 依赖安装完成"
else
    echo -e "${GREEN}✓${NC} 依赖已安装"
fi

# 检查配置文件
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}! 配置文件不存在${NC}"
    echo -e "${YELLOW}→${NC} 从 .env.example 创建 .env 文件..."
    cp .env.example .env
    echo -e "${YELLOW}! 请编辑 .env 文件配置API密钥${NC}"
    echo -e "${YELLOW}! 按Enter继续或Ctrl+C退出编辑配置...${NC}"
    read
fi

# 启动服务
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}启动服务...${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 如果服务退出
echo ""
echo -e "${YELLOW}服务已停止${NC}"


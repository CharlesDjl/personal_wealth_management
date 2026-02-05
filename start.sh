#!/bin/bash

# 一键启动脚本 - 同时启动前端和后端

set -e

# 颜色输出
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}==================================${NC}"
echo -e "${BLUE} 个人财富管理系统 - 启动中...${NC}"
echo -e "${BLUE}==================================${NC}"

# 清理函数
cleanup() {
    echo -e "\n${YELLOW}正在停止所有服务...${NC}"
    jobs -p | xargs -r kill 2>/dev/null || true
    exit 0
}

trap cleanup SIGINT SIGTERM

# 检查 Python 和 node 是否存在
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}错误: 未找到 python3${NC}"
    exit 1
fi

if ! command -v npm &> /dev/null; then
    echo -e "${RED}错误: 未找到 npm${NC}"
    exit 1
fi

# 创建日志目录
mkdir -p logs

# 启动后端
echo -e "\n${GREEN}[1/2] 启动后端 (FastAPI)...${NC}"
# 检查是否需要安装依赖
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}创建 Python 虚拟环境...${NC}"
    python3 -m venv venv
fi

source venv/bin/activate

if ! pip show fastapi &> /dev/null; then
    echo -e "${YELLOW}安装 Python 依赖...${NC}"
    pip install -r requirements.txt
fi

# 启动后端（后台运行）
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000 > logs/backend.log 2>&1 &
BACKEND_PID=$!
echo -e "${GREEN}✓ 后端已启动 (PID: $BACKEND_PID)${NC}"

# 等待后端启动
echo -e "${YELLOW}等待后端就绪...${NC}"
for i in {1..30}; do
    if curl -s http://127.0.0.1:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ 后端就绪${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "${RED}后端启动超时，请检查 logs/backend.log${NC}"
        tail -20 logs/backend.log
        exit 1
    fi
    sleep 0.5
done

# 启动前端
echo -e "\n${GREEN}[2/2] 启动前端 (Vite)...${NC}"
# 检查 node_modules
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}安装前端依赖...${NC}"
    npm install
fi

# 启动前端（前台运行，保持输出可见）
echo -e "${GREEN}✓ 前端启动中...${NC}"
echo -e "${GREEN}==================================${NC}"
echo -e "${GREEN} 后端: http://127.0.0.1:8000${NC}"
echo -e "${GREEN} 前端: http://localhost:5173${NC}"
echo -e "${GREEN} 后端日志: logs/backend.log${NC}"
echo -e "${BLUE}==================================${NC}"
echo -e "${YELLOW}按 Ctrl+C 停止所有服务${NC}\n"

npm run dev

# 如果前端退出，也停止后端
cleanup

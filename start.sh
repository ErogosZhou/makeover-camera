#!/bin/bash

# 换装相机 启动脚本

echo "🏠 换装相机 - AI家装轻改造助手"
echo "================================"

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "❌ 未找到 Python3，请先安装"
    exit 1
fi

# 进入backend目录
cd "$(dirname "$0")/backend"

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "📦 创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
echo "📦 安装依赖..."
pip install -r requirements.txt -q

# 创建uploads目录
mkdir -p uploads

# 检查.env文件
if [ ! -f ".env" ]; then
    echo "⚠️  未找到 .env 文件"
    echo "请复制 env.example.txt 为 .env 并填入API密钥"
    echo ""
    echo "示例："
    echo "  cp env.example.txt .env"
    echo "  vim .env"
    echo ""
fi

# 启动后端
echo ""
echo "🚀 启动后端服务..."
echo "   API地址: http://localhost:8000"
echo "   文档地址: http://localhost:8000/docs"
echo ""
echo "💡 提示: 新开一个终端运行前端"
echo "   cd frontend && python3 -m http.server 3000"
echo ""

python main.py


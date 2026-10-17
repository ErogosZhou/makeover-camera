#!/bin/bash
# 换装相机 腾讯云 SCF 部署脚本

set -e

echo "🏠 换装相机 部署到腾讯云 SCF"
echo "================================"

# 检查 serverless 是否安装
if ! command -v serverless &> /dev/null; then
    echo "❌ 未找到 serverless CLI，正在安装..."
    npm install -g serverless
fi

# 检查环境变量文件
if [ -f ".env.scf" ]; then
    echo "📦 加载环境变量..."
    export $(cat .env.scf | grep -v '^#' | xargs)
else
    echo "⚠️  未找到 .env.scf 文件"
    echo "   请复制 .env.scf.example 为 .env.scf 并填入配置"
    exit 1
fi

# 安装后端依赖到本地（确保 SCF 可以找到）
echo "📦 安装 Python 依赖..."
cd backend
pip install -r requirements.txt -t . --upgrade
cd ..

# 部署
echo "🚀 开始部署..."
serverless deploy

echo ""
echo "✅ 部署完成！"
echo ""
echo "📋 后续步骤："
echo "1. 在腾讯云控制台绑定自定义域名"
echo "2. 配置 HTTPS 证书"
echo "3. 部署前端到 COS 静态网站托管"

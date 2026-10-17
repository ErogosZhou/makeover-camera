#!/bin/bash
# 换装相机 快速部署脚本
# 在本地执行，会自动完成所有部署步骤

set -e

SERVER_IP="129.211.172.11"
SERVER_USER="root"
SERVER_PASS="wn7B4NjH3%C\$"

echo "========================================="
echo "  换装相机 一键部署"
echo "========================================="
echo ""
echo "目标服务器: $SERVER_IP"
echo ""

# 检查项目目录
if [ ! -f "backend/main.py" ]; then
    echo "错误: 请在项目根目录运行此脚本"
    exit 1
fi

# 步骤1: 上传环境配置脚本
echo ">>> [1/5] 上传环境配置脚本..."
scp -o StrictHostKeyChecking=no deploy/server_setup.sh $SERVER_USER@$SERVER_IP:/tmp/

# 步骤2: 配置服务器环境
echo ""
echo ">>> [2/5] 配置服务器环境（需要 5-10 分钟）..."
ssh -o StrictHostKeyChecking=no $SERVER_USER@$SERVER_IP "bash /tmp/server_setup.sh"

# 步骤3: 打包并上传代码
echo ""
echo ">>> [3/5] 打包代码..."
tar czf /tmp/homeglow.tar.gz \
    --exclude='backend/venv' \
    --exclude='backend/__pycache__' \
    --exclude='backend/*.pyc' \
    --exclude='backend/uploads' \
    --exclude='backend/*.db' \
    --exclude='backend/*.log' \
    --exclude='.git' \
    --exclude='deploy' \
    backend frontend

echo ">>> [3/5] 上传代码和配置..."
scp /tmp/homeglow.tar.gz $SERVER_USER@$SERVER_IP:/tmp/
scp backend/.env $SERVER_USER@$SERVER_IP:/tmp/
scp deploy/deploy_app.sh $SERVER_USER@$SERVER_IP:/tmp/

rm /tmp/homeglow.tar.gz

# 步骤4: 解压代码
echo ""
echo ">>> [4/5] 解压代码..."
ssh $SERVER_USER@$SERVER_IP << 'ENDSSH'
mkdir -p /var/www/homeglow
cd /var/www/homeglow
tar xzf /tmp/homeglow.tar.gz
cp /tmp/.env backend/.env
cp /tmp/deploy_app.sh backend/
rm /tmp/homeglow.tar.gz /tmp/.env /tmp/deploy_app.sh
ENDSSH

# 步骤5: 部署应用
echo ""
echo ">>> [5/5] 部署应用..."
ssh $SERVER_USER@$SERVER_IP "cd /var/www/homeglow/backend && bash deploy_app.sh"

echo ""
echo "========================================="
echo "  ✅ 部署完成！"
echo "========================================="
echo ""
echo "访问地址: http://$SERVER_IP/"
echo ""
echo "查看日志:"
echo "  ssh $SERVER_USER@$SERVER_IP"
echo "  tail -f /var/log/homeglow/app.log"
echo ""

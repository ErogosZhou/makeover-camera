#!/bin/bash
# 换装相机 手动部署脚本（需要手动输入密码）

set -e

SERVER_IP="129.211.172.11"
SERVER_USER="root"

echo "========================================="
echo "  换装相机 部署"
echo "========================================="
echo ""
echo "目标服务器: $SERVER_IP"
echo "密码: wn7B4NjH3%C\$"
echo ""
echo "注意: 每个 scp/ssh 命令都需要输入密码"
echo ""
read -p "按回车继续..."

# 检查项目目录
if [ ! -f "backend/main.py" ]; then
    echo "错误: 请在项目根目录运行此脚本"
    exit 1
fi

# 打包代码
echo ""
echo ">>> [1/4] 打包代码..."
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
echo "✓ 代码打包完成"

# 上传文件
echo ""
echo ">>> [2/4] 上传代码（需要输入密码 3 次）..."
echo "上传代码包..."
scp -o StrictHostKeyChecking=no /tmp/homeglow.tar.gz $SERVER_USER@$SERVER_IP:/tmp/
echo "上传配置文件..."
scp -o StrictHostKeyChecking=no backend/.env $SERVER_USER@$SERVER_IP:/tmp/
echo "上传部署脚本..."
scp -o StrictHostKeyChecking=no deploy/deploy_app.sh $SERVER_USER@$SERVER_IP:/tmp/
echo "✓ 文件上传完成"

rm /tmp/homeglow.tar.gz

# 解压和部署
echo ""
echo ">>> [3/4] 解压代码（需要输入密码 1 次）..."
ssh -o StrictHostKeyChecking=no $SERVER_USER@$SERVER_IP << 'ENDSSH'
mkdir -p /var/www/homeglow
cd /var/www/homeglow
echo "解压代码包..."
tar xzf /tmp/homeglow.tar.gz
echo "复制配置文件..."
cp /tmp/.env backend/.env
cp /tmp/deploy_app.sh backend/
rm /tmp/homeglow.tar.gz /tmp/.env /tmp/deploy_app.sh
echo "✓ 代码解压完成"
ENDSSH

# 部署应用
echo ""
echo ">>> [4/4] 部署应用（需要输入密码 1 次）..."
ssh -o StrictHostKeyChecking=no $SERVER_USER@$SERVER_IP "cd /var/www/homeglow/backend && bash deploy_app.sh"

echo ""
echo "========================================="
echo "  ✅ 部署完成！"
echo "========================================="
echo ""
echo "访问地址: http://$SERVER_IP/"
echo ""
echo "查看状态:"
echo "  ssh $SERVER_USER@$SERVER_IP"
echo "  supervisorctl status homeglow"
echo ""
echo "查看日志:"
echo "  tail -f /var/log/homeglow/app.log"
echo ""

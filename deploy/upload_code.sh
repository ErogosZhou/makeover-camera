#!/bin/bash
# 上传代码到服务器

SERVER_IP="129.211.172.11"
SERVER_USER="root"
SERVER_DIR="/var/www/homeglow"

echo "========================================="
echo "  上传代码到服务器"
echo "========================================="

# 进入项目根目录
cd "$(dirname "$0")/.."

echo ">>> 打包代码..."
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

echo ">>> 上传到服务器..."
scp /tmp/homeglow.tar.gz $SERVER_USER@$SERVER_IP:/tmp/

echo ">>> 解压代码..."
ssh $SERVER_USER@$SERVER_IP << 'EOF'
mkdir -p /var/www/homeglow
cd /var/www/homeglow
tar xzf /tmp/homeglow.tar.gz
rm /tmp/homeglow.tar.gz
EOF

rm /tmp/homeglow.tar.gz

echo ""
echo "========================================="
echo "  ✅ 代码上传完成！"
echo "========================================="
echo ""
echo "接下来运行："
echo "  ssh root@$SERVER_IP"
echo "  bash /var/www/homeglow/backend/deploy_app.sh"
echo ""

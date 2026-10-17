#!/bin/bash
# 换装相机 快速更新脚本

set -e

SERVER="root@129.211.172.11"
REMOTE_DIR="/var/www/homeglow"

echo "========================================="
echo "  换装相机 代码更新"
echo "========================================="

# 检查是否在项目目录
if [ ! -f "backend/main.py" ]; then
    echo "错误: 请在项目根目录运行此脚本"
    exit 1
fi

echo ""
echo ">>> [1/3] 上传后端代码..."
scp -r backend/{main.py,api,services,models,config,scf_handler.py} $SERVER:$REMOTE_DIR/backend/

echo ""
echo ">>> [2/3] 上传前端代码..."
scp frontend/v2.zh.html frontend/v2.html $SERVER:$REMOTE_DIR/frontend/

echo ""
echo ">>> [3/3] 重启应用..."
ssh $SERVER "supervisorctl restart homeglow"

echo ""
sleep 2
ssh $SERVER "supervisorctl status homeglow"

echo ""
echo "========================================="
echo "  ✅ 更新完成！"
echo "========================================="
echo ""
echo "访问: http://129.211.172.11/"
echo ""

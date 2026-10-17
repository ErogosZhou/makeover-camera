#!/bin/bash
# 换装相机 应用部署脚本

set -e

APP_DIR="/var/www/homeglow"
BACKEND_DIR="$APP_DIR/backend"
FRONTEND_DIR="$APP_DIR/frontend"

echo "========================================="
echo "  换装相机 应用部署"
echo "========================================="

cd $APP_DIR

# 安装 Python 依赖
echo ">>> 安装 Python 依赖..."
cd $BACKEND_DIR
pip3 install -r requirements.txt --no-cache-dir

# 创建上传目录
mkdir -p $BACKEND_DIR/uploads

# 配置 Supervisor
echo ">>> 配置 Supervisor..."
cat > /etc/supervisor/conf.d/homeglow.conf << EOF
[program:homeglow]
command=/usr/bin/python3 $BACKEND_DIR/main.py
directory=$BACKEND_DIR
user=root
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/homeglow/app.log
stdout_logfile_maxbytes=50MB
stdout_logfile_backups=10
environment=PATH="/usr/bin"
EOF

# 重启 Supervisor
supervisorctl reread
supervisorctl update
supervisorctl restart homeglow

# 配置 Nginx
echo ">>> 配置 Nginx..."
cat > /etc/nginx/conf.d/homeglow.conf << 'EOF'
server {
    listen 80;
    server_name _;

    client_max_body_size 20M;

    # API 转发到后端
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket 支持
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        # 超时设置
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }

    # 上传的图片
    location /uploads/ {
        alias /var/www/homeglow/backend/uploads/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # 前端静态文件
    location / {
        root /var/www/homeglow/frontend;
        try_files $uri $uri/ /v2.zh.html;
        expires 1h;
        add_header Cache-Control "public";
    }

    # 健康检查
    location /health {
        proxy_pass http://127.0.0.1:8000/api/v1/health;
        access_log off;
    }
}
EOF

# 测试 Nginx 配置
nginx -t

# 重启 Nginx
systemctl restart nginx

echo ""
echo "========================================="
echo "  ✅ 应用部署完成！"
echo "========================================="
echo ""
echo "服务状态："
supervisorctl status homeglow
echo ""
echo "访问地址："
echo "http://$(curl -s ifconfig.me)"
echo ""
echo "日志查看："
echo "  应用日志: tail -f /var/log/homeglow/app.log"
echo "  Nginx日志: tail -f /var/log/nginx/access.log"
echo ""

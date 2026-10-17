#!/bin/bash
# 换装相机 服务器初始化脚本
# 适用于 TencentOS Server 3.3 / CentOS / RHEL

set -e

echo "========================================="
echo "  换装相机 服务器环境配置"
echo "========================================="

# 更新系统
echo ">>> 更新系统包..."
yum update -y

# 安装基础工具
echo ">>> 安装基础工具..."
yum install -y git wget curl vim unzip

# 安装 Python 3.12
echo ">>> 安装 Python 3.12..."
yum install -y python3.12 python3.12-devel python3.12-pip

# 设置 Python3.12 为默认
alternatives --install /usr/bin/python3 python3 /usr/bin/python3.12 1
alternatives --install /usr/bin/pip3 pip3 /usr/bin/pip3.12 1

# 验证 Python 版本
python3 --version

# 安装 Nginx
echo ">>> 安装 Nginx..."
yum install -y nginx
systemctl enable nginx

# 安装 Supervisor
echo ">>> 安装 Supervisor..."
pip3 install supervisor

# 创建 Supervisor 配置目录
mkdir -p /etc/supervisor/conf.d

# 生成 Supervisor 配置文件
cat > /etc/supervisord.conf << 'EOF'
[unix_http_server]
file=/var/run/supervisor.sock
chmod=0700

[supervisord]
logfile=/var/log/supervisord.log
logfile_maxbytes=50MB
logfile_backups=10
loglevel=info
pidfile=/var/run/supervisord.pid
nodaemon=false

[rpcinterface:supervisor]
supervisor.rpcinterface_factory = supervisor.rpcinterface:make_main_rpcinterface

[supervisorctl]
serverurl=unix:///var/run/supervisor.sock

[include]
files = /etc/supervisor/conf.d/*.conf
EOF

# 创建 Supervisor systemd 服务
cat > /etc/systemd/system/supervisord.service << 'EOF'
[Unit]
Description=Supervisor process control system
After=network.target

[Service]
Type=forking
ExecStart=/usr/local/bin/supervisord -c /etc/supervisord.conf
ExecStop=/usr/local/bin/supervisorctl shutdown
ExecReload=/usr/local/bin/supervisorctl reload
KillMode=process
Restart=on-failure
RestartSec=42s

[Install]
WantedBy=multi-user.target
EOF

# 启用并启动 Supervisor
systemctl daemon-reload
systemctl enable supervisord
systemctl start supervisord

# 创建应用目录
echo ">>> 创建应用目录..."
mkdir -p /var/www/homeglow
mkdir -p /var/log/homeglow

# 防火墙配置
echo ">>> 配置防火墙..."
if command -v firewall-cmd &> /dev/null; then
    firewall-cmd --permanent --add-service=http
    firewall-cmd --permanent --add-service=https
    firewall-cmd --permanent --add-port=8000/tcp
    firewall-cmd --reload
fi

echo ""
echo "========================================="
echo "  ✅ 服务器环境配置完成！"
echo "========================================="
echo ""
echo "接下来："
echo "1. 上传代码到 /var/www/homeglow"
echo "2. 运行 deploy_app.sh 部署应用"
echo ""

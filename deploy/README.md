# 换装相机 服务器部署指南

服务器信息：
- IP: 129.211.172.11
- 用户: root
- 系统: TencentOS Server 3.3

## 一键部署

### 步骤1: 配置服务器环境

```bash
# 本地执行，上传环境配置脚本
scp deploy/server_setup.sh root@129.211.172.11:/tmp/

# SSH 登录服务器
ssh root@129.211.172.11

# 运行环境配置脚本
bash /tmp/server_setup.sh
```

### 步骤2: 上传代码

```bash
# 在本地项目目录执行
cd /Users/zhouzichao/geminihome/homeglow
chmod +x deploy/*.sh

# 上传代码
./deploy/upload_code.sh
```

### 步骤3: 上传 .env 文件

```bash
# 在本地执行
scp backend/.env root@129.211.172.11:/var/www/homeglow/backend/
```

### 步骤4: 部署应用

```bash
# SSH 到服务器
ssh root@129.211.172.11

# 上传部署脚本
scp deploy/deploy_app.sh root@129.211.172.11:/var/www/homeglow/backend/

# 运行部署脚本
cd /var/www/homeglow/backend
bash deploy_app.sh
```

### 步骤5: 访问测试

打开浏览器访问：
- http://129.211.172.11/

---

## 日常维护命令

```bash
# SSH 登录
ssh root@129.211.172.11

# 查看应用状态
supervisorctl status homeglow

# 重启应用
supervisorctl restart homeglow

# 查看应用日志
tail -f /var/log/homeglow/app.log

# 查看 Nginx 日志
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log

# 更新代码（在本地执行）
cd /Users/zhouzichao/geminihome/homeglow
./deploy/upload_code.sh
ssh root@129.211.172.11 "supervisorctl restart homeglow"
```

---

## 配置 HTTPS（备案通过后）

```bash
# SSH 到服务器
ssh root@129.211.172.11

# 安装 certbot
yum install -y certbot python3-certbot-nginx

# 申请证书（替换 your-domain.com）
certbot --nginx -d your-domain.com -d www.your-domain.com

# 证书会自动配置到 Nginx，并设置自动续期
```

---

## 故障排查

### 应用无法启动

```bash
# 查看详细错误日志
tail -100 /var/log/homeglow/app.log

# 手动运行测试
cd /var/www/homeglow/backend
python3 main.py
```

### Nginx 配置错误

```bash
# 测试配置
nginx -t

# 查看错误日志
tail -50 /var/log/nginx/error.log
```

### 端口被占用

```bash
# 查看 8000 端口占用
netstat -tlnp | grep 8000

# 杀掉进程
kill -9 <PID>
```

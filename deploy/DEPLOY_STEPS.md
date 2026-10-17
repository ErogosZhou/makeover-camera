# 部署步骤（逐步执行）

服务器信息：
- IP: 129.211.172.11
- 密码: wn7B4NjH3%C$

---

## 第一步：上传环境配置脚本

在你的**本地终端**执行：

```bash
cd /Users/zhouzichao/geminihome/homeglow

# 上传环境配置脚本
scp deploy/server_setup.sh root@129.211.172.11:/tmp/
# 输入密码: wn7B4NjH3%C$
```

---

## 第二步：配置服务器环境

```bash
# SSH 登录服务器
ssh root@129.211.172.11
# 输入密码: wn7B4NjH3%C$

# 运行环境配置脚本（需要5-10分钟）
bash /tmp/server_setup.sh

# 完成后退出
exit
```

---

## 第三步：上传代码

回到**本地终端**：

```bash
cd /Users/zhouzichao/geminihome/homeglow

# 打包代码
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

# 上传代码包
scp /tmp/homeglow.tar.gz root@129.211.172.11:/tmp/
# 输入密码

# 上传 .env 文件
scp backend/.env root@129.211.172.11:/tmp/
```

---

## 第四步：部署应用

SSH 到服务器：

```bash
ssh root@129.211.172.11
# 输入密码
```

在服务器上执行：

```bash
# 创建目录
mkdir -p /var/www/homeglow

# 解压代码
cd /var/www/homeglow
tar xzf /tmp/homeglow.tar.gz

# 复制 .env
cp /tmp/homeglow.tar.gz backend/.env

# 上传部署脚本
exit  # 先退出服务器
```

回到本地：

```bash
scp deploy/deploy_app.sh root@129.211.172.11:/var/www/homeglow/backend/
```

再次登录服务器：

```bash
ssh root@129.211.172.11

# 运行部署脚本
cd /var/www/homeglow/backend
bash deploy_app.sh
```

---

## 第五步：验证

打开浏览器访问：

**http://129.211.172.11/**

应该能看到 换装相机 首页（中文版）。

---

## 如果出错

查看日志：

```bash
# 应用日志
tail -f /var/log/homeglow/app.log

# Nginx 日志
tail -f /var/log/nginx/error.log
```

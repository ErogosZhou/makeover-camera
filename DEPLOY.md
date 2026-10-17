# 换装相机 腾讯云部署指南

> 使用云函数 SCF + 函数 URL 方案（API 网关已于 2025年6月停服）

## 架构说明

```
用户 -> 函数URL/自定义域名 -> 云函数SCF -> 业务逻辑
                                  ↓
                            COS存储（图片）
```

**优势**：
- 函数 URL 免费，无需额外付费
- Serverless 架构，按调用计费
- 自动弹性伸缩

## 准备工作

### 1. 开通腾讯云服务

在腾讯云控制台开通以下服务：
- **云函数 SCF**: https://console.cloud.tencent.com/scf
- **对象存储 COS**: https://console.cloud.tencent.com/cos

### 2. 创建 COS 存储桶

1. 进入 COS 控制台，点击「创建存储桶」
2. 配置：
   - 名称：`homeglow`（会自动加上 AppID 后缀）
   - 地域：选择与云函数相同的地域（如 `ap-guangzhou`）
   - 访问权限：**公有读私有写**（图片需要公开访问）
3. 创建后记录存储桶名称，格式如 `homeglow-1234567890`

### 3. 获取 API 密钥

1. 进入「访问管理」->「API密钥管理」
2. 创建密钥，记录 `SecretId` 和 `SecretKey`

### 4. 配置环境变量

```bash
# 复制配置模板
cp .env.scf.example .env.scf

# 编辑配置文件，填入真实值
vim .env.scf
```

## 部署步骤

### 方式一：使用部署脚本（推荐）

```bash
# 安装 Serverless CLI（如未安装）
npm install -g serverless

# 执行部署
./deploy.sh
```

### 方式二：手动部署

```bash
# 1. 加载环境变量
export $(cat .env.scf | grep -v '^#' | xargs)

# 2. 安装依赖到 backend 目录
cd backend
pip install -r requirements.txt -t . --upgrade
cd ..

# 3. 部署
serverless deploy
```

部署成功后会输出函数 URL 地址，类似：
```
functionUrl: https://xxxxxxxx.gz.tencentscf.com
```

## 绑定自定义域名

### 方式一：通过云函数控制台（推荐）

1. 登录 [云函数控制台](https://console.cloud.tencent.com/scf)
2. 找到 `homeglow-api` 函数
3. 点击「函数 URL」标签页
4. 点击「添加自定义域名」
5. 填写：
   - **域名**：你的域名，如 `api.yourdomain.com`
   - **协议**：HTTPS
   - **证书**：选择已有证书或申请免费证书

### 方式二：使用 CDN 加速（可选）

如果需要 CDN 加速，可以：

1. 在 CDN 控制台添加域名
2. 源站配置为函数 URL 地址
3. 配置 HTTPS 证书

### DNS 解析配置

在你的域名服务商添加 CNAME 记录：

| 主机记录 | 记录类型 | 记录值 |
|---------|---------|--------|
| api | CNAME | xxxxxxxx.gz.tencentscf.com |

等待 DNS 生效（通常几分钟）

### 测试访问

```bash
# 使用函数 URL
curl https://xxxxxxxx.gz.tencentscf.com/api/v1/health

# 使用自定义域名
curl https://api.yourdomain.com/api/v1/health
```

## 前端部署

前端是纯静态页面，推荐部署到 COS 静态网站：

### 1. 创建前端存储桶

1. 在 COS 创建新存储桶（如 `homeglow-web-xxx`）
2. 权限设置为「公有读私有写」
3. 开启「静态网站」功能

### 2. 修改前端 API 地址

编辑 `frontend/index.html`，修改 API 地址：

```javascript
// 修改为你的后端地址
const API_BASE = 'https://api.yourdomain.com';
// 或使用函数 URL
const API_BASE = 'https://xxxxxxxx.gz.tencentscf.com';
```

### 3. 上传前端文件

```bash
# 使用 coscmd 上传
pip install coscmd
coscmd config -a <SecretId> -s <SecretKey> -b <bucket> -r <region>
coscmd upload -r frontend/ /
```

### 4. 绑定前端域名

在 COS 静态网站设置中绑定域名，如 `www.yourdomain.com`

## 常见问题

### Q: 云函数冷启动慢？

可以配置预置并发（会产生额外费用）：
```yaml
# serverless.yml 中添加
inputs:
  provisionedConcurrencyConfig:
    count: 1  # 预置1个实例
```

### Q: 上传图片失败？

检查：
1. COS 存储桶权限是否为「公有读私有写」
2. 环境变量中的 COS 配置是否正确
3. SecretId/SecretKey 是否有 COS 访问权限

### Q: 跨域问题？

已在代码中配置 CORS。如仍有问题：
1. 检查前端请求的域名是否在 CORS 白名单中
2. 可以在 `main.py` 中添加你的域名到 `allow_origins`

### Q: 函数 URL 是否支持自定义域名？

支持！在云函数控制台的「函数 URL」页面可以添加自定义域名。

### Q: 如何查看日志？

1. 进入云函数控制台
2. 选择函数 -> 「日志查询」
3. 或配置 CLS 日志服务进行持久化

## 成本估算

| 服务 | 免费额度 | 超出价格 |
|-----|---------|---------|
| 云函数 SCF | 40万GB-s/月 | ¥0.00011/GB-s |
| 函数 URL | **免费** | 无 |
| COS 存储 | 50GB/月 | ¥0.118/GB |
| COS 流量 | 10GB/月 | ¥0.50/GB |

对于小型项目，基本在免费额度内，每月成本接近 0。

## 项目结构（部署相关）

```
homeglow/
├── backend/
│   ├── scf_handler.py      # 云函数入口
│   ├── services/
│   │   └── cos_storage.py  # COS 存储服务
│   └── ...
├── frontend/
│   └── index.html
├── serverless.yml          # 部署配置
├── .env.scf.example        # 环境变量模板
├── deploy.sh               # 部署脚本
└── DEPLOY.md               # 本文档
```

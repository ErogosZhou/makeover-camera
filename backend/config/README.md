# 配置管理

## 概述

配置管理模块负责读取和管理应用的所有配置项，包括 API 密钥、服务器配置等。

## 文件结构

```
config/
├── __init__.py      # 导出 settings
└── settings.py      # 配置类定义
```

## 配置项说明

### 基础配置

- `APP_NAME`: 应用名称（默认: "换装相机"）
- `DEBUG`: 调试模式（默认: True）
- `API_V1_PREFIX`: API 前缀（默认: "/api/v1"）

### 服务器配置

- `HOST`: 服务器地址（默认: "0.0.0.0"）
- `PORT`: 服务器端口（默认: 8000）

### 文件上传配置

- `UPLOAD_DIR`: 上传目录（默认: "uploads"）
- `MAX_UPLOAD_SIZE`: 最大上传大小（默认: 10MB）
- `ALLOWED_EXTENSIONS`: 允许的文件扩展名（默认: {"jpg", "jpeg", "png", "webp"}）

### 图片生成服务配置

- `IMAGE_GEN_API_KEY`: 图片生成 API 密钥（必需）
- `IMAGE_GEN_API_URL`: API 地址（默认: "https://xiaoai.plus/v1"）
- `IMAGE_GEN_MODEL`: 模型名称（默认: "gemini-3-pro-image-preview"）

### VLLM 服务配置

- `VLLM_API_KEY`: VLLM API 密钥（必需）
- `VLLM_API_URL`: API 地址（默认: "https://xiaoai.plus/v1"）
- `VLLM_MODEL`: 模型名称（默认: "gemini-3-pro-preview"）

### 电商平台配置

#### 拼多多多多进宝
- `PDD_CLIENT_ID`: 客户端 ID
- `PDD_CLIENT_SECRET`: 客户端密钥
- `PDD_PID`: 推广位 ID

#### 大淘客
- `DATAOKE_APP_KEY`: 应用 Key
- `DATAOKE_APP_SECRET`: 应用密钥

#### 淘宝客
- `TAOBAO_APP_KEY`: 应用 Key
- `TAOBAO_APP_SECRET`: 应用密钥
- `TAOBAO_ADZONE_ID`: 推广位 ID

### 数据库配置

- `DATABASE_URL`: 数据库连接字符串（默认: "sqlite+aiosqlite:///./homeglow.db"）

### 腾讯云 COS 配置（可选）

- `COS_SECRET_ID`: COS Secret ID
- `COS_SECRET_KEY`: COS Secret Key
- `COS_REGION`: 区域（默认: "ap-guangzhou"）
- `COS_BUCKET`: 存储桶名称
- `COS_CDN_DOMAIN`: CDN 加速域名（可选）

## 使用方法

### 读取配置

```python
from config.settings import settings

# 读取配置项
api_key = settings.IMAGE_GEN_API_KEY
upload_dir = settings.UPLOAD_DIR
```

### 检查 API 密钥

```python
from config.settings import check_api_keys

missing = check_api_keys()
if missing:
    print(f"缺少配置: {', '.join(missing)}")
```

## 环境变量配置

配置通过环境变量读取，支持 `.env` 文件。

### 创建 `.env` 文件

```bash
cp env.example.txt .env
```

### 配置示例

```env
# 图片生成服务
IMAGE_GEN_API_KEY=your_gemini_api_key
IMAGE_GEN_API_URL=https://xiaoai.plus/v1
IMAGE_GEN_MODEL=gemini-3-pro-image-preview

# VLLM 服务
VLLM_API_KEY=your_gemini_api_key
VLLM_API_URL=https://xiaoai.plus/v1
VLLM_MODEL=gemini-3-pro-preview

# 拼多多配置
PDD_CLIENT_ID=your_client_id
PDD_CLIENT_SECRET=your_client_secret
PDD_PID=your_pid

# 或使用大淘客
DATAOKE_APP_KEY=your_app_key
DATAOKE_APP_SECRET=your_app_secret

# 腾讯云 COS（可选）
COS_SECRET_ID=your_secret_id
COS_SECRET_KEY=your_secret_key
COS_BUCKET=your_bucket
COS_REGION=ap-guangzhou
```

## 配置验证

`check_api_keys()` 函数会检查必需的 API 密钥：

- 图片生成 API 密钥
- VLLM API 密钥
- 至少一个电商平台配置（拼多多/大淘客/淘宝客）

## 扩展开发

### 添加新的配置项

1. 在 `Settings` 类中添加新字段
2. 设置默认值（可选）
3. 添加类型注解

示例：

```python
class Settings(BaseSettings):
    # 新配置项
    NEW_SERVICE_API_KEY: Optional[str] = None
    NEW_SERVICE_API_URL: str = "https://api.example.com"
```

### 添加配置验证

在 `check_api_keys()` 函数中添加验证逻辑。

## 注意事项

1. **安全性**：不要将 `.env` 文件提交到版本控制
2. **默认值**：为可选配置项设置合理的默认值
3. **类型**：使用类型注解确保类型安全
4. **环境变量**：配置项名称会自动转换为环境变量名称（大写，下划线分隔）




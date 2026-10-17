# Backend - 换装相机 后端服务

## 概述

换装相机 后端是基于 FastAPI 的异步 Web 服务，提供 AI 家装改造的核心功能。

## 技术栈

- **FastAPI** - 高性能异步 Web 框架
- **Python 3.6+** - 编程语言（生产环境兼容 Python 3.6）
- **Pydantic** - 数据验证和序列化
- **httpx** - 异步 HTTP 客户端
- **Pillow** - 图像处理（Progressive JPEG 转换）
- **loguru** - 日志记录
- **SQLAlchemy + SQLite** - 数据库 ORM

## 项目结构

```
backend/
├── main.py              # 应用入口，FastAPI 应用初始化
├── api/                 # API 路由层
│   └── routes.py        # 所有 API 端点定义
├── config/              # 配置管理
│   └── settings.py      # 环境变量和配置读取
├── models/              # 数据模型
│   └── schemas.py       # Pydantic 模型定义
├── services/            # 业务逻辑服务层
│   ├── image_generator.py    # 🔥 图片生成服务（Seedream/Gemini）
│   ├── space_analyzer.py     # AI 空间分析（豆包大模型）
│   ├── item_identifier.py    # 物品识别服务（Gemini Vision）
│   ├── product_matcher.py    # 商品匹配服务（拼多多）
│   ├── product_service.py    # 统一商品服务
│   ├── prompts_i18n.py       # Prompt 模板（多语言）
│   └── cos_storage.py        # 腾讯云 COS 存储服务
├── uploads/             # 本地文件上传目录（开发环境）
├── requirements.txt     # Python 依赖
└── env.example.txt      # 环境变量示例
```

## 核心功能

### 1. 图片上传 (`/api/v1/upload`)
- 支持 JPEG、PNG、WebP 格式
- 最大 10MB
- 支持本地存储和腾讯云 COS 存储（Serverless 环境）

### 2. 生成改造效果图 (`/api/v1/generate-v2`)
- 零决策体验：用户无需选择风格和预算
- AI 自动分析空间（豆包大模型）
- 调用 Seedream 生成图片（15-20秒）
- 自动转换为 Progressive JPEG 优化加载

### 3. 物品识别 (`/api/v1/identify-items`)
- 使用 Gemini Vision 识别效果图中的物品
- 提取软装物品列表（地毯、抱枕、灯具等）
- 智能过滤硬装和建筑元素

### 4. 商品匹配 (`/api/v1/products/search`)
- 基于识别结果搜索拼多多商品
- 筛选条件：销量、好评率、价格区间
- 返回匹配商品和拼多多链接

## 启动方式

### 开发环境

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 配置环境变量
cp env.example.txt .env
# 编辑 .env 文件，填入 API 密钥

# 启动服务
python main.py
```

服务将在 `http://localhost:8000` 启动

- API 文档: `http://localhost:8000/docs`
- 健康检查: `http://localhost:8000/api/v1/health`

### 生产环境

使用 `uvicorn` 启动：

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

## 环境变量配置

### 必需配置：

**AI 服务**:
- `IMAGE_GEN_API_KEY` - 图片生成 API 密钥（Seedream/豆包）
- `IMAGE_GEN_PROVIDER` - 图片生成服务商（seedream 或 gemini）
- `IMAGE_GEN_MODEL` - 生成模型（doubao-seedream-4-0-250828）
- `DOUBAO_API_KEY` - 豆包大模型 API 密钥（空间分析）
- `GEMINI_API_KEY` - Gemini API 密钥（物品识别）

**电商平台**（至少配置一个）:
- 拼多多：`PDD_CLIENT_ID`, `PDD_CLIENT_SECRET`, `PDD_PID`

### 可选配置：

**存储服务**:
- `COS_SECRET_ID`, `COS_SECRET_KEY`, `COS_BUCKET` - 腾讯云 COS 存储
- `COS_REGION` - COS 区域

**应用配置**:
- `DEBUG` - 调试模式（默认 False）
- `HOST` - 服务地址（默认 0.0.0.0）
- `PORT` - 服务端口（默认 8000）
- `UPLOAD_DIR` - 上传目录（默认 ./uploads）

**安全配置**:
- `JWT_SECRET_KEY` - JWT 密钥（用于用户认证）
- `JWT_ALGORITHM` - JWT 算法（默认 HS256）

## API 端点

### GET `/api/v1/health`
健康检查

### GET `/api/v1/options`
获取配置选项（房间类型、风格、预算）

### POST `/api/v1/upload`
上传图片，返回 `image_id`

### POST `/api/v1/generate-v2`
**v2版本（推荐）**: 零决策生成，AI 自动分析并生成

请求体:
```json
{
  "image_id": "abc123",
  "lang": "zh"
}
```

响应:
```json
{
  "result": {
    "generated_image_url": "/uploads/generated_xxx.jpg",
    "room_type": "living_room",
    "applied_style": "nordic",
    "space_analysis": {...}
  }
}
```

### POST `/api/v1/identify-items`
识别效果图中的物品

请求体:
```json
{
  "image_url": "/uploads/generated_xxx.jpg"
}
```

### POST `/api/v1/products/search`
搜索匹配的商品（拼多多）

请求体:
```json
{
  "keywords": "北欧风地毯"
}
```

## 任务流程

1. **PENDING** - 任务创建，等待处理
2. **GENERATING** - 调用图片生成 API，生成效果图
3. **IDENTIFYING** - 识别效果图中的新增物品
4. **MATCHING** - 为每个物品匹配商品
5. **COMPLETED** - 完成，返回结果
6. **FAILED** - 失败，返回错误信息

## 数据存储

当前使用内存存储任务状态（`tasks_store` 字典），重启会丢失。

生产环境建议：
- 使用 Redis 存储任务状态
- 使用数据库存储历史记录
- 使用对象存储（COS/S3）存储图片

## 注意事项

1. **API 密钥安全**：不要将 `.env` 文件提交到版本控制
2. **CORS 配置**：开发环境允许所有来源，生产环境需要限制
3. **文件上传**：开发环境使用本地存储，生产环境建议使用云存储
4. **异步处理**：生成任务使用后台任务处理，避免阻塞请求
5. **错误处理**：所有服务调用都有异常处理，失败时返回友好错误信息

## 扩展开发

### 添加新的图片生成服务

修改 `services/image_generator.py`，实现新的生成逻辑。

### 添加新的电商平台

在 `services/product_matcher.py` 中添加新的搜索方法。

### 添加新的风格或预算档位

修改 `api/routes.py` 中的 `get_options()` 函数。

## 架构设计

详细架构请参考 [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md)

### 核心设计理念

1. **专业设计语言**: 基于真实室内设计师的方法论
   - 60-30-10 色彩法则
   - 三角构图原则
   - 空间层次构建

2. **Progressive JPEG**: 图片自动转换为渐进式加载
   - 用户先看到模糊图，逐渐变清晰
   - 提升加载体验

3. **Python 3.6 兼容**: 服务器兼容性
   - 使用 `@app.on_event()` 代替 `asynccontextmanager`
   - 避免使用 3.7+ 特性

## 常见问题

### 服务无法启动

**问题**: `Address already in use`

**解决**:
```bash
lsof -i :8000 | grep LISTEN
kill -9 <PID>
```

### 图片生成返回 None

**可能原因**:
1. API Key 未配置 → 检查 `.env`
2. Seedream 服务超时 → 查看日志
3. 图片格式不支持 → 确保 JPG/PNG/WebP

### 前端卡在"AI 正在分析"

**调试**:
1. 检查浏览器 Network 标签
2. 查看 `/api/v1/generate-v2` 响应
3. 检查后端日志

## 开发指南

### 添加新风格

1. 在 `models/schemas.py` 添加枚举值:
```python
class StyleType(str, Enum):
    NORDIC = "nordic"
    YOUR_STYLE = "your_style"  # 新增
```

2. 在 `services/image_generator.py` 添加风格定义:
```python
STYLE_SYSTEM = {
    StyleType.YOUR_STYLE: {
        "name": "你的风格",
        "design_principle": "...",
        "color_strategy": {...},
        # ...
    }
}
```

3. 在 `services/prompts_i18n.py` 添加翻译

### 部署到生产环境

```bash
# 1. 上传代码到服务器
scp -r backend/ root@SERVER:/var/www/homeglow/

# 2. 安装依赖
ssh root@SERVER "cd /var/www/homeglow/backend && pip3 install -r requirements.txt"

# 3. 重启服务
ssh root@SERVER "supervisorctl restart homeglow"

# 4. 查看日志
ssh root@SERVER "tail -f /var/log/homeglow/app.log"
```

## 性能优化

### 已实现

- ✅ 异步 HTTP 请求（httpx）
- ✅ Progressive JPEG 转换
- ✅ 图片压缩（quality=90）

### 待优化

- [ ] CDN 加速（腾讯云 COS + CDN）
- [ ] 数据库索引优化
- [ ] API 请求并发（asyncio.gather）
- [ ] 图片懒加载

## 相关文档

- 📖 [架构文档](../docs/ARCHITECTURE.md) - 系统架构、数据流、核心模块
- 🤖 [AI 上下文](../docs/AI_CONTEXT.md) - 专门为 AI 助手准备的文档
- 📋 [API 路由文档](./api/README.md) - API 端点详细说明
- ⚙️ [配置管理文档](./config/README.md) - 环境变量和配置
- 📊 [数据模型文档](./models/README.md) - Pydantic 模型定义
- 🔧 [服务层文档](./services/README.md) - 业务逻辑服务

## 更新日志

### v2.0 (2026-02-08)
- ✨ 零决策体验（无需选择风格和预算）
- ✨ Seedream 图像生成（替代 Gemini）
- ✨ Progressive JPEG 优化
- ✨ 完整的架构文档和 AI 上下文文档
- 🐛 修复 Python 3.6 兼容性问题

### v1.0 (2025-12)
- 🎉 初始版本
- ✨ Gemini 图像生成
- ✨ 用户手动选择风格和预算




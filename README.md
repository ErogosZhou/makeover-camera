# 🏠 换装相机 - AI家装轻改造助手

> 一张照片，看见家的另一种可能

## 项目简介

换装相机 是一款基于AI的家装软装改造工具。用户上传房间照片，选择风格和预算，AI会生成改造后的效果图，并推荐可购买的同款商品。

## 技术栈

### 后端
- **FastAPI** - 高性能异步Web框架
- **Python 3.10+** - 编程语言
- **Pydantic** - 数据验证
- **httpx** - 异步HTTP客户端

### 前端
- **原生 HTML5** - 移动端H5页面
- **Tailwind CSS** - 样式框架
- **Alpine.js** - 轻量级交互框架

### 外部服务（需配置API）
- **图片生成服务** - Nano Banana / Flux 等
- **VLLM服务** - Claude / GPT-4V
- **电商推广** - 淘宝联盟 / 大淘客

## 快速开始

### 1. 安装后端依赖

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
# 复制示例配置
cp env.example.txt .env

# 编辑 .env 文件，填入真实的API密钥
```

### 3. 启动后端服务

```bash
cd backend
python main.py
```

后端服务将在 http://localhost:8000 启动

- API文档: http://localhost:8000/docs
- 健康检查: http://localhost:8000/api/v1/health

### 4. 启动前端

```bash
cd frontend

# 方式1: 使用Python内置服务器
python -m http.server 3000

# 方式2: 使用Node.js serve
npx serve -p 3000
```

前端页面访问: http://localhost:3000

## 项目结构

```
homeglow/
├── backend/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes.py          # API路由定义
│   │   └── README.md          # API路由文档
│   ├── config/
│   │   ├── __init__.py
│   │   ├── settings.py        # 配置管理
│   │   └── README.md          # 配置管理文档
│   ├── models/
│   │   ├── __init__.py
│   │   ├── schemas.py         # Pydantic模型
│   │   └── README.md          # 数据模型文档
│   ├── services/
│   │   ├── __init__.py
│   │   ├── image_generator.py # 图片生成服务
│   │   ├── item_identifier.py # 物品识别服务
│   │   ├── product_matcher.py # 商品匹配服务
│   │   ├── cos_storage.py     # COS存储服务
│   │   └── README.md          # 服务层文档
│   ├── main.py                # 应用入口
│   ├── requirements.txt       # Python依赖
│   ├── env.example.txt        # 环境变量示例
│   └── README.md              # 后端文档
│
├── frontend/
│   ├── index.html             # H5移动端页面
│   ├── src/                   # 源代码目录（预留）
│   │   └── README.md          # 前端源代码文档
│   └── README.md              # 前端文档
│
└── README.md                  # 项目主文档
```

## 项目文档

为了便于 AI 理解和修改代码，每个主要目录都有详细的 README 文档：

### 后端文档
- [后端总览](./backend/README.md) - 后端服务概述、启动方式、核心功能
- [API 路由](./backend/api/README.md) - API 端点说明、请求响应格式
- [配置管理](./backend/config/README.md) - 环境变量配置、配置项说明
- [数据模型](./backend/models/README.md) - Pydantic 模型定义、枚举类型
- [服务层](./backend/services/README.md) - 业务逻辑服务、外部 API 集成

### 前端文档
- [前端总览](./frontend/README.md) - 前端技术栈、页面流程、API 集成
- [源代码目录](./frontend/src/README.md) - 组件化改造建议、目录结构说明

## API 接口

### 获取配置选项
```
GET /api/v1/options
```

### 上传图片
```
POST /api/v1/upload
Content-Type: multipart/form-data

file: <图片文件>
```

### 发起生成任务
```
POST /api/v1/generate
Content-Type: multipart/form-data

image_id: string      # 上传返回的图片ID
room_type: string     # 房间类型
style: string         # 装修风格
budget: string        # 预算档位
custom_prompt: string # 自定义需求（可选）
```

### 查询任务状态
```
GET /api/v1/task/{task_id}
```

### 获取完整结果
```
GET /api/v1/result/{task_id}
```

## 待实现功能

以下功能需要配置对应的API密钥后实现：

### 1. 图片生成服务 (`services/image_generator.py`)

需要实现 `generate()` 方法，调用图片生成API（如Nano Banana）。

```python
# 配置
IMAGE_GEN_API_KEY=your_api_key
IMAGE_GEN_API_URL=https://api.xxx.com
```

### 2. 物品识别服务 (`services/item_identifier.py`)

需要实现 `identify()` 方法，调用VLLM识别效果图中的物品。

```python
# 配置
VLLM_API_KEY=your_anthropic_or_openai_key
VLLM_MODEL=claude-3-5-sonnet-20241022
```

### 3. 商品匹配服务 (`services/product_matcher.py`)

需要实现以下方法：
- `_search_taobao()` - 淘宝联盟商品搜索
- `_search_dataoke()` - 大淘客商品搜索
- `verify_similarity()` - 商品相似度校验

```python
# 淘宝联盟配置
TAOBAO_APP_KEY=your_app_key
TAOBAO_APP_SECRET=your_app_secret
TAOBAO_ADZONE_ID=your_adzone_id

# 或使用大淘客（更简单）
DATAOKE_APP_KEY=your_app_key
DATAOKE_APP_SECRET=your_app_secret
```

## 开发路线图

- [x] 项目结构搭建
- [x] FastAPI后端框架
- [x] 数据模型定义
- [x] API路由实现
- [x] H5前端页面
- [ ] 图片生成API对接
- [ ] VLLM物品识别对接
- [ ] 淘宝联盟/大淘客对接
- [ ] 商品相似度校验
- [ ] 数据库持久化
- [ ] 用户系统
- [ ] 部署上线

## 注意事项

1. **不要提交 `.env` 文件**，其中包含敏感的API密钥
2. 开发阶段CORS已开放，生产环境需要限制
3. 当前使用内存存储任务状态，重启会丢失，生产环境需要使用Redis或数据库

## License

MIT


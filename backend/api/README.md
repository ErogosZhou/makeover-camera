# API 路由层

## 概述

API 路由层负责处理所有 HTTP 请求，定义 API 端点和请求/响应格式。

## 文件结构

```
api/
├── __init__.py      # 导出 router
└── routes.py        # 所有 API 路由定义
```

## 主要功能

### 1. 图片上传 (`POST /api/v1/upload`)

**功能**：上传房间照片

**请求**：
- `file`: 图片文件（multipart/form-data）

**响应**：
```json
{
  "success": true,
  "image_id": "uuid",
  "image_url": "/uploads/filename.jpg",
  "message": "上传成功"
}
```

**实现细节**：
- 验证文件类型和大小
- 支持本地存储和 COS 存储
- 生成唯一文件名（UUID）

### 2. 获取配置选项 (`GET /api/v1/options`)

**功能**：返回前端需要的配置选项

**响应**：
```json
{
  "room_types": [...],
  "styles": [...],
  "budgets": [...]
}
```

**包含内容**：
- 房间类型：客厅、卧室、书房、阳台、餐厅
- 装修风格：简约北欧、日式无印、复古中古、轻奢现代、自然原木
- 预算档位：轻改造(300)、标准改造(500)、精致改造(1000)、豪华改造(2000)

### 3. 发起生成任务 (`POST /api/v1/generate`)

**功能**：创建异步生成任务

**请求**：
- `image_id`: 上传返回的图片 ID
- `room_type`: 房间类型
- `style`: 装修风格
- `budget`: 预算档位
- `custom_prompt`: 自定义需求（可选）

**响应**：
```json
{
  "task_id": "uuid",
  "status": "pending",
  "progress": 0,
  "message": "任务已创建，正在处理中..."
}
```

**实现细节**：
- 创建后台任务
- 立即返回 task_id
- 通过轮询 `/task/{task_id}` 获取进度

### 4. 查询任务状态 (`GET /api/v1/task/{task_id}`)

**功能**：查询任务当前状态和进度

**响应**：
```json
{
  "task_id": "uuid",
  "status": "generating",
  "progress": 30,
  "message": "正在生成效果图...",
  "result": null  // 完成时包含完整结果
}
```

**任务状态**：
- `pending` - 等待处理 (0%)
- `generating` - 生成效果图 (30%)
- `identifying` - 识别物品 (60%)
- `matching` - 匹配商品 (80%)
- `completed` - 完成 (100%)
- `failed` - 失败 (0%)

### 5. 获取完整结果 (`GET /api/v1/result/{task_id}`)

**功能**：获取任务的完整生成结果

**响应**：
```json
{
  "task_id": "uuid",
  "status": "completed",
  "original_image_url": "/uploads/xxx.jpg",
  "generated_image_url": "/uploads/generated_xxx.png",
  "shopping_list": [
    {
      "identified_item": {...},
      "matched_products": [...]
    }
  ],
  "total_estimated_price": 1234.56,
  "created_at": "2024-01-01T00:00:00",
  "completed_at": "2024-01-01T00:05:00"
}
```

## 后台任务处理

`process_generation_task()` 函数负责处理生成任务：

1. **生成效果图**
   - 调用 `ImageGeneratorService.generate()`
   - 保存生成图片

2. **识别物品**
   - 调用 `ItemIdentifierService.identify()`
   - 对比原图和效果图，识别新增物品

3. **匹配商品**
   - 对每个识别出的物品调用 `ProductMatcherService.match_products_for_item()`
   - 搜索电商平台，返回匹配商品

4. **汇总结果**
   - 计算总预估价格
   - 更新任务状态为 `completed`

## 错误处理

- 文件验证失败：返回 400 错误
- 图片不存在：返回 404 错误
- 任务不存在：返回 404 错误
- API 调用失败：记录错误，返回 500 错误

## 扩展开发

### 添加新的 API 端点

1. 在 `routes.py` 中添加新的路由函数
2. 使用 `@router.get()` 或 `@router.post()` 装饰器
3. 定义请求和响应模型（在 `models/schemas.py`）

### 修改任务处理流程

修改 `process_generation_task()` 函数，添加新的处理步骤。

### 添加新的配置选项

修改 `get_options()` 函数，添加新的选项。

## 注意事项

1. **异步处理**：生成任务使用后台任务，避免阻塞请求
2. **任务存储**：当前使用内存存储，生产环境应使用 Redis
3. **文件路径**：注意处理相对路径和绝对路径
4. **CORS**：开发环境允许所有来源，生产环境需要限制




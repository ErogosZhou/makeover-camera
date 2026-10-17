# 服务层

## 概述

服务层包含所有业务逻辑，负责与外部 API 交互和处理核心功能。

## 文件结构

```
services/
├── __init__.py              # 导出服务类
├── image_generator.py       # 图片生成服务
├── item_identifier.py       # 物品识别服务
├── product_matcher.py       # 商品匹配服务
└── cos_storage.py           # 腾讯云 COS 存储服务
```

## 服务说明

### 1. ImageGeneratorService - 图片生成服务

**文件**: `image_generator.py`

**功能**: 调用 Gemini 图片生成 API，基于原图生成改造后的效果图

**主要方法**:
- `generate()`: 生成效果图

**配置**:
- `IMAGE_GEN_API_KEY`: API 密钥
- `IMAGE_GEN_API_URL`: API 地址
- `IMAGE_GEN_MODEL`: 模型名称

**使用示例**:
```python
from services.image_generator import ImageGeneratorService
from models.schemas import RoomType, StyleType, BudgetLevel

service = ImageGeneratorService()
image_url = await service.generate(
    original_image_path="uploads/image.jpg",
    room_type=RoomType.LIVING_ROOM,
    style=StyleType.NORDIC,
    budget=BudgetLevel.MEDIUM,
    custom_prompt="希望多一些绿植"
)
```

**实现细节**:
- 使用 System Prompt 定义角色和约束
- 根据房间类型、风格、预算构建 User Prompt
- 将原图转为 base64 发送
- 解析响应中的图片（支持 base64 和 URL）
- 保存生成图片到本地

### 2. ItemIdentifierService - 物品识别服务

**文件**: `item_identifier.py`

**功能**: 对比原图和效果图，识别新增的软装物品

**主要方法**:
- `identify()`: 识别新增物品

**配置**:
- `VLLM_API_KEY`: API 密钥
- `VLLM_API_URL`: API 地址
- `VLLM_MODEL`: 模型名称

**使用示例**:
```python
from services.item_identifier import ItemIdentifierService

service = ItemIdentifierService()
items = await service.identify(
    generated_image_path="uploads/generated.png",
    original_image_path="uploads/original.jpg"
)
```

**实现细节**:
- 使用 System Prompt 定义识别规则
- 对比两张图片，找出新增物品
- 提取物品特征（名称、类别、颜色、材质等）
- 返回 JSON 格式的识别结果
- 支持 JSON 修复（处理不完整的响应）

**返回数据**:
- 物品名称、类别、描述
- 颜色、材质、风格
- 尺寸估计、价格估计
- 搜索关键词

### 3. ProductMatcherService - 商品匹配服务

**文件**: `product_matcher.py`

**功能**: 基于识别出的物品，搜索电商平台匹配商品

**主要方法**:
- `search_products()`: 搜索商品
- `match_products_for_item()`: 为物品匹配商品

**配置**:
- 拼多多：`PDD_CLIENT_ID`, `PDD_CLIENT_SECRET`, `PDD_PID`
- 大淘客：`DATAOKE_APP_KEY`, `DATAOKE_APP_SECRET`

**使用示例**:
```python
from services.product_matcher import ProductMatcherService
from models.schemas import IdentifiedItem

service = ProductMatcherService()
item = IdentifiedItem(...)
products = await service.match_products_for_item(
    item=item,
    generated_image_path="uploads/generated.png",
    limit=5
)
```

**实现细节**:
- 优先使用拼多多，备选大淘客
- 使用物品的搜索关键词进行搜索
- 解析商品信息（价格、图片、销量、佣金率）
- 按销量排序，返回前 N 个商品
- 生成推广链接

**支持的平台**:
- 拼多多多多进宝
- 大淘客（淘宝/京东）

### 4. COSStorageService - 腾讯云 COS 存储服务

**文件**: `cos_storage.py`

**功能**: 提供云存储服务，用于 Serverless 环境

**主要方法**:
- `upload_file()`: 上传文件
- `upload_from_url()`: 从 URL 下载并上传
- `get_presigned_url()`: 获取预签名 URL

**配置**:
- `COS_SECRET_ID`: Secret ID
- `COS_SECRET_KEY`: Secret Key
- `COS_BUCKET`: 存储桶名称
- `COS_REGION`: 区域

**使用示例**:
```python
from services.cos_storage import cos_storage

if cos_storage.enabled:
    url = await cos_storage.upload_file(
        file_content=image_bytes,
        filename="image.jpg",
        content_type="image/jpeg",
        folder="uploads"
    )
```

**实现细节**:
- 自动检测配置是否完整
- 如果未配置或 SDK 未安装，自动回退到本地存储
- 支持 CDN 加速域名
- 生成唯一文件名（UUID）

## 服务初始化

所有服务在 `api/routes.py` 中初始化：

```python
image_generator = ImageGeneratorService()
item_identifier = ItemIdentifierService()
product_matcher = ProductMatcherService()
```

## 错误处理

所有服务都有完善的错误处理：

1. **配置检查**: 检查 API 密钥是否配置
2. **异常捕获**: 捕获网络错误、超时等异常
3. **日志记录**: 使用 loguru 记录错误信息
4. **友好错误**: 返回友好的错误信息给用户

## 扩展开发

### 添加新的图片生成服务

1. 修改 `ImageGeneratorService` 类
2. 实现新的生成逻辑
3. 更新配置项

### 添加新的电商平台

1. 在 `ProductMatcherService` 中添加新的搜索方法
2. 实现平台特定的 API 调用
3. 解析平台返回的数据格式
4. 更新配置项

### 添加新的存储服务

1. 创建新的存储服务类（参考 `COSStorageService`）
2. 实现 `upload_file()` 等方法
3. 在 `routes.py` 中使用新服务

## 注意事项

1. **异步操作**: 所有服务方法都是异步的，使用 `async/await`
2. **超时设置**: HTTP 客户端设置了合理的超时时间
3. **资源清理**: 服务关闭时清理 HTTP 客户端
4. **配置检查**: 使用前检查配置是否完整
5. **错误处理**: 所有外部调用都有异常处理

## 依赖服务

- **httpx**: 异步 HTTP 客户端
- **loguru**: 日志记录
- **qcloud_cos**: 腾讯云 COS SDK（可选）




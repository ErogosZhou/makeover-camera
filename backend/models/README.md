# 数据模型

## 概述

数据模型模块定义了所有 API 请求和响应的数据结构，使用 Pydantic 进行数据验证和序列化。

## 文件结构

```
models/
├── __init__.py      # 导出模型
└── schemas.py       # 所有 Pydantic 模型定义
```

## 枚举类型

### RoomType - 房间类型

```python
class RoomType(str, Enum):
    LIVING_ROOM = "living_room"      # 客厅
    BEDROOM = "bedroom"              # 卧室
    STUDY = "study"                  # 书房
    BALCONY = "balcony"              # 阳台
    DINING_ROOM = "dining_room"      # 餐厅
    OTHER = "other"                  # 其他
```

### StyleType - 装修风格

```python
class StyleType(str, Enum):
    NORDIC = "nordic"                # 简约北欧
    JAPANESE = "japanese"            # 日式无印
    VINTAGE = "vintage"              # 复古中古
    MODERN_LUXURY = "modern_luxury"  # 轻奢现代
    NATURAL = "natural"              # 自然原木
    MINIMALIST = "minimalist"        # 极简主义
```

### BudgetLevel - 预算档位

```python
class BudgetLevel(str, Enum):
    LOW = "low"           # ¥300
    MEDIUM = "medium"     # ¥500
    HIGH = "high"         # ¥1000
    PREMIUM = "premium"   # ¥2000
```

### TaskStatus - 任务状态

```python
class TaskStatus(str, Enum):
    PENDING = "pending"              # 等待处理
    GENERATING = "generating"        # 生成效果图中
    IDENTIFYING = "identifying"      # 识别物品中
    MATCHING = "matching"            # 匹配商品中
    COMPLETED = "completed"          # 完成
    FAILED = "failed"                # 失败
```

## 请求模型

### GenerateRequest

生成请求模型（当前未使用，实际使用 Form 数据）

```python
class GenerateRequest(BaseModel):
    room_type: RoomType
    style: StyleType
    budget: BudgetLevel
    custom_prompt: Optional[str] = None
```

## 响应模型

### UploadResponse

图片上传响应

```python
class UploadResponse(BaseModel):
    success: bool
    image_id: str
    image_url: str
    message: str
```

### IdentifiedItem

识别出的物品

```python
class IdentifiedItem(BaseModel):
    id: str
    name: str                        # 物品名称
    category: str                    # 类别（纺织品/灯具/绿植等）
    description: str                 # 详细描述
    color: Optional[str] = None      # 颜色
    material: Optional[str] = None   # 材质
    style: Optional[str] = None      # 风格
    size_estimate: Optional[str] = None  # 估计尺寸
    price_estimate: Optional[str] = None # 估计价格区间
    search_keywords: List[str] = []  # 搜索关键词
```

### MatchedProduct

匹配到的商品

```python
class MatchedProduct(BaseModel):
    id: str
    name: str                        # 商品名称
    price: float                     # 价格
    original_price: Optional[float] = None  # 原价
    image_url: str                   # 商品图片
    shop_name: Optional[str] = None  # 店铺名
    sales: Optional[int] = None      # 销量
    commission_rate: Optional[float] = None  # 佣金率
    affiliate_link: Optional[str] = None    # 推广链接
    similarity_score: Optional[float] = None # 相似度评分
    platform: str = "taobao"         # 平台（taobao/jd/pdd）
```

### ShoppingItem

购物清单项

```python
class ShoppingItem(BaseModel):
    identified_item: IdentifiedItem  # 识别出的物品
    matched_products: List[MatchedProduct] = []  # 匹配到的商品列表
```

### GenerationResult

生成结果

```python
class GenerationResult(BaseModel):
    task_id: str
    status: TaskStatus
    original_image_url: str          # 原图URL
    generated_image_url: Optional[str] = None  # 生成的效果图URL
    shopping_list: List[ShoppingItem] = []     # 购物清单
    total_estimated_price: Optional[float] = None  # 总预估价格
    created_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
```

### TaskStatusResponse

任务状态响应

```python
class TaskStatusResponse(BaseModel):
    task_id: str
    status: TaskStatus
    progress: int                    # 进度百分比 (0-100)
    message: str
    result: Optional[GenerationResult] = None  # 完成时包含结果
```

### OptionsResponse

配置选项响应

```python
class OptionsResponse(BaseModel):
    room_types: List[dict]           # 房间类型列表
    styles: List[StyleOption]         # 风格选项列表
    budgets: List[BudgetOption]      # 预算选项列表
```

### StyleOption

风格选项

```python
class StyleOption(BaseModel):
    value: str
    label: str
    description: str
    preview_image: Optional[str] = None
```

### BudgetOption

预算选项

```python
class BudgetOption(BaseModel):
    value: str
    label: str
    amount: int                      # 金额
    description: str
```

## 使用示例

### 创建请求模型

```python
from models.schemas import GenerateRequest, RoomType, StyleType, BudgetLevel

request = GenerateRequest(
    room_type=RoomType.LIVING_ROOM,
    style=StyleType.NORDIC,
    budget=BudgetLevel.MEDIUM,
    custom_prompt="希望多一些绿植"
)
```

### 创建响应模型

```python
from models.schemas import UploadResponse

response = UploadResponse(
    success=True,
    image_id="uuid-123",
    image_url="/uploads/image.jpg",
    message="上传成功"
)
```

### 数据验证

Pydantic 会自动验证数据类型和约束：

```python
# 如果数据不符合模型定义，会抛出 ValidationError
try:
    item = IdentifiedItem(
        id="1",
        name="地毯",
        category="纺织品",
        description="..."
    )
except ValidationError as e:
    print(e)
```

## 扩展开发

### 添加新的枚举类型

```python
class NewEnum(str, Enum):
    VALUE1 = "value1"
    VALUE2 = "value2"
```

### 添加新的模型

```python
class NewModel(BaseModel):
    field1: str
    field2: Optional[int] = None
    field3: List[str] = []
```

### 添加字段验证

```python
from pydantic import Field, validator

class NewModel(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    age: int = Field(..., ge=0, le=150)
    
    @validator('name')
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError('名称不能为空')
        return v
```

## 注意事项

1. **类型注解**：所有字段都应该有类型注解
2. **可选字段**：使用 `Optional[T]` 表示可选字段
3. **默认值**：为可选字段设置合理的默认值
4. **验证**：利用 Pydantic 的验证功能确保数据正确性
5. **序列化**：模型自动支持 JSON 序列化和反序列化




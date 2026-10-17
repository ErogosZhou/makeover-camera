"""
Pydantic 数据模型定义
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Any
from enum import Enum
from datetime import datetime


# ============ 枚举类型 ============

class RoomType(str, Enum):
    """房间类型"""
    LIVING_ROOM = "living_room"      # 客厅
    BEDROOM = "bedroom"              # 卧室
    STUDY = "study"                  # 书房
    BALCONY = "balcony"              # 阳台
    DINING_ROOM = "dining_room"      # 餐厅
    OTHER = "other"                  # 其他


class StyleType(str, Enum):
    """装修风格"""
    NORDIC = "nordic"                # 简约北欧
    JAPANESE = "japanese"            # 日式无印
    VINTAGE = "vintage"              # 复古中古
    MODERN_LUXURY = "modern_luxury"  # 轻奢现代
    NATURAL = "natural"              # 自然原木
    MINIMALIST = "minimalist"        # 极简主义
    BOHO = "boho"                    # 波西米亚
    MODERN_MINIMALIST = "modern_minimalist"  # 现代极简
    SCANDINAVIAN = "scandinavian"    # 斯堪的纳维亚
    COASTAL = "coastal"              # 海岸风
    INDUSTRIAL = "industrial"        # 工业风


class BudgetLevel(str, Enum):
    """预算档位"""
    LOW = "low"           # ¥300
    MEDIUM = "medium"     # ¥500
    HIGH = "high"         # ¥1000
    PREMIUM = "premium"   # ¥2000
    B200 = "200"          # $200
    B400 = "400"          # $400
    B800 = "800"          # $800
    B1500 = "1500"        # $1500


class TaskStatus(str, Enum):
    """任务状态"""
    PENDING = "pending"              # 等待处理
    GENERATING = "generating"        # 生成效果图中
    IDENTIFYING = "identifying"      # 识别物品中
    MATCHING = "matching"            # 匹配商品中
    COMPLETED = "completed"          # 完成
    FAILED = "failed"                # 失败


# ============ 请求模型 ============

class GenerateRequest(BaseModel):
    """生成请求"""
    room_type: RoomType = Field(default=RoomType.LIVING_ROOM, description="房间类型")
    style: StyleType = Field(default=StyleType.NORDIC, description="装修风格")
    budget: BudgetLevel = Field(default=BudgetLevel.MEDIUM, description="预算档位")
    custom_prompt: Optional[str] = Field(default=None, max_length=500, description="自定义需求描述")


# ============ 响应模型 ============

class UploadResponse(BaseModel):
    """图片上传响应"""
    success: bool
    image_id: str
    image_url: str
    message: str


class IdentifiedItem(BaseModel):
    """识别出的物品"""
    id: str
    name: str                        # 物品名称，如"编织地毯"
    category: str                    # 类别，如"纺织品"
    description: str                 # 详细描述
    color: Optional[str] = None      # 颜色
    material: Optional[str] = None   # 材质
    style: Optional[str] = None      # 风格
    size_estimate: Optional[str] = None  # 估计尺寸
    price_estimate: Optional[str] = None # 估计价格区间
    search_keywords: List[str] = []  # 搜索关键词


class MatchedProduct(BaseModel):
    """匹配到的商品"""
    id: str
    name: str                        # 商品名称
    price: float                     # 价格
    original_price: Optional[float] = None  # 原价
    image_url: str                   # 商品图片
    shop_name: Optional[str] = None  # 店铺名
    sales: Optional[int] = None      # 销量
    commission_rate: Optional[float] = None  # 佣金率
    affiliate_link: Optional[str] = None    # 推广链接（淘口令或短链）
    similarity_score: Optional[float] = None # 与效果图物品的相似度评分
    platform: str = "taobao"         # 平台：taobao/jd/pdd


class ShoppingItem(BaseModel):
    """购物清单项"""
    identified_item: IdentifiedItem  # 识别出的物品
    matched_products: List[MatchedProduct] = []  # 匹配到的商品列表


class GenerationResult(BaseModel):
    """生成结果"""
    task_id: str
    status: TaskStatus
    original_image_url: str          # 原图URL
    generated_image_url: Optional[str] = None  # 生成的效果图URL(完整图)
    thumbnail_url: Optional[str] = None  # 🆕 缩略图URL(快速加载)
    generation_prompt: Optional[str] = None    # VLLM生成的图生图prompt(用于打字机展示)
    shopping_list: List[ShoppingItem] = []     # 购物清单
    total_estimated_price: Optional[float] = None  # 总预估价格
    # AI 空间分析结果：流式文本或结构化字典，保持兼容
    space_analysis: Optional[Any] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None


class TaskStatusResponse(BaseModel):
    """任务状态响应"""
    task_id: str
    status: TaskStatus
    progress: int = Field(ge=0, le=100, description="进度百分比")
    message: str
    result: Optional[GenerationResult] = None


# ============ 配置选项响应 ============

class StyleOption(BaseModel):
    """风格选项"""
    value: str
    label: str
    description: str
    preview_image: Optional[str] = None


class BudgetOption(BaseModel):
    """预算选项"""
    value: str
    label: str
    amount: int
    description: str


class OptionsResponse(BaseModel):
    """配置选项响应"""
    room_types: List[dict]
    styles: List[StyleOption]
    budgets: List[BudgetOption]

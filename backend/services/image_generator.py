"""
图片生成服务
支持多个生图提供商：Gemini、Seedream (豆包)

设计理念：
- 基于专业室内设计方法论
- 结构化的空间分析与改造策略
- 强调视觉冲击力与可落地性
- 可配置切换不同生图服务
"""
import httpx
import base64
import os
import uuid
import asyncio
import json
from typing import Optional, Dict, Any
from loguru import logger
from enum import Enum

from config.settings import settings
from models.schemas import StyleType, BudgetLevel, RoomType
from services.prompts_i18n import get_prompts


class ImageGenProvider(str, Enum):
    """图片生成提供商"""
    GEMINI = "gemini"
    SEEDREAM = "seedream"


class ImageGeneratorService:
    """图片生成服务 - 大师级室内设计"""
    
    # ============================================================
    # SYSTEM PROMPT - 专业室内设计师的思维方式
    # ============================================================
    
    SYSTEM_PROMPT = """你是一位拥有20年经验的资深室内软装设计师，曾为顶级酒店和高端住宅完成过数百个项目。

## 你的设计哲学

1. **空间优先**：先读懂空间的光线、比例、动线，再决定如何改造
2. **克制美学**：好的设计是"刚刚好"，每一件物品都有存在的理由
3. **层次构建**：通过地面→坐卧→墙面→光线四个层次建立空间纵深
4. **材质对话**：软与硬、粗与细、亮与哑之间需要平衡
5. **可落地性**：所有建议的物品都是普通人能在主流电商平台买到的

## 你的工作方式

分析原图时，你会快速评估：
- 主光源方向和光线质量（冷/暖、强/弱）
- 空间比例（层高、面宽、进深）
- 现有色调基底（墙面、地板、主要家具）
- 视觉重心和动线起点

改造时，你会遵循：
- 60-30-10 色彩法则（主色-辅助色-点缀色）
- 三角构图原则（物品摆放形成稳定视觉结构）
- 奇数法则（同类物品用1/3/5件组合）
- 高低错落（创造垂直方向的节奏感）

## 绝对约束

- 不改变建筑结构、墙面颜色、地板、门窗
- 只通过添加软装实现改造
- 生成真实、自然的室内照片效果
- 光影必须与原图环境一致
- 物品比例必须符合真实尺寸"""

    # ============================================================
    # 风格体系 - 专业设计语言，非文学性表达
    # ============================================================
    
    STYLE_SYSTEM = {
        StyleType.NORDIC: {
            "name": "北欧风格",
            "design_principle": "功能主义与自然光的最大化利用",
            "color_strategy": {
                "base": "大面积白色或浅灰（色温偏冷）",
                "secondary": "原木色、米色、浅驼色（增加温度）",
                "accent": "低饱和度的莫兰迪色系点缀（雾霾蓝、灰粉、橄榄绿）"
            },
            "material_palette": ["白橡木", "亚麻", "羊毛", "陶瓷", "黄铜（少量）"],
            "spatial_technique": [
                "保持大面积留白，避免堆砌",
                "用线条感强的物品强调几何秩序",
                "绿植作为唯一的高饱和色彩来源"
            ],
            "lighting_approach": "最大化自然光，辅以暖色温（2700K-3000K）的氛围灯",
            "key_items": ["几何图案地毯", "亚麻质感抱枕", "细腿落地灯", "陶瓷花瓶", "编织收纳筐"],
            "avoid": ["深色大面积家具", "繁复花纹", "过多装饰品", "冷白光源"]
        },
        
        StyleType.JAPANESE: {
            "name": "日式风格",
            "design_principle": "侘寂美学——在不完美中寻找宁静",
            "color_strategy": {
                "base": "温暖的米白、象牙白",
                "secondary": "原木色（偏红的胡桃木或偏黄的白蜡木）",
                "accent": "黑色线条勾勒、一抹绿植"
            },
            "material_palette": ["实木", "棉麻", "藤编", "和纸", "粗陶"],
            "spatial_technique": [
                "强调水平线条，压低视觉重心",
                "大量留白，呼吸感",
                "物品摆放讲究不对称的平衡"
            ],
            "lighting_approach": "柔和的漫射光，避免直射强光，推荐纸质灯罩",
            "key_items": ["低矮茶几", "蒲团/懒人沙发", "枯枝插花", "木质托盘", "棉麻盖毯"],
            "avoid": ["高饱和色彩", "金属光泽", "复杂图案", "过高的家具"]
        },
        
        StyleType.VINTAGE: {
            "name": "复古中古风格",
            "design_principle": "时间沉淀的质感与故事性",
            "color_strategy": {
                "base": "焦糖色、咖啡色、墨绿色等深沉色调",
                "secondary": "奶油色、驼色中和厚重感",
                "accent": "黄铜金、琥珀色、酒红色提亮"
            },
            "material_palette": ["胡桃木", "丝绒", "黄铜", "皮革", "玻璃"],
            "spatial_technique": [
                "混搭不同年代的经典设计单品",
                "用镜面和金属反射增加层次",
                "书籍、老物件营造生活痕迹"
            ],
            "lighting_approach": "暖黄光（2400K-2700K），多点光源，避免均匀照明",
            "key_items": ["丝绒抱枕", "黄铜台灯", "复古挂画", "皮质收纳", "老式摆钟"],
            "avoid": ["现代极简家具", "冷色调", "塑料材质", "LED白光"]
        },
        
        StyleType.MODERN_LUXURY: {
            "name": "现代轻奢风格",
            "design_principle": "精简的奢华——少而精，重品质感",
            "color_strategy": {
                "base": "高级灰、奶咖色、大地色系",
                "secondary": "黑色增加分量感",
                "accent": "金色/香槟金点缀（控制在5%以内）"
            },
            "material_palette": ["大理石纹理", "金属", "皮革", "丝绒", "玻璃"],
            "spatial_technique": [
                "线条利落，拒绝繁复",
                "通过材质质感而非数量体现价值",
                "对称构图传递秩序感"
            ],
            "lighting_approach": "分层照明：主灯+轮廓光+重点照明，色温3000K-3500K",
            "key_items": ["大理石纹托盘", "金属边几", "皮质抱枕", "艺术装饰画", "水晶/玻璃摆件"],
            "avoid": ["廉价感的金色", "过多装饰", "花哨图案", "不协调的材质混搭"]
        },
        
        StyleType.NATURAL: {
            "name": "自然风格",
            "design_principle": "将户外引入室内，构建城市中的自然栖息地",
            "color_strategy": {
                "base": "大地色系——沙色、泥土色、岩石灰",
                "secondary": "各种层次的绿色",
                "accent": "陶土红、日落橙（源自自然的暖色）"
            },
            "material_palette": ["原木", "藤编", "麻绳", "粗陶", "干花"],
            "spatial_technique": [
                "绿植是主角，分布在不同高度层次",
                "自然材质的粗糙质感是特色",
                "避免过于精致，保留手工感"
            ],
            "lighting_approach": "模拟自然光的温暖感，植物灯可兼顾照明与养护",
            "key_items": ["大型绿植（琴叶榕/龟背竹）", "藤编收纳", "麻质地毯", "陶土花盆", "木质置物架"],
            "avoid": ["人造感强的材质", "高光泽表面", "过于工业的元素", "塑料制品"]
        },
        
        StyleType.MINIMALIST: {
            "name": "极简风格",
            "design_principle": "Less is more——每一件物品都必须证明其存在价值",
            "color_strategy": {
                "base": "纯白或浅灰，大面积单色",
                "secondary": "黑色或深灰作为锚点",
                "accent": "几乎不用，或仅用一处艺术品色彩"
            },
            "material_palette": ["哑光涂料", "水泥质感", "金属", "玻璃", "少量木质"],
            "spatial_technique": [
                "隐藏收纳，保持表面整洁",
                "负空间（留白）是设计的一部分",
                "用光影变化代替装饰"
            ],
            "lighting_approach": "建筑化照明，隐藏光源，用光线塑造空间",
            "key_items": ["纯色地毯", "几何抱枕", "极简落地灯", "单支绿植", "无框装饰画"],
            "avoid": ["任何多余的装饰", "复杂图案", "过多色彩", "视觉噪音"]
        }
    }

    # ============================================================
    # 预算策略 - 基于设计完整性而非物品数量
    # ============================================================
    
    BUDGET_STRATEGY = {
        BudgetLevel.LOW: {
            "name": "点睛改造",
            "budget_range": "300元左右",
            "philosophy": "用最少的改动实现最大的视觉提升",
            "focus": "找到空间最需要填补的一个视觉空缺",
            "approach": [
                "优先解决最显眼的问题点",
                "选择1-2件有存在感的单品",
                "颜色上与现有空间形成呼应或对比"
            ],
            "typical_items": "一块地毯 或 一组抱枕 或 一盏灯 或 一个大型绿植"
        },
        
        BudgetLevel.MEDIUM: {
            "name": "氛围升级",
            "budget_range": "500元左右",
            "philosophy": "构建完整的视觉焦点区域",
            "focus": "打造一个让人眼前一亮的核心场景",
            "approach": [
                "地面层+坐卧层的组合搭配",
                "建立主次分明的物品关系",
                "通过色彩将不同物品关联成整体"
            ],
            "typical_items": "地毯 + 抱枕组合 + 落地灯/绿植 + 小摆件"
        },
        
        BudgetLevel.HIGH: {
            "name": "质感重塑",
            "budget_range": "1000元左右",
            "philosophy": "全方位提升空间的层次感与精致度",
            "focus": "从四个层次全面优化空间体验",
            "approach": [
                "地面层-中间层-墙面层-光线层的完整构建",
                "材质混搭创造丰富的触感体验",
                "光线设计营造氛围感"
            ],
            "typical_items": "中型地毯 + 抱枕套装 + 盖毯 + 灯具组合 + 挂画 + 绿植组合 + 桌面摆件"
        },
        
        BudgetLevel.PREMIUM: {
            "name": "风格焕新",
            "budget_range": "2000元左右",
            "philosophy": "系统性地重新定义空间气质",
            "focus": "让空间呈现出完整、统一的设计语言",
            "approach": [
                "大件软装奠定空间基调",
                "多层次光源系统",
                "艺术品与绿植的整体规划",
                "角落与细节的完整处理"
            ],
            "typical_items": "大尺寸地毯 + 窗帘/遮光帘 + 多个灯具 + 整套抱枕盖毯 + 挂画组合 + 大型绿植 + 置物系统 + 香氛"
        }
    }

    # ============================================================
    # 房间特性 - 不同空间的设计考量
    # ============================================================
    
    ROOM_CONTEXT = {
        RoomType.LIVING_ROOM: {
            "name": "客厅",
            "primary_function": "社交、休闲、展示",
            "design_focus": [
                "沙发区是绝对的视觉中心",
                "需要兼顾会客的正式感和日常的舒适感",
                "茶几/边几区域是摆件的主要展示区"
            ],
            "common_issues": ["沙发背景墙空旷", "茶几杂乱", "缺乏层次感", "光线单一"]
        },
        
        RoomType.BEDROOM: {
            "name": "卧室",
            "primary_function": "睡眠、私密放松",
            "design_focus": [
                "床头是视觉焦点",
                "强调包裹感和安全感",
                "光线需要可调节，满足不同场景"
            ],
            "common_issues": ["床头空旷", "床品单调", "缺乏阅读灯", "没有舒适角落"]
        },
        
        RoomType.STUDY: {
            "name": "书房",
            "primary_function": "工作、学习、思考",
            "design_focus": [
                "桌面是功能核心",
                "需要平衡专注感与舒适感",
                "收纳与展示的平衡"
            ],
            "common_issues": ["桌面杂乱", "灯光不足", "缺乏个性", "没有放松角落"]
        },
        
        RoomType.BALCONY: {
            "name": "阳台",
            "primary_function": "休闲、绿植、洗晒",
            "design_focus": [
                "利用自然光优势",
                "绿植是天然的设计元素",
                "创造一个逃离感的角落"
            ],
            "common_issues": ["沦为杂物间", "缺乏休憩空间", "绿植杂乱无章"]
        },
        
        RoomType.DINING_ROOM: {
            "name": "餐厅",
            "primary_function": "用餐、家庭聚会",
            "design_focus": [
                "餐桌是绝对中心",
                "吊灯/光线对氛围影响巨大",
                "餐边柜是展示与收纳的关键"
            ],
            "common_issues": ["餐桌空旷", "光线不聚焦", "墙面单调"]
        },
        
        RoomType.OTHER: {
            "name": "其他空间",
            "primary_function": "视具体情况而定",
            "design_focus": ["分析空间现有功能", "找出最需要改善的点"],
            "common_issues": ["需要根据图片具体分析"]
        }
    }

    def __init__(self):
        # 根据配置选择提供商
        self.provider = settings.IMAGE_GEN_PROVIDER.lower()

        if self.provider == ImageGenProvider.SEEDREAM:
            self.api_key = settings.SEEDREAM_API_KEY
            self.api_url = settings.SEEDREAM_API_URL
            self.model = settings.SEEDREAM_MODEL
        else:
            # 默认使用 Gemini，兼容旧配置
            self.api_key = settings.GEMINI_API_KEY or settings.IMAGE_GEN_API_KEY
            self.api_url = settings.GEMINI_API_URL or settings.IMAGE_GEN_API_URL
            self.model = settings.GEMINI_MODEL or settings.IMAGE_GEN_MODEL

        self._client: Optional[httpx.AsyncClient] = None
        logger.info(f"图片生成服务初始化: provider={self.provider}, model={self.model}")
    
    async def _get_client(self) -> httpx.AsyncClient:
        """获取HTTP客户端"""
        if self._client is None:
            timeout = httpx.Timeout(30.0, connect=30.0, read=300.0)
            self._client = httpx.AsyncClient(timeout=timeout, trust_env=False)
        return self._client
    
    def get_design_brief(
        self,
        room_type: RoomType,
        style: StyleType,
        budget: BudgetLevel
    ) -> Dict[str, Any]:
        """
        生成设计简报 - 可在前端展示给用户
        这个方法可以在任务开始时立即调用，让用户看到AI的"思考过程"
        """
        style_info = self.STYLE_SYSTEM[style]
        budget_info = self.BUDGET_STRATEGY[budget]
        room_info = self.ROOM_CONTEXT[room_type]
        
        return {
            "style": {
                "name": style_info["name"],
                "principle": style_info["design_principle"],
                "colors": style_info["color_strategy"],
                "key_items": style_info["key_items"][:4]  # 只展示前4个
            },
            "budget": {
                "name": budget_info["name"],
                "range": budget_info["budget_range"],
                "philosophy": budget_info["philosophy"]
            },
            "room": {
                "name": room_info["name"],
                "focus": room_info["design_focus"][0]  # 最重要的一条
            }
        }
    
    def _build_user_prompt(
        self,
        room_type: RoomType,
        style: StyleType,
        budget: BudgetLevel,
        custom_prompt: Optional[str] = None,
        space_analysis: Optional[Any] = None,
        image_prompt: Optional[str] = None,
        lang: str = "zh"
    ) -> str:
        """构建专业级 User Prompt，可结合空间分析结果"""

        if lang == "en":
            prompts = get_prompts("image_generator", "en")
            style_system = prompts.get("style_system", {})
            budget_strategy = prompts.get("budget_strategy", {})
            room_context = prompts.get("room_context", {})

            style_info = style_system.get(style.value) or next(iter(style_system.values()), {})
            budget_info = budget_strategy.get(budget.value) or next(iter(budget_strategy.values()), {})
            room_info = room_context.get(room_type.value, {"name": room_type.value, "focus": ""})

            space_analysis_section = ""
            if space_analysis:
                if isinstance(space_analysis, str):
                    space_analysis_section = f"## Space Analysis\n{space_analysis}"
                else:
                    space_analysis_section = f"## Space Analysis\n{space_analysis}"

            custom_prompt_section = ""
            if custom_prompt:
                custom_prompt_section = f"## User Notes\n{custom_prompt}"

            return prompts.get("user_prompt_template", "").format(
                room_name=room_info.get("name", room_type.value),
                space_analysis_section=space_analysis_section,
                style_name=style_info.get("name", style.value),
                design_principle=style_info.get("design_principle", ""),
                color_base=style_info.get("color_strategy", {}).get("base", ""),
                color_secondary=style_info.get("color_strategy", {}).get("secondary", ""),
                color_accent=style_info.get("color_strategy", {}).get("accent", ""),
                materials=", ".join(style_info.get("material_palette", [])),
                key_items=", ".join(style_info.get("key_items", [])),
                avoid_items=", ".join(style_info.get("avoid", [])),
                budget_name=budget_info.get("name", ""),
                budget_range=budget_info.get("budget_range", ""),
                budget_philosophy=budget_info.get("philosophy", ""),
                typical_items=budget_info.get("typical_items", ""),
                custom_prompt_section=custom_prompt_section
            )

        style_info = self.STYLE_SYSTEM[style]
        budget_info = self.BUDGET_STRATEGY[budget]
        room_info = self.ROOM_CONTEXT[room_type]

        prompt = f"""## 任务
基于这张{room_info["name"]}照片，生成软装改造后的效果图。"""

        # 如果有空间分析，优先使用 AI 对这个具体空间的理解
        if space_analysis:
            # 兼容字符串流式分析和旧的结构化结果
            if isinstance(space_analysis, str):
                prompt += f"""

## 针对这个空间的 AI 分析（流式文本）
{space_analysis}
"""
            else:
                prompt += f"""

## 针对这个空间的 AI 分析

空间特征：
- 光线：{space_analysis.get("space_reading", {}).get("light", "未知")}
- 比例：{space_analysis.get("space_reading", {}).get("proportion", "未知")}
- 现有基调：{space_analysis.get("space_reading", {}).get("base_tone", "未知")}

诊断问题：{space_analysis.get("diagnosis", {}).get("main_issue", "未知")}

改造方案：
- 视觉焦点：{space_analysis.get("solution", {}).get("focal_point", "未知")}
- 快速见效：{space_analysis.get("solution", {}).get("quick_win", "未知")}
- 配色建议：{space_analysis.get("solution", {}).get("color_advice", "未知")}
- 推荐添加：{", ".join(space_analysis.get("solution", {}).get("key_additions", []))}
"""

        # 如果有模型标记的生图提示词，追加以提高契合度
        if image_prompt:
            prompt += f"""

## AI 生成提示词（模型标记）
{image_prompt}
"""
        
        prompt += f"""

## 目标风格：{style_info["name"]}
核心原则：{style_info["design_principle"]}

色彩策略：
- 主色调(60%)：{style_info["color_strategy"]["base"]}
- 辅助色(30%)：{style_info["color_strategy"]["secondary"]}
- 点缀色(10%)：{style_info["color_strategy"]["accent"]}

材质语言：{", ".join(style_info["material_palette"])}

推荐单品：{", ".join(style_info["key_items"])}

避免：{", ".join(style_info["avoid"])}

## 改造档位：{budget_info["name"]}（{budget_info["budget_range"]}）
{budget_info["philosophy"]}

参考物品组合：{budget_info["typical_items"]}

## 输出要求
直接生成改造后的效果图。确保：
1. 新增物品的尺寸比例真实合理
2. 光影与原图环境完全一致
3. 整体效果自然，像真实拍摄的照片
4. 所有物品都是可以在电商平台购买的真实商品"""

        if custom_prompt:
            prompt += f"\n\n## 用户特别要求\n{custom_prompt}"
        
        return prompt
    
    def _get_media_type(self, image_path: str) -> str:
        """获取图片的媒体类型"""
        ext = os.path.splitext(image_path)[1].lower()
        media_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.webp': 'image/webp',
            '.gif': 'image/gif'
        }
        return media_types.get(ext, 'image/jpeg')

    def _build_seedream_prompt(
        self,
        room_type: RoomType,
        style: StyleType,
        budget: BudgetLevel,
        custom_prompt: Optional[str] = None,
        lang: str = "zh"
    ) -> str:
        """
        为 Seedream 构建优化的提示词
        Seedream 图生图模型，提示词需要强调保持原图结构，只添加家具软装
        """
        style_info = self.STYLE_SYSTEM.get(style, self.STYLE_SYSTEM[StyleType.NORDIC])
        budget_info = self.BUDGET_STRATEGY.get(budget, self.BUDGET_STRATEGY[BudgetLevel.MEDIUM])
        room_info = self.ROOM_CONTEXT.get(room_type, self.ROOM_CONTEXT[RoomType.LIVING_ROOM])

        if lang == "en":
            prompt = f"""Based on this reference image, create a {style_info["name"]} style {room_info["name"]} interior design.

IMPORTANT: Keep the exact same room structure, wall colors, floor texture, windows and doors from the reference image. Only add furniture and soft furnishings.

Add these items in {style_info["name"]} style:
- {", ".join(style_info["key_items"][:4])}
- Materials: {", ".join(style_info["material_palette"][:3])}

Photography style: professional interior design photo, photorealistic, natural lighting, same camera angle as reference"""
        else:
            prompt = f"""基于参考图，为这个{room_info["name"]}添加{style_info["name"]}风格的家具和软装。

重要：完全保持参考图中的房间结构、墙面颜色、地板纹理、窗户和门的位置不变，只添加家具和装饰品。

添加{style_info["name"]}风格的：
- {", ".join(style_info["key_items"][:4])}
- 材质：{", ".join(style_info["material_palette"][:3])}

摄影风格：专业室内设计照片，真实感，自然光线，保持与参考图相同的拍摄角度"""

        if custom_prompt:
            prompt += f"\n\n{custom_prompt}"

        return prompt
    
    async def generate(
        self,
        original_image_path: str,
        room_type: RoomType,
        style: StyleType,
        budget: BudgetLevel,
        custom_prompt: Optional[str] = None,
        space_analysis: Optional[Any] = None,
        image_prompt: Optional[str] = None,
        lang: str = "zh",
        progress_callback=None
    ) -> Optional[str]:
        """
        生成改造效果图 - 根据配置自动选择提供商

        Args:
            original_image_path: 原图路径
            room_type: 房间类型
            style: 装修风格
            budget: 预算档位
            custom_prompt: 自定义需求
            space_analysis: AI空间分析结果（可选，用于增强生成效果）
            progress_callback: 可选的进度回调函数，接收参数 (percentage, message)

        Returns:
            生成图片的本地路径，失败返回None
        """
        if not self.api_key:
            logger.error("图片生成服务未配置API密钥")
            raise ValueError(
                "图片生成服务未配置。请在 .env 文件中设置对应的 API Key"
            )

        # 根据提供商选择不同的生成方法
        if self.provider == ImageGenProvider.SEEDREAM:
            return await self._generate_with_seedream(
                original_image_path, room_type, style, budget, custom_prompt, space_analysis, image_prompt, lang, progress_callback
            )
        else:
            return await self._generate_with_gemini(
                original_image_path, room_type, style, budget, custom_prompt, space_analysis, image_prompt, lang
            )

    async def _generate_with_seedream(
        self,
        original_image_path: str,
        room_type: RoomType,
        style: StyleType,
        budget: BudgetLevel,
        custom_prompt: Optional[str] = None,
        space_analysis: Optional[Any] = None,
        image_prompt: Optional[str] = None,
        lang: str = "zh",
        progress_callback=None
    ) -> Optional[str]:
        """使用 Seedream (豆包) 图生图（支持流式进度）"""
        user_prompt = self._build_seedream_prompt(room_type, style, budget, custom_prompt, lang)
        logger.info(f"[Seedream] Prompt: {user_prompt[:200]}...")

        # 读取原图并转为 base64
        with open(original_image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode()
        media_type = self._get_media_type(original_image_path)
        image_base64 = f"data:{media_type};base64,{image_data}"

        client = await self._get_client()

        # Seedream 图生图 API 格式（当前模型仅支持非流式）
        request_body = {
            "model": self.model,
            "prompt": user_prompt,
            "image": image_base64,  # 传入参考图
            "response_format": "url",
            "size": "2K",
            "watermark": False
        }

        logger.info(f"[Seedream] 调用API: {self.api_url}/images/generations, model={self.model}")

        max_retries = 3
        retry_delay = 5
        last_error = None

        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    logger.info(f"[Seedream] 第 {attempt + 1} 次重试...")

                response = await client.post(
                    f"{self.api_url}/images/generations",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json=request_body,
                    timeout=120.0
                )
                logger.info(f"[Seedream] API响应状态码: {response.status_code}")

                if response.status_code != 200:
                    raise Exception(f"[Seedream] API调用失败: {response.status_code} - {response.text}")

                result = response.json()
                data = result.get("data", [])
                image_url = data[0].get("url") if data else None

                if image_url:
                    logger.info("[Seedream] 图片生成完成")
                    if progress_callback:
                        await progress_callback(100, "图片生成完成")
                    return await self._download_and_save_image(image_url)
                else:
                    logger.error(f"[Seedream] 响应中未获取到图片URL: {result}")
                    return None

            except httpx.TimeoutException as e:
                logger.warning(f"[Seedream] API调用超时 (尝试 {attempt + 1}/{max_retries})")
                last_error = e
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay * (attempt + 1))
                    continue
            except httpx.ConnectError as e:
                logger.warning(f"[Seedream] API连接失败 (尝试 {attempt + 1}/{max_retries})")
                last_error = e
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay * (attempt + 1))
                    continue
            except Exception as e:
                if "API调用失败" in str(e):
                    raise
                logger.warning(f"[Seedream] 图片生成失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                last_error = e
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay * (attempt + 1))
                    continue

        if isinstance(last_error, httpx.TimeoutException):
            raise Exception(f"[Seedream] 图片生成超时（已重试{max_retries}次）")
        elif isinstance(last_error, httpx.ConnectError):
            raise Exception(f"[Seedream] 无法连接到服务（已重试{max_retries}次）")
        else:
            raise Exception(f"[Seedream] 图片生成失败（已重试{max_retries}次）: {str(last_error)}")

    async def _generate_with_gemini(
        self,
        original_image_path: str,
        room_type: RoomType,
        style: StyleType,
        budget: BudgetLevel,
        custom_prompt: Optional[str] = None,
        space_analysis: Optional[Any] = None,
        image_prompt: Optional[str] = None,
        lang: str = "zh"
    ) -> Optional[str]:
        """使用 Gemini 生成图片（原有逻辑）"""
        user_prompt = self._build_user_prompt(room_type, style, budget, custom_prompt, space_analysis, image_prompt, lang)
        logger.info(f"[Gemini] User Prompt: {user_prompt[:200]}...")

        # 读取原图并转为base64
        with open(original_image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode()

        media_type = self._get_media_type(original_image_path)

        client = await self._get_client()

        # 构建请求
        system_prompt = self.SYSTEM_PROMPT
        if lang == "en":
            system_prompt = get_prompts("image_generator", "en").get("system_prompt", self.SYSTEM_PROMPT)

        request_body = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{media_type};base64,{image_data}"
                            }
                        },
                        {
                            "type": "text",
                            "text": user_prompt
                        }
                    ]
                }
            ],
            "max_tokens": 4096
        }

        logger.info(f"[Gemini] 调用API: {self.api_url}/chat/completions, model={self.model}")

        # 重试逻辑
        max_retries = 3
        retry_delay = 5
        last_error = None

        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    logger.info(f"[Gemini] 第 {attempt + 1} 次重试...")

                response = await client.post(
                    f"{self.api_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json=request_body
                )

                logger.info(f"[Gemini] API响应状态码: {response.status_code}")

                if response.status_code == 200:
                    result = response.json()
                    logger.debug(f"[Gemini] API响应: {result}")

                    choices = result.get("choices", [])
                    if not choices:
                        logger.error("[Gemini] API响应中没有choices")
                        return None

                    message = choices[0].get("message", {})
                    content = message.get("content", [])

                    if isinstance(content, str):
                        logger.warning(f"[Gemini] 模型返回文本而非图片: {content[:200]}")
                        if "data:image" in content:
                            import re
                            match = re.search(r'data:image/[^;]+;base64,([A-Za-z0-9+/=]+)', content)
                            if match:
                                image_base64 = match.group(1)
                                return await self._save_generated_image(image_base64)
                        return None

                    for item in content:
                        if isinstance(item, dict):
                            if item.get("type") == "image_url":
                                image_url = item.get("image_url", {}).get("url", "")
                                if image_url.startswith("data:image"):
                                    base64_data = image_url.split(",", 1)[1] if "," in image_url else ""
                                    if base64_data:
                                        return await self._save_generated_image(base64_data)
                            elif item.get("type") == "image":
                                if "data" in item:
                                    return await self._save_generated_image(item["data"])
                                elif "url" in item:
                                    return await self._download_and_save_image(item["url"])

                    logger.error(f"[Gemini] 未能从响应中提取图片，完整响应: {result}")
                    return None

                elif response.status_code >= 500:
                    error_text = response.text
                    logger.warning(f"[Gemini] API服务器错误 (尝试 {attempt + 1}/{max_retries}): {response.status_code} - {error_text}")
                    last_error = Exception(f"API服务器错误: {response.status_code}")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(retry_delay * (attempt + 1))
                        continue
                else:
                    error_text = response.text
                    logger.error(f"[Gemini] 图片生成API调用失败: {response.status_code} - {error_text}")
                    raise Exception(f"API调用失败: {response.status_code} - {error_text}")

            except httpx.TimeoutException as e:
                logger.warning(f"[Gemini] 图片生成API调用超时 (尝试 {attempt + 1}/{max_retries}): {e}")
                last_error = e
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay * (attempt + 1))
                    continue
            except httpx.ConnectError as e:
                logger.warning(f"[Gemini] 图片生成API连接失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                last_error = e
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay * (attempt + 1))
                    continue
            except Exception as e:
                if "API调用失败" in str(e):
                    raise
                logger.warning(f"[Gemini] 图片生成失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                last_error = e
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay * (attempt + 1))
                    continue

        if isinstance(last_error, httpx.TimeoutException):
            raise Exception(f"[Gemini] 图片生成超时（已重试{max_retries}次），请稍后再试。API服务可能繁忙。")
        elif isinstance(last_error, httpx.ConnectError):
            raise Exception(f"[Gemini] 无法连接到图片生成服务（已重试{max_retries}次），请检查网络连接。")
        else:
            raise Exception(f"[Gemini] 图片生成失败（已重试{max_retries}次）: {str(last_error)}")
    
    async def _save_generated_image(self, base64_data: str) -> str:
        """保存base64图片到本地"""
        try:
            image_bytes = base64.b64decode(base64_data)
            
            filename = f"generated_{uuid.uuid4()}.png"
            filepath = os.path.join(settings.UPLOAD_DIR, filename)
            
            with open(filepath, "wb") as f:
                f.write(image_bytes)
            
            logger.info(f"生成图片已保存: {filepath}")
            return f"/uploads/{filename}"
            
        except Exception as e:
            logger.error(f"保存生成图片失败: {e}")
            raise
    
    async def _download_and_save_image(self, url: str) -> dict:
        """下载远程图片并保存为两个版本：缩略图(快速加载)和完整图(高质量)

        Returns:
            dict: {
                "thumbnail_url": "/uploads/thumb_xxx.jpg",  # 缩略图 ~200KB
                "full_url": "/uploads/generated_xxx.jpg"     # 完整图 ~1.2MB
            }
        """
        try:
            from PIL import Image
            import io

            client = await self._get_client()
            response = await client.get(url)

            if response.status_code == 200:
                # 生成唯一标识符
                unique_id = uuid.uuid4().hex[:8]

                # 加载图片
                img = Image.open(io.BytesIO(response.content))

                # 如果是RGBA模式，转换为RGB
                if img.mode == 'RGBA':
                    img = img.convert('RGB')

                # 1️⃣ 生成缩略图版本 (800x600, quality=70)
                thumb_filename = f"thumb_{unique_id}.jpg"
                thumb_filepath = os.path.join(settings.UPLOAD_DIR, thumb_filename)

                # 保持宽高比缩放到800x600以内
                img_thumb = img.copy()
                img_thumb.thumbnail((800, 600), Image.Resampling.LANCZOS)
                img_thumb.save(thumb_filepath, 'JPEG', quality=70, optimize=True, progressive=True)

                # 2️⃣ 生成完整图版本 (原尺寸, quality=85)
                full_filename = f"generated_{unique_id}.jpg"
                full_filepath = os.path.join(settings.UPLOAD_DIR, full_filename)
                img.save(full_filepath, 'JPEG', quality=85, optimize=True, progressive=True)

                logger.info(f"图片已下载并生成两个版本:")
                logger.info(f"  - 缩略图: {thumb_filepath} (质量70, 快速加载)")
                logger.info(f"  - 完整图: {full_filepath} (质量85, 高质量)")

                return {
                    "thumbnail_url": f"/uploads/{thumb_filename}",
                    "full_url": f"/uploads/{full_filename}"
                }
            else:
                raise Exception(f"下载图片失败: {response.status_code}")

        except Exception as e:
            logger.error(f"下载生成图片失败: {e}")
            raise
    
    # ============================================================
    # V2 生成方法 - 零决策，让生图模型自动判断风格
    # ============================================================

    V2_AUTO_STYLE_PROMPT_EN = """Based on this room photo, generate a soft furnishing makeover.

## Your Task
Automatically determine the most suitable interior design style for this space based on:
- The room's natural lighting and architecture
- Existing furniture and flooring
- The overall spatial proportions

## Constraints
- Keep the original room structure, walls, and floors unchanged
- Only modify soft furnishings (sofa covers, curtains, rugs), lighting fixtures, and decorative items
- All items should be realistic products available on e-commerce platforms
- Maintain consistent lighting and shadows with the original photo

## Output
Generate a high-quality, photorealistic interior design rendering showing the transformed space."""

    V2_AUTO_STYLE_PROMPT_ZH = """你是一位资深室内软装设计师。基于这张房间照片，生成一个令人眼前一亮的软装改造效果图。

## 设计策略

### 第一步：快速分析空间
- 光线：判断主光源方向（窗户位置）、光线质量（冷/暖、强/弱）
- 色调：识别墙面、地板的现有颜色基调
- 空间感：评估层高、面宽、视觉重心

### 第二步：选择适配风格
根据空间特点自动选择最合适的风格（北欧/日式/现代轻奢/自然风/波西米亚等）

### 第三步：执行改造策略

**色彩方案**（60-30-10法则）：
- 主色调60%：延续现有墙面/地板的基调，用大面积软装呼应
- 辅助色30%：选择与主色和谐的中性色（米色/灰色/木色）
- 点缀色10%：用1-2种鲜明颜色制造视觉焦点（抱枕/装饰画/绿植）

**材质搭配**（软硬对比）：
- 优先选择：亚麻、棉麻、羊毛、原木、陶瓷、藤编
- 材质对话：粗糙vs光滑、哑光vs亮面，创造层次感

**空间层次**（地面→坐卧→墙面→光线）：
- 地面层：地毯定义区域，尺寸要够大（沙发前腿压在地毯上）
- 坐卧层：抱枕/靠垫增加舒适度，用3-5个不同尺寸和图案
- 墙面层：装饰画/挂毯，尺寸要与墙面成比例（宽度占墙面60-75%）
- 光线层：落地灯/台灯营造氛围，高低错落

**摆放原则**：
- 三角构图：3件物品形成视觉稳定的三角关系
- 奇数法则：同类物品用1/3/5件组合
- 高低错落：避免所有物品同一高度

## 绝对约束
- ✅ 只通过软装改造：窗帘、地毯、抱枕、装饰画、灯具、绿植、摆件
- ❌ 不改变：墙面颜色、地板、门窗、大型家具（沙发/床可以加套子）
- ✅ 真实感：光影必须自然，物品比例符合真实尺寸
- ✅ 可购买性：所有物品都能在拼多多/淘宝买到

## 视觉目标
生成的效果图应该：
- 让人第一眼就觉得"哇，好有设计感"
- 保持克制，不要堆砌，每件物品都有存在的理由
- 氛围感强烈，但又是普通人能落地的方案
- 高质量、真实感的室内摄影效果"""

    V2_STYLE_OVERRIDE_PROMPT_EN = """Based on this room photo, generate a soft furnishing makeover in {style_name} style.

## Style Guidelines: {style_name}
{style_description}

## Constraints
- Keep the original room structure, walls, and floors unchanged
- Only modify soft furnishings (sofa covers, curtains, rugs), lighting fixtures, and decorative items
- All items should be realistic products available on e-commerce platforms
- Maintain consistent lighting and shadows with the original photo

## Output
Generate a high-quality, photorealistic interior design rendering in {style_name} style."""

    V2_STYLE_OVERRIDE_PROMPT_ZH = """基于这张房间照片，用{style_name}风格生成软装改造效果图。

## 风格指南：{style_name}
{style_description}

## 约束条件
- 保持原有房间结构、墙面、地板不变
- 只改变软装（沙发套、窗帘、地毯）、灯具和装饰品
- 所有物品都是电商平台可购买的真实商品
- 光影与原图保持一致

## 输出
生成高质量、真实感的{style_name}风格室内设计效果图。"""

    V2_STYLE_DESCRIPTIONS = {
        StyleType.NORDIC: (
            "Nordic/Scandinavian",
            "北欧风",
            """色彩：大面积白色/浅灰为主（60%），原木色/米色/浅驼色为辅（30%），低饱和度莫兰迪色点缀（10% - 雾霾蓝/灰粉/橄榄绿）
材质：白橡木、亚麻、羊毛、陶瓷、少量黄铜
关键单品：几何图案地毯、亚麻质感抱枕（3-5个）、细腿落地灯、陶瓷花瓶、编织收纳筐、大型绿植（龟背竹/琴叶榕）
空间手法：大面积留白，线条感强的几何秩序，绿植作为唯一高饱和色
光线：最大化自然光，暖色温氛围灯（2700K-3000K）
避免：深色大家具、繁复花纹、过多装饰、冷白光"""
        ),
        StyleType.JAPANESE: (
            "Japanese/Wabi-sabi",
            "日式",
            """色彩：温暖米白/象牙白（60%），偏红胡桃木或偏黄白蜡木（30%），低调灰绿/深褐点缀（10%）
材质：榻榻米/竹子/和纸/麻布/深色木材
关键单品：矮脚家具、障子门/竹帘、手工陶器、日式蒲团坐垫、枯山水风格摆件、松树盆景
空间手法：横向延展、不对称平衡、留白制造呼吸感
光线：柔和漫射光，纸灯笼/行灯，拒绝直射顶灯
避免：繁复装饰、鲜艳色彩、高饱和度、欧式家具"""
        ),
        StyleType.VINTAGE: (
            "Vintage/Mid-century",
            "复古中古",
            """色彩：深邃色调为主（60% - 酒红/墨绿/芥末黄/焦糖色），木质中性色（30%），金属色点缀（10% - 黄铜/玫瑰金）
材质：天鹅绒、皮革、柚木、黄铜、玻璃
关键单品：天鹅绒沙发套/抱枕、黄铜落地灯、复古挂钟、老式留声机造型摆件、花纹地毯（波斯/几何）、干花/羽毛装饰
空间手法：色彩浓郁但不失优雅，金属反光制造奢华感
光线：暖黄光、Edison灯泡、重点照明
避免：极简白色、塑料材质、冷色调、过于现代感"""
        ),
        StyleType.MODERN_LUXURY: (
            "Modern Luxury",
            "现代轻奢",
            """色彩：中性灰/米白/象牙白（60%），深灰/黑色锚定（30%），金属/宝石色点缀（10% - 金/铜/祖母绿）
材质：大理石纹理、金属（拉丝金/黑钛）、皮革、丝绒、镜面
关键单品：大理石纹抱枕、金属边框装饰画、几何吊灯、丝绒窗帘、金属托盘+香薰蜡烛、黑白摄影作品
空间手法：干净利落的线条+精致材质，镜面反光增加空间感
光线：嵌入式灯带、金属反光、柔和氛围灯
避免：乡村质朴、过多木质、鲜艳色彩、廉价塑料"""
        ),
        StyleType.NATURAL: (
            "Natural/Organic",
            "自然风",
            """色彩：大地色系（60% - 米黄/陶土/沙色），原木色（30%），植物绿色（10%）
材质：原木（保留木纹）、藤编、竹子、陶土、棉麻、黄麻
关键单品：大量绿植（不同高度3-5盆）、藤编吊灯/篮子、陶土花盆、麻绳装饰、原木托盘、手工编织地毯
空间手法：植物作为主角，自然材质层叠，拒绝人造感
光线：自然光为主，暖色温补光
避免：塑料材质、金属光泽、纯白墙面、人工色彩"""
        ),
        StyleType.BOHO: (
            "Bohemian",
            "波西米亚",
            """色彩：暖色调混搭（60% - 焦糖/砖红/芥末黄），民族图案色彩（30% - 蓝/绿/橙），金色点缀（10%）
材质：多层纺织品、流苏、刺绣、皮革、木珠、羽毛
关键单品：流苏挂毯/Macramé、民族风地毯叠加、大量抱枕（5-7个混搭）、藤椅、摩洛哥风格灯笼、羽毛/捕梦网装饰
空间手法：层叠丰富、混搭不同文化元素、打破规则
光线：暖黄光、民族风灯具、蜡烛
避免：极简、单调、工业感、冷色调"""
        ),
        StyleType.MINIMALIST: (
            "Minimalist",
            "极简主义",
            """色彩：单色调（60% - 纯白/极灰/黑），同色系深浅变化（30%），最多1个点缀色（10%）
材质：哑光表面、纯色织物、隐藏式材质
关键单品：纯色地毯、单色抱枕（最多3个）、几何雕塑摆件、线条灯具、隐藏式收纳
空间手法：少即是多，每个物品都必须有功能，隐藏杂物
光线：建筑化灯光、灯带、射灯
避免：任何繁复装饰、花纹图案、过多物品"""
        ),
        StyleType.MODERN_MINIMALIST: (
            "Modern Minimalist",
            "现代简约",
            """色彩：黑白灰为主（60%），木色/米色（30%），1个鲜明点缀色（10% - 蓝/黄/红任选一个）
材质：光滑表面、现代织物、金属细节
关键单品：几何图案地毯、纯色+几何抱枕、现代装饰画（抽象/色块）、简约灯具、少量绿植
空间手法：直线条、几何形状、功能优先
光线：明亮均匀、嵌入式筒灯+氛围灯
避免：繁复装饰、乡村元素、过多色彩"""
        ),
        StyleType.COASTAL: (
            "Coastal",
            "海岸风",
            """色彩：蓝白配色（60% - 天蓝/海军蓝/白），原木/米色（30%），珊瑚橙点缀（10%）
材质：亚麻、棉质、漂白木、绳子、贝壳、玻璃
关键单品：蓝白条纹/海浪纹地毯、亚麻窗帘、贝壳/珊瑚摆件、麻绳装饰、蓝色玻璃花瓶、海洋主题装饰画
空间手法：清爽通透、轻盈材质、海洋元素点缀
光线：明亮自然光、白光/冷白光
避免：深色沉重、封闭感、陆地植物过多"""
        ),
        StyleType.INDUSTRIAL: (
            "Industrial",
            "工业风",
            """色彩：深色调（60% - 黑/深灰/锈色），原木/混凝土色（30%），金属色（10% - 铁锈/铜/银）
材质：裸露金属、做旧木材、皮革、铁艺
关键单品：金属吊灯（Edison灯泡）、铁艺书架/装饰、皮革沙发套、做旧木箱、齿轮/管道造型摆件、黑白工业风装饰画
空间手法：暴露结构感、粗犷与精致并存、功能性物件作为装饰
光线：暖黄工业灯、铁艺灯罩、Edison灯泡
避免：田园风、粉色系、精致花纹、过多织物"""
        ),
    }

    async def generate_v2_with_items(
        self,
        original_image_path: str,
        override_style: Optional[StyleType] = None,
        lang: str = "en",
        progress_callback=None,
        prompt_callback=None,
        items_callback=None  # 🆕 物品数组回调，用于并发处理
    ) -> tuple[Optional[dict], Optional[str], Optional[list[str]]]:
        """
        V2 生成方法 - 同时返回图片、设计文本和物品数组（优化版）

        Args:
            original_image_path: 原图路径
            override_style: 用户指定的风格
            lang: 语言
            progress_callback: 进度回调
            prompt_callback: 设计文案回调
            items_callback: 物品数组回调（每个物品立即回调）

        Returns:
            (生成图片信息字典{"thumbnail_url": str, "full_url": str}, 设计文本, 物品数组)
        """
        if not self.api_key:
            logger.error("图片生成服务未配置API密钥")
            raise ValueError("图片生成服务未配置")

        # 使用VLLM生成设计方案和物品数组
        design_text = None
        items_array = []

        if not override_style and lang == "zh":
            logger.info("使用VLLM生成设计方案和物品数组...")
            try:
                from services.vllm_service import vllm_service
                design_text, items_array = await vllm_service.generate_prompt_with_items(original_image_path)

                if design_text:
                    logger.info(f"✅ VLLM生成成功: 设计方案{len(design_text)}字, 物品{len(items_array) if items_array else 0}个")

                    # 立即回调设计文本，让前端开始打字机
                    if prompt_callback:
                        await prompt_callback(design_text)

                    # 流式回调物品数组，每个物品立即开始匹配
                    if items_callback and items_array:
                        for item_name in items_array:
                            await items_callback(item_name)
                else:
                    logger.warning("VLLM未生成内容,使用fallback")
            except Exception as e:
                logger.warning(f"VLLM生成失败: {e}")

        # Fallback: 使用固定prompt
        if not design_text:
            logger.warning("使用fallback prompt生成")
            from services.vllm_service import vllm_service
            design_text = vllm_service.get_fallback_prompt()

        # 使用设计文本生成图片（与物品匹配并发）
        logger.info(f"V2 [seedream] 最终使用的Prompt: {design_text[:200]}...")

        try:
            if self.provider == "seedream":
                generated_image_path = await self._generate_v2_with_seedream(
                    original_image_path=original_image_path,
                    user_prompt=design_text,
                    progress_callback=progress_callback
                )
            else:
                raise ValueError(f"不支持的provider: {self.provider}")

            return generated_image_path, design_text, items_array

        except Exception as e:
            logger.error(f"图片生成失败: {e}")
            raise

    async def generate_v2(
        self,
        original_image_path: str,
        override_style: Optional[StyleType] = None,
        lang: str = "en",
        progress_callback=None,
        prompt_callback=None  # 🆕 VLLM生成prompt后的回调
    ) -> tuple[Optional[str], Optional[str]]:
        """
        V2 生成方法 - 零决策，支持多提供商

        Args:
            original_image_path: 原图路径
            override_style: 用户指定的风格（可选，None则让AI自动判断）
            lang: 语言
            progress_callback: 可选的进度回调函数，接收参数 (percentage, message)

        Returns:
            (生成图片的本地路径, VLLM生成的prompt)
        """
        if not self.api_key:
            logger.error("图片生成服务未配置API密钥")
            raise ValueError("图片生成服务未配置。请在 .env 文件中设置对应的 API Key")

        # 🆕 优先使用VLLM生成针对性prompt
        user_prompt = None
        vllm_prompt = None

        if not override_style and lang == "zh":
            # 只有在自动风格+中文时才使用VLLM
            logger.info("尝试使用VLLM生成针对性prompt...")
            try:
                from services.vllm_service import vllm_service
                vllm_prompt = await vllm_service.generate_prompt(original_image_path)
                if vllm_prompt:
                    user_prompt = vllm_prompt
                    logger.info(f"✅ VLLM生成prompt成功 ({len(vllm_prompt)}字)")
                    # 🆕 立即回调通知routes.py，让前端开始打字机展示
                    if prompt_callback:
                        await prompt_callback(vllm_prompt)
                else:
                    logger.warning("VLLM未生成prompt,使用fallback")
                    from services.vllm_service import vllm_service
                    user_prompt = vllm_service.get_fallback_prompt()
                    vllm_prompt = user_prompt
                    if prompt_callback:
                        await prompt_callback(vllm_prompt)
            except Exception as e:
                logger.warning(f"VLLM生成prompt失败: {e},使用固定prompt")

        # Fallback: 使用原有的固定prompt
        if not user_prompt:
            if override_style:
                style_info = self.V2_STYLE_DESCRIPTIONS.get(override_style, ("Custom", "自定义", ""))
                style_name = style_info[1] if lang == "zh" else style_info[0]
                style_desc = style_info[2]

                if lang == "zh":
                    user_prompt = self.V2_STYLE_OVERRIDE_PROMPT_ZH.format(
                        style_name=style_name,
                        style_description=style_desc
                    )
                else:
                    user_prompt = self.V2_STYLE_OVERRIDE_PROMPT_EN.format(
                        style_name=style_name,
                        style_description=style_desc
                    )
            else:
                user_prompt = self.V2_AUTO_STYLE_PROMPT_ZH if lang == "zh" else self.V2_AUTO_STYLE_PROMPT_EN

        logger.info(f"V2 [{self.provider}] 最终使用的Prompt: {user_prompt[:200]}...")

        # 根据提供商选择不同的调用方式
        if self.provider == ImageGenProvider.SEEDREAM:
            image_path = await self._generate_v2_with_seedream(original_image_path, user_prompt, progress_callback)
            return (image_path, vllm_prompt)
        else:
            image_path = await self._generate_v2_with_gemini(original_image_path, user_prompt, lang)
            return (image_path, vllm_prompt)

    async def _generate_v2_with_seedream(
        self,
        original_image_path: str,
        user_prompt: str,
        progress_callback=None
    ) -> Optional[str]:
        """
        V2 Seedream 图生图实现（支持流式进度）

        Args:
            original_image_path: 原图路径
            user_prompt: 生成提示词
            progress_callback: 可选的进度回调函数，接收参数 (percentage, message)
        """
        # 读取原图并转为 base64
        with open(original_image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode()
        media_type = self._get_media_type(original_image_path)
        image_base64 = f"data:{media_type};base64,{image_data}"

        client = await self._get_client()

        # 当前模型仅支持非流式
        request_body = {
            "model": self.model,
            "prompt": user_prompt,
            "image": image_base64,  # 传入参考图
            "response_format": "url",
            "size": "2K",
            "watermark": False
        }

        logger.info(f"[Seedream V2] 调用API: {self.api_url}/images/generations")

        max_retries = 3
        retry_delay = 5
        last_error = None

        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    logger.info(f"[Seedream V2] 第 {attempt + 1} 次重试...")

                response = await client.post(
                    f"{self.api_url}/images/generations",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json=request_body,
                    timeout=120.0
                )
                logger.info(f"[Seedream V2] API响应状态码: {response.status_code}")

                if response.status_code != 200:
                    raise Exception(f"[Seedream V2] API调用失败: {response.status_code} - {response.text}")

                result = response.json()
                data = result.get("data", [])
                image_url = data[0].get("url") if data else None

                if image_url:
                    logger.info("[Seedream V2] 图片生成完成")
                    if progress_callback:
                        await progress_callback(100, "图片生成完成")
                    return await self._download_and_save_image(image_url)
                else:
                    logger.error(f"[Seedream V2] 响应中未获取到图片URL: {result}")
                    return None

            except httpx.TimeoutException as e:
                last_error = e
                logger.error(f"[Seedream V2] 请求超时: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay * (attempt + 1))
                    continue
            except httpx.ConnectError as e:
                last_error = e
                logger.error(f"[Seedream V2] 连接失败: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay * (attempt + 1))
                    continue
            except Exception as e:
                if "API调用失败" in str(e):
                    raise
                last_error = e
                logger.error(f"[Seedream V2] 生成失败: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay * (attempt + 1))
                    continue

        raise Exception(f"[Seedream V2] 图片生成失败: {str(last_error)}")

    async def _generate_v2_with_gemini(self, original_image_path: str, user_prompt: str, lang: str) -> Optional[str]:
        """V2 Gemini 实现（原有逻辑）"""
        with open(original_image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode()

        media_type = self._get_media_type(original_image_path)
        client = await self._get_client()

        system_prompt = "You are a professional interior designer. Generate photorealistic room makeover images." if lang == "en" else "你是一位专业室内设计师。生成真实感的房间改造效果图。"

        request_body = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{media_type};base64,{image_data}"
                            }
                        },
                        {
                            "type": "text",
                            "text": user_prompt
                        }
                    ]
                }
            ],
            "max_tokens": 4096
        }

        logger.info(f"[Gemini V2] 调用API: {self.api_url}/chat/completions, model={self.model}")

        # 重试逻辑
        max_retries = 3
        retry_delay = 5
        last_error = None

        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    logger.info(f"[Gemini V2] 第 {attempt + 1} 次重试...")

                response = await client.post(
                    f"{self.api_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json=request_body
                )

                logger.info(f"[Gemini V2] API响应状态码: {response.status_code}")

                if response.status_code == 200:
                    result = response.json()

                    choices = result.get("choices", [])
                    if not choices:
                        logger.error("[Gemini V2] API响应中没有choices")
                        return None

                    message = choices[0].get("message", {})
                    content = message.get("content", [])

                    if isinstance(content, str):
                        logger.warning(f"[Gemini V2] 模型返回文本而非图片: {content[:200]}")
                        if "data:image" in content:
                            import re
                            match = re.search(r'data:image/[^;]+;base64,([A-Za-z0-9+/=]+)', content)
                            if match:
                                image_base64 = match.group(1)
                                return await self._save_generated_image(image_base64)
                        return None

                    for item in content:
                        if isinstance(item, dict):
                            if item.get("type") == "image_url":
                                image_url = item.get("image_url", {}).get("url", "")
                                if image_url.startswith("data:image"):
                                    base64_data = image_url.split(",", 1)[1] if "," in image_url else ""
                                    if base64_data:
                                        return await self._save_generated_image(base64_data)
                            elif item.get("type") == "image":
                                if "data" in item:
                                    return await self._save_generated_image(item["data"])
                                elif "url" in item:
                                    return await self._download_and_save_image(item["url"])

                    logger.error(f"[Gemini V2] 未能从响应中提取图片")
                    return None

                elif response.status_code >= 500:
                    error_text = response.text
                    logger.warning(f"[Gemini V2] API服务器错误 (尝试 {attempt + 1}/{max_retries}): {response.status_code}")
                    last_error = Exception(f"API服务器错误: {response.status_code}")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(retry_delay * (attempt + 1))
                        continue
                else:
                    error_text = response.text
                    logger.error(f"[Gemini V2] 图片生成API调用失败: {response.status_code} - {error_text}")
                    raise Exception(f"API调用失败: {response.status_code} - {error_text}")

            except httpx.TimeoutException as e:
                logger.warning(f"[Gemini V2] API调用超时 (尝试 {attempt + 1}/{max_retries})")
                last_error = e
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay * (attempt + 1))
                    continue
            except httpx.ConnectError as e:
                logger.warning(f"[Gemini V2] API连接失败 (尝试 {attempt + 1}/{max_retries})")
                last_error = e
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay * (attempt + 1))
                    continue
            except Exception as e:
                if "API调用失败" in str(e):
                    raise
                logger.warning(f"[Gemini V2] 图片生成失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                last_error = e
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay * (attempt + 1))
                    continue

        if isinstance(last_error, httpx.TimeoutException):
            raise Exception(f"[Gemini V2] 图片生成超时（已重试{max_retries}次），请稍后再试。")
        elif isinstance(last_error, httpx.ConnectError):
            raise Exception(f"[Gemini V2] 无法连接到图片生成服务（已重试{max_retries}次）。")
        else:
            raise Exception(f"图片生成失败（已重试{max_retries}次）: {str(last_error)}")

    async def close(self):
        """关闭HTTP客户端"""
        if self._client:
            await self._client.aclose()
            self._client = None

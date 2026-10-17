"""
换装相机 设计系统
大师级软装设计方法论与风格定义
"""
from typing import Optional
from models.schemas import StyleType, BudgetLevel, RoomType


class DesignSystem:
    """
    专业软装设计系统
    
    设计哲学：
    - 每个空间都有最适合它的软装方案
    - 好的软装是"看不出设计痕迹"的自然存在
    - 可购买、可落地才是真正的好设计
    """
    
    # ========== 系统提示词：定义AI的专业身份 ==========
    SYSTEM_PROMPT = """你是一位拥有15年经验的高级软装设计师，曾为数百个家庭完成空间改造。

你的设计原则：
1. 空间优先 - 先理解空间的光线、比例、动线，再决定添加什么
2. 克制添加 - 宁少勿多，每件物品都要有存在的理由
3. 层次分明 - 用地面、中层、墙面、光线四个层次构建空间
4. 可落地性 - 推荐的物品必须是电商平台能买到的真实商品

你的工作方式：
- 分析原图的空间特点和现有基调
- 根据风格要求确定色彩和材质方向
- 在关键位置添加软装，建立视觉焦点
- 确保光影自然，物品比例正确

技术约束：
- 不改变硬装（墙面、地板、门窗、天花）
- 不移动或替换现有大件家具
- 只通过添加软装提升空间质感
- 生成真实自然的室内照片效果"""

    # ========== 风格定义：专业但不晦涩 ==========
    STYLES = {
        StyleType.NORDIC: {
            "name": "北欧简约",
            "core": "功能主义美学，少即是多",
            "palette": {
                "base": "白色、浅灰、米白",
                "accent": "雾霾蓝、烟粉、芥末黄",
                "material": "原木色、亚麻本色"
            },
            "key_elements": [
                "几何图案纺织品",
                "原木腿细脚家具",
                "绿植（琴叶榕、龟背竹）",
                "羊毛/棉麻质感"
            ],
            "avoid": "过多装饰、深色大面积、繁复图案",
            "light_strategy": "最大化自然光，暖白色人工光源",
            "spatial_feel": "通透、轻盈、呼吸感"
        },
        
        StyleType.JAPANESE: {
            "name": "日式原木",
            "core": "侘寂美学，自然与秩序的平衡",
            "palette": {
                "base": "木色、米色、灰白",
                "accent": "抹茶绿、靛蓝、陶土色",
                "material": "浅色木纹、棉麻、陶器"
            },
            "key_elements": [
                "低矮家具线条",
                "棉麻窗帘/布艺",
                "陶瓷器皿摆件",
                "枯枝/简约插花"
            ],
            "avoid": "金属光泽、高饱和色、西式古典元素",
            "light_strategy": "柔和漫射光，纸质灯罩过滤",
            "spatial_feel": "宁静、留白、禅意"
        },
        
        StyleType.VINTAGE: {
            "name": "复古中古",
            "core": "时间沉淀的质感，混搭的协调",
            "palette": {
                "base": "焦糖棕、墨绿、酒红",
                "accent": "黄铜色、琥珀色、象牙白",
                "material": "胡桃木、丝绒、黄铜"
            },
            "key_elements": [
                "中古风格灯具",
                "丝绒/天鹅绒织物",
                "黄铜五金装饰",
                "复古挂画/镜框"
            ],
            "avoid": "塑料感材质、过于现代的线条、冷色调",
            "light_strategy": "暖黄光源，多点位氛围照明",
            "spatial_feel": "温暖、故事感、沉稳"
        },
        
        StyleType.MODERN_LUXURY: {
            "name": "现代轻奢",
            "core": "精致克制，细节见品质",
            "palette": {
                "base": "高级灰、奶白、大地色",
                "accent": "金色、黑色、翡翠绿",
                "material": "大理石纹、金属、皮革"
            },
            "key_elements": [
                "金属边框装饰",
                "几何造型摆件",
                "皮质/丝质织物",
                "艺术装置挂画"
            ],
            "avoid": "廉价感装饰、过于花哨、堆砌感",
            "light_strategy": "层次照明，重点照明突出艺术品",
            "spatial_feel": "精致、高级、克制的奢华"
        },
        
        StyleType.NATURAL: {
            "name": "自然清新",
            "core": "将户外搬进室内，生机盎然",
            "palette": {
                "base": "森林绿、原木色、米白",
                "accent": "植物绿、泥土棕、天空蓝",
                "material": "藤编、竹木、棉麻、陶土"
            },
            "key_elements": [
                "大量绿植组合",
                "藤编/草编收纳",
                "木质/陶土花器",
                "自然肌理纺织品"
            ],
            "avoid": "人造材质、冷硬金属、工业感",
            "light_strategy": "模拟自然光，植物补光",
            "spatial_feel": "清新、生命力、治愈"
        },
        
        StyleType.MINIMALIST: {
            "name": "极简主义",
            "core": "去除一切非必要，留下纯粹",
            "palette": {
                "base": "纯白、浅灰、黑",
                "accent": "单一亮色点缀（可选）",
                "material": "哑光表面、隐藏收纳"
            },
            "key_elements": [
                "纯色无图案布艺",
                "隐藏式收纳",
                "单一造型绿植",
                "线条感装饰"
            ],
            "avoid": "任何多余装饰、复杂图案、色彩堆砌",
            "light_strategy": "均匀照明，无阴影死角",
            "spatial_feel": "纯净、秩序、专注"
        }
    }
    
    # ========== 房间特性：不同空间的设计侧重 ==========
    ROOM_CHARACTERISTICS = {
        RoomType.LIVING_ROOM: {
            "name": "客厅",
            "function": "社交、休憩、展示",
            "focus_areas": ["沙发区域", "茶几周围", "电视墙/主墙面"],
            "key_additions": ["地毯定义区域", "抱枕增加层次", "落地灯补充照明", "墙面装饰建立焦点"],
            "scale": "可接受大尺寸软装"
        },
        RoomType.BEDROOM: {
            "name": "卧室",
            "function": "睡眠、放松、私密",
            "focus_areas": ["床头区域", "床尾/床侧", "窗边"],
            "key_additions": ["床头灯/壁灯", "床尾毯/盖毯", "床头装饰画", "飘窗软垫"],
            "scale": "柔软、助眠、不宜过多"
        },
        RoomType.STUDY: {
            "name": "书房",
            "function": "工作、阅读、思考",
            "focus_areas": ["桌面区域", "书架/墙面", "阅读角"],
            "key_additions": ["台灯/护眼灯", "桌面收纳", "墙面置物架", "舒适座椅软垫"],
            "scale": "功能优先，避免干扰"
        },
        RoomType.BALCONY: {
            "name": "阳台",
            "function": "休闲、绿植、晾晒",
            "focus_areas": ["座椅区", "绿植区", "地面"],
            "key_additions": ["户外地毯/垫", "绿植组合", "小型休闲桌椅", "氛围灯串"],
            "scale": "耐候材质，小巧精致"
        },
        RoomType.DINING_ROOM: {
            "name": "餐厅",
            "function": "用餐、聚会",
            "focus_areas": ["餐桌上方", "餐边柜", "墙面"],
            "key_additions": ["餐桌布艺", "吊灯/餐吊灯", "餐边装饰", "墙面挂画"],
            "scale": "围绕餐桌为核心"
        },
        RoomType.OTHER: {
            "name": "其他空间",
            "function": "多功能",
            "focus_areas": ["主要活动区域"],
            "key_additions": ["根据功能定制"],
            "scale": "灵活适配"
        }
    }
    
    # ========== 预算策略：不是数物品，而是设计完整度 ==========
    BUDGET_STRATEGIES = {
        BudgetLevel.LOW: {
            "name": "轻点缀",
            "price_range": "300元以内",
            "philosophy": "一两件精准的单品，四两拨千斤",
            "approach": "找到空间最需要改善的一个点，用最少的投入实现最大的改变",
            "typical_items": "1个重点软装 + 1-2个小配饰",
            "priority": ["视觉焦点单品", "氛围光源", "点缀绿植"]
        },
        BudgetLevel.MEDIUM: {
            "name": "基础改造",
            "price_range": "500元左右",
            "philosophy": "建立空间的基本层次感",
            "approach": "地面+中层+一个墙面焦点，形成完整的视觉动线",
            "typical_items": "地毯/落地灯 + 布艺组合 + 墙面装饰",
            "priority": ["区域定义（地毯）", "层次构建（布艺）", "焦点设立（挂画/灯具）"]
        },
        BudgetLevel.HIGH: {
            "name": "品质提升",
            "price_range": "1000元左右",
            "philosophy": "系统化提升空间的整体质感",
            "approach": "完整的四层次设计：地面层、坐卧层、墙面层、光线层",
            "typical_items": "品质地毯 + 灯具组合 + 布艺系列 + 绿植组合 + 墙面装饰",
            "priority": ["整体氛围营造", "材质质感提升", "细节完善"]
        },
        BudgetLevel.PREMIUM: {
            "name": "全面焕新",
            "price_range": "2000元左右",
            "philosophy": "接近专业设计师的完整软装方案",
            "approach": "每个角落都经过考量，形成完整的设计语言",
            "typical_items": "全套布艺更新 + 多组灯具 + 大型绿植 + 艺术装饰品 + 收纳系统",
            "priority": ["空间完整性", "风格一致性", "生活品质感"]
        }
    }
    
    @classmethod
    def get_style_info(cls, style: StyleType) -> dict:
        """获取风格详细信息"""
        return cls.STYLES.get(style, cls.STYLES[StyleType.NORDIC])
    
    @classmethod
    def get_room_info(cls, room_type: RoomType) -> dict:
        """获取房间特性信息"""
        return cls.ROOM_CHARACTERISTICS.get(room_type, cls.ROOM_CHARACTERISTICS[RoomType.OTHER])
    
    @classmethod
    def get_budget_info(cls, budget: BudgetLevel) -> dict:
        """获取预算策略信息"""
        return cls.BUDGET_STRATEGIES.get(budget, cls.BUDGET_STRATEGIES[BudgetLevel.MEDIUM])
    
    @classmethod
    def generate_design_brief(
        cls,
        room_type: RoomType,
        style: StyleType,
        budget: BudgetLevel
    ) -> dict:
        """
        生成设计简报 - 用于展示给用户
        简洁但专业的设计思路概述
        """
        style_info = cls.get_style_info(style)
        room_info = cls.get_room_info(room_type)
        budget_info = cls.get_budget_info(budget)
        
        return {
            "style_name": style_info["name"],
            "style_core": style_info["core"],
            "palette": style_info["palette"],
            "room_name": room_info["name"],
            "focus_areas": room_info["focus_areas"],
            "budget_name": budget_info["name"],
            "budget_philosophy": budget_info["philosophy"],
            "spatial_feel": style_info["spatial_feel"]
        }
    
    @classmethod
    def build_generation_prompt(
        cls,
        room_type: RoomType,
        style: StyleType,
        budget: BudgetLevel,
        custom_prompt: Optional[str] = None
    ) -> str:
        """
        构建图片生成的完整Prompt
        结构化、专业、直接
        """
        style_info = cls.get_style_info(style)
        room_info = cls.get_room_info(room_type)
        budget_info = cls.get_budget_info(budget)
        
        prompt = f"""基于这张{room_info['name']}照片，生成软装改造后的效果图。

【设计方向】
风格：{style_info['name']} - {style_info['core']}
色彩：基础色({style_info['palette']['base']})，点缀色({style_info['palette']['accent']})
材质：{style_info['palette']['material']}
空间感：{style_info['spatial_feel']}

【改造重点】
区域：{', '.join(room_info['focus_areas'])}
核心单品：{', '.join(style_info['key_elements'][:3])}
光线处理：{style_info['light_strategy']}

【预算定位】{budget_info['name']}
{budget_info['approach']}
添加：{budget_info['typical_items']}

【设计约束】
- 避免：{style_info['avoid']}
- 保持物品比例真实、光影自然
- 确保推荐的物品在电商平台可购买

请直接生成改造后的效果图。"""

        if custom_prompt:
            prompt += f"\n\n【用户特殊要求】\n{custom_prompt}"
        
        return prompt


# ========== 用于前端展示的简化版风格信息 ==========
def get_style_options_for_frontend():
    """
    获取前端展示用的风格选项
    简洁但有设计感的描述
    """
    return [
        {
            "value": "nordic",
            "label": "北欧简约",
            "description": "白+原木+几何，通透轻盈",
            "keywords": ["明亮", "原木", "几何"]
        },
        {
            "value": "japanese",
            "label": "日式原木",
            "description": "留白+棉麻+低矮，宁静禅意",
            "keywords": ["禅意", "棉麻", "木质"]
        },
        {
            "value": "vintage",
            "label": "复古中古",
            "description": "深木+黄铜+丝绒，温暖怀旧",
            "keywords": ["复古", "黄铜", "质感"]
        },
        {
            "value": "modern_luxury",
            "label": "现代轻奢",
            "description": "灰+金+大理石，精致克制",
            "keywords": ["轻奢", "金属", "高级"]
        },
        {
            "value": "natural",
            "label": "自然清新",
            "description": "绿植+藤编+陶土，生机治愈",
            "keywords": ["绿植", "自然", "清新"]
        },
        {
            "value": "minimalist",
            "label": "极简主义",
            "description": "纯色+线条+留白，纯净专注",
            "keywords": ["极简", "纯净", "秩序"]
        }
    ]




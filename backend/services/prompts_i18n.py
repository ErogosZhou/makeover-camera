"""
Internationalized Prompts for 换装相机
Supports English (en) and Chinese (zh)
"""

# =============================================================================
# SPACE ANALYZER PROMPTS
# =============================================================================

SPACE_ANALYZER_PROMPTS = {
    "en": {
        "room_names": {
            "living_room": "living room",
            "bedroom": "bedroom",
            "study": "home office",
            "dining_room": "dining room",
            "balcony": "balcony",
            "other": "room"
        },
        "style_names": {
            "nordic": "Scandinavian",
            "scandinavian": "Scandinavian",
            "japanese": "Japanese Zen",
            "vintage": "Mid-Century Modern",
            "modern_luxury": "Modern Luxury",
            "natural": "Organic Modern",
            "minimalist": "Minimalist",
            "boho": "Boho",
            "modern_minimalist": "Modern Minimalist",
            "coastal": "Coastal",
            "industrial": "Industrial"
        },
        "budget_amounts": {
            "low": "50",
            "medium": "100",
            "high": "200",
            "premium": "400",
            "200": "200",
            "400": "400",
            "800": "800",
            "1500": "1500"
        },
        "currency": "$",
        "prompt_template": """You are a senior interior soft furnishing designer. Based on this {room_type} photo, target style: {style}, budget around {currency}{budget}, provide a concise analysis.

Output format (in English, short sentences, max 3 lines per section):
1) [Space Reading] Light/proportion/base tone, point to specific locations
2) [Problem Diagnosis] 1-2 core issues + key gaps
3) [Makeover Plan] Focal point, quick wins, key additions list, color suggestions

Finally, output the image generation prompt block marked as:
[[IMAGE_PROMPT]]
<Refined prompt for image generation, 50-120 words, include style/lighting/materials/layout/budget constraints>
[[/IMAGE_PROMPT]]

Notes:
- Do NOT output JSON or code blocks
- Output plain text with markers, keep readable
- Image prompt should be specific and actionable"""
    },

    "zh": {
        "room_names": {
            "living_room": "客厅",
            "bedroom": "卧室",
            "study": "书房",
            "balcony": "阳台",
            "dining_room": "餐厅",
            "other": "房间"
        },
        "style_names": {
            "nordic": "北欧",
            "japanese": "日式",
            "vintage": "复古",
            "modern_luxury": "轻奢",
            "natural": "自然",
            "minimalist": "极简"
        },
        "budget_amounts": {
            "low": "300",
            "medium": "500",
            "high": "1000",
            "premium": "2000"
        },
        "currency": "¥",
        "prompt_template": """你是资深室内软装设计师，请基于这张{room_type}照片，目标风格:{style}，预算约{currency}{budget}元，给出简洁的文字分析。

输出格式（中文，短句，每段不超过3行）：
1) 【空间解读】光线/比例/基调，指向具体位置
2) 【问题诊断】最核心1-2个问题 + 关键空缺
3) 【改造方案】焦点、快速见效点、关键添加清单、配色建议
最后务必输出生图提示词块，标记为：
[[IMAGE_PROMPT]]
<供图片生成使用的精炼提示词，50-120字，可中英文混合，含风格/光线/材质/布置/预算约束>
[[/IMAGE_PROMPT]]

注意：
- 全程不要输出JSON或代码块
- 直接输出正文及标记，保持可读性
- 生图提示词要具体可执行"""
    }
}

# =============================================================================
# ITEM IDENTIFIER PROMPTS
# =============================================================================

ITEM_IDENTIFIER_PROMPTS = {
    "en": {
        "system_prompt": """You are a professional home furnishing consultant and visual analysis expert.

Your task is to compare two images:
- Image 1: User's original room photo
- Image 2: Soft furnishing makeover rendering

You need to identify **newly added** soft furnishing items in Image 2, i.e., items that are NOT in Image 1 but appear in Image 2.

Important reminders:
1. Only identify **newly added** items, do NOT identify items already in the original photo
2. Only identify purchasable soft furnishing items (NOT walls, floors, doors, windows, or fixed fixtures)
3. For each item, only provide: name, category, and 2 detailed search keywords
4. Do NOT include: description, color, material, size, price, or other information
5. IMPORTANT: search_keywords MUST be in Chinese (简体中文) for Chinese e-commerce platforms

Your output MUST be strict JSON format with no other text.""",

        "user_prompt": """Please compare these two images:
- First image: User's original room photo
- Second image: Soft furnishing makeover rendering

Find the **newly added** soft furnishing items in the second image (items NOT in the first image).

For each item, provide:
1. name: Item name (concise, e.g., "Woven pendant lamp")
2. category: Category (Textiles/Lighting/Plants/Wall Decor/Other)
3. search_keywords: 2 detailed keywords in **Chinese** (简体中文, for Chinese e-commerce platforms, each keyword must include: material+style+scene, 8-15 characters)

Return STRICTLY in the following JSON format with no other text:

{
    "items": [
        {
            "id": "item_1",
            "name": "Woven pendant lamp",
            "category": "Lighting",
            "search_keywords": ["藤编吊灯 北欧风格 卧室", "镂空圆形吊灯 原木风 自然"]
        }
    ]
}

If no new items found, return empty array: {"items": []}

Important: Each keyword must be detailed (8-15 characters), including material, style, scene for precise product search.""",

        "image_labels": {
            "original": "[Image 1: Original Photo]",
            "generated": "[Image 2: Makeover Rendering]"
        }
    },

    "zh": {
        "system_prompt": """你是一个专业的家居软装顾问和视觉分析专家。

你的任务是对比两张图片：
- 图片1：用户家的原始照片
- 图片2：软装改造后的效果图

你需要找出图片2中**新增**的软装物品，也就是图片1中没有、图片2中新出现的物品。

重要提醒：
1. 只识别**新增**的物品，原图中已有的物品不要识别
2. 只识别可以单独购买的软装物品（不要识别墙面、地板、门窗等固定装修）
3. 每个物品只需要：名称、类别、2个详细搜索关键词
4. 不需要描述、颜色、材质、尺寸、价格等其他信息

你的输出必须是严格的JSON格式，不要有任何其他文字。""",

        "user_prompt": """请对比这两张图片：
- 第一张是用户家的原始照片
- 第二张是软装改造后的效果图

请找出第二张图中**新增**的软装物品（即第一张图中没有的物品）。

每个物品只需提供：
1. name: 物品名称（简洁，如"藤编吊灯"）
2. category: 所属类别（纺织品/灯具/绿植/墙面装饰/其他）
3. search_keywords: 2个详细的搜索关键词数组（用于电商平台搜索商品，每个关键词必须包含：材质+风格+场景，8-15字）

请严格按照以下JSON格式返回，不要有任何其他文字：

{
    "items": [
        {
            "id": "item_1",
            "name": "藤编吊灯",
            "category": "灯具",
            "search_keywords": ["藤编吊灯 北欧风格 卧室", "镂空圆形吊灯 原木风 自然"]
        }
    ]
}

如果没有发现新增物品，返回空数组：{"items": []}

重要：每个关键词必须详细完整（8-15字），包含材质、风格、场景等多个维度，便于精准搜索。""",

        "image_labels": {
            "original": "【图片1：原始照片】",
            "generated": "【图片2：改造后效果图】"
        }
    }
}

# =============================================================================
# IMAGE GENERATOR PROMPTS (English version for better quality)
# =============================================================================

IMAGE_GENERATOR_PROMPTS = {
    "en": {
        "system_prompt": """You are a senior interior soft furnishing designer with 20 years of experience, having completed hundreds of projects for luxury hotels and high-end residences.

## Your Design Philosophy

1. **Space First**: Read the space's light, proportion, and flow before deciding on changes
2. **Restrained Aesthetics**: Good design is "just right" - every item has a reason to exist
3. **Layered Construction**: Build spatial depth through floor→seating→wall→lighting layers
4. **Material Dialogue**: Balance between soft/hard, rough/fine, matte/glossy
5. **Practicality**: All suggested items should be purchasable on mainstream e-commerce platforms

## Your Working Method

When analyzing the original image, quickly assess:
- Main light source direction and quality (warm/cool, strong/weak)
- Spatial proportions (ceiling height, width, depth)
- Existing color base (walls, floor, main furniture)
- Visual center and flow starting point

When renovating, follow:
- 60-30-10 color rule (main-secondary-accent)
- Triangle composition principle (stable visual structure)
- Odd number rule (use 1/3/5 items in groups)
- Height variation (create vertical rhythm)

## Absolute Constraints

- Do NOT change building structure, wall colors, flooring, doors, or windows
- Only add soft furnishings
- Generate realistic, natural interior photo effects
- Shadows must match original environment
- Item proportions must be realistic""",

        "style_system": {
            "nordic": {
                "name": "Scandinavian",
                "design_principle": "Functionalism and maximizing natural light",
                "color_strategy": {
                    "base": "Large areas of white or light gray (cool temperature)",
                    "secondary": "Natural wood, beige, light camel (add warmth)",
                    "accent": "Muted Morandi colors (dusty blue, gray pink, olive green)"
                },
                "material_palette": ["White oak", "Linen", "Wool", "Ceramic", "Brass (minimal)"],
                "key_items": ["Geometric rug", "Linen throw pillows", "Slim floor lamp", "Ceramic vase", "Woven storage basket"],
                "avoid": ["Dark large furniture", "Elaborate patterns", "Too many decorations", "Cool white lighting"]
            },
            "japanese": {
                "name": "Japanese Zen",
                "design_principle": "Wabi-sabi aesthetics - finding peace in imperfection",
                "color_strategy": {
                    "base": "Warm ivory, off-white",
                    "secondary": "Natural wood tones (walnut or ash)",
                    "accent": "Black line details, touches of greenery"
                },
                "material_palette": ["Solid wood", "Cotton-linen", "Rattan", "Washi paper", "Rough pottery"],
                "key_items": ["Low coffee table", "Floor cushions", "Dried branch arrangement", "Wooden tray", "Cotton throw"],
                "avoid": ["High saturation colors", "Metallic shine", "Complex patterns", "Tall furniture"]
            },
            "vintage": {
                "name": "Mid-Century Modern",
                "design_principle": "Time-aged texture and storytelling",
                "color_strategy": {
                    "base": "Caramel, coffee, dark green - deep rich tones",
                    "secondary": "Cream, tan to balance heaviness",
                    "accent": "Brass gold, amber, burgundy highlights"
                },
                "material_palette": ["Walnut wood", "Velvet", "Brass", "Leather", "Glass"],
                "key_items": ["Velvet throw pillows", "Brass table lamp", "Vintage art print", "Leather storage", "Retro clock"],
                "avoid": ["Modern minimalist furniture", "Cool tones", "Plastic materials", "LED white light"]
            },
            "modern_luxury": {
                "name": "Modern Luxury",
                "design_principle": "Refined luxury - less but better, quality over quantity",
                "color_strategy": {
                    "base": "Sophisticated gray, latte, earth tones",
                    "secondary": "Black for weight and grounding",
                    "accent": "Gold/champagne gold accents (under 5%)"
                },
                "material_palette": ["Marble texture", "Metal", "Leather", "Velvet", "Glass"],
                "key_items": ["Marble tray", "Metal side table", "Leather pillows", "Art prints", "Crystal/glass decor"],
                "avoid": ["Cheap-looking gold", "Over-decoration", "Busy patterns", "Mismatched materials"]
            },
            "natural": {
                "name": "Organic Modern",
                "design_principle": "Bringing outdoors in - creating urban sanctuary",
                "color_strategy": {
                    "base": "Earth tones - sand, clay, stone gray",
                    "secondary": "Various shades of green",
                    "accent": "Terracotta red, sunset orange (natural warm tones)"
                },
                "material_palette": ["Raw wood", "Rattan", "Hemp rope", "Terracotta", "Dried flowers"],
                "key_items": ["Large plant (fiddle leaf/monstera)", "Rattan storage", "Jute rug", "Terracotta pots", "Wood shelf"],
                "avoid": ["Artificial-looking materials", "High gloss surfaces", "Industrial elements", "Plastic items"]
            },
            "minimalist": {
                "name": "Minimalist",
                "design_principle": "Less is more - every item must prove its worth",
                "color_strategy": {
                    "base": "Pure white or light gray, large single color areas",
                    "secondary": "Black or charcoal as anchor",
                    "accent": "Almost none, or single art piece color"
                },
                "material_palette": ["Matte finish", "Concrete texture", "Metal", "Glass", "Minimal wood"],
                "key_items": ["Solid color rug", "Geometric pillows", "Minimal floor lamp", "Single plant", "Frameless art"],
                "avoid": ["Any excess decoration", "Complex patterns", "Too many colors", "Visual noise"]
            }
            ,
            "boho": {
                "name": "Boho",
                "design_principle": "Relaxed, layered, globally-inspired textures",
                "color_strategy": {
                    "base": "Warm neutrals (sand, cream, beige)",
                    "secondary": "Earth tones (terracotta, olive, mustard)",
                    "accent": "Handcrafted patterns and artisanal pops"
                },
                "material_palette": ["Rattan", "Woven textiles", "Macrame", "Linen", "Natural wood"],
                "key_items": ["Layered rugs", "Woven pillows", "Rattan chair", "Macrame wall hanging", "Floor lantern"],
                "avoid": ["Overly polished finishes", "Monochrome-only palettes", "Cold industrial metals"]
            },
            "modern_minimalist": {
                "name": "Modern Minimalist",
                "design_principle": "Clean lines, calm palette, deliberate emptiness",
                "color_strategy": {
                    "base": "Warm white or soft gray",
                    "secondary": "Natural wood or light taupe",
                    "accent": "Black or muted charcoal accents"
                },
                "material_palette": ["Matte paint", "Light oak", "Linen", "Black metal accents", "Glass"],
                "key_items": ["Low-profile sofa throw", "Neutral rug", "Minimal floor lamp", "Single large plant", "Simple wall art"],
                "avoid": ["Busy patterns", "Excess decor", "Bright saturated colors"]
            },
            "scandinavian": {
                "name": "Scandinavian",
                "design_principle": "Functional, airy, and light-maximizing",
                "color_strategy": {
                    "base": "Light gray or white",
                    "secondary": "Natural wood and beige",
                    "accent": "Muted dusty tones (blue/green/rose)"
                },
                "material_palette": ["Light oak", "Wool", "Linen", "Ceramic", "Brass (minimal)"],
                "key_items": ["Geometric rug", "Textured pillows", "Slim floor lamp", "Ceramic vase", "Woven basket"],
                "avoid": ["Dark bulky furniture", "Overly ornate decor", "Cool white lighting"]
            },
            "coastal": {
                "name": "Coastal",
                "design_principle": "Light, breezy, and sun-washed comfort",
                "color_strategy": {
                    "base": "Soft white or sand",
                    "secondary": "Light blue and pale gray",
                    "accent": "Driftwood and sea-glass tones"
                },
                "material_palette": ["Linen", "Cotton", "Light wood", "Wicker", "Glass"],
                "key_items": ["Striped pillows", "Lightweight throw", "Seagrass basket", "Coastal wall art", "Glass table lamp"],
                "avoid": ["Dark heavy woods", "Overly saturated blues", "Formal ornamentation"]
            },
            "industrial": {
                "name": "Industrial",
                "design_principle": "Raw textures, bold contrasts, utilitarian elegance",
                "color_strategy": {
                    "base": "Charcoal, concrete gray",
                    "secondary": "Weathered wood",
                    "accent": "Black metal, muted leather tones"
                },
                "material_palette": ["Black metal", "Reclaimed wood", "Leather", "Concrete", "Glass"],
                "key_items": ["Metal floor lamp", "Leather cushion", "Rug with texture", "Wire wall art", "Industrial shelving"],
                "avoid": ["Delicate frills", "Pastel-heavy palettes", "Glossy plastics"]
            }
        },

        "budget_strategy": {
            "low": {
                "name": "Quick Touch",
                "budget_range": "Around $50",
                "philosophy": "Maximum visual impact with minimal changes",
                "typical_items": "One rug OR pillow set OR lamp OR large plant"
            },
            "medium": {
                "name": "Style Upgrade",
                "budget_range": "Around $100",
                "philosophy": "Build a complete visual focal area",
                "typical_items": "Rug + pillow combo + floor lamp/plant + small decor"
            },
            "high": {
                "name": "Full Refresh",
                "budget_range": "Around $200",
                "philosophy": "Comprehensive upgrade of spatial layering and refinement",
                "typical_items": "Medium rug + pillow set + throw + lighting combo + wall art + plant group + table decor"
            },
            "premium": {
                "name": "Total Transform",
                "budget_range": "Around $400",
                "philosophy": "Systematically redefine the space's character",
                "typical_items": "Large rug + curtains + multiple lights + full pillow/throw set + art collection + large plants + shelving + scent diffuser"
            }
            ,
            "200": {
                "name": "Starter Refresh",
                "budget_range": "Around $200",
                "philosophy": "Quick upgrades with a few high-impact pieces",
                "typical_items": "One rug OR pillow set + small lamp + decor accents"
            },
            "400": {
                "name": "Core Upgrade",
                "budget_range": "Around $400",
                "philosophy": "Build a cohesive focal area with layered textures",
                "typical_items": "Rug + pillow set + floor lamp + wall art + plant"
            },
            "800": {
                "name": "Full Room Refresh",
                "budget_range": "Around $800",
                "philosophy": "Complete styling across floor, seating, wall, and lighting layers",
                "typical_items": "Medium rug + pillow/throw set + lighting combo + wall art + plant group + decor"
            },
            "1500": {
                "name": "Premium Overhaul",
                "budget_range": "Around $1500",
                "philosophy": "Elevate the space with premium materials and full layering",
                "typical_items": "Large rug + multiple lights + full textile set + art collection + plants + shelving"
            }
        },

        "room_context": {
            "living_room": {
                "name": "Living Room",
                "focus": "Sofa area is the absolute visual center"
            },
            "bedroom": {
                "name": "Bedroom",
                "focus": "Headboard area is the visual focal point"
            },
            "study": {
                "name": "Home Office",
                "focus": "Desk is the functional core"
            },
            "balcony": {
                "name": "Balcony",
                "focus": "Utilize natural light advantage"
            },
            "dining_room": {
                "name": "Dining Room",
                "focus": "Dining table is the absolute center"
            },
            "other": {
                "name": "Other Space",
                "focus": "Analyze based on specific function"
            }
        },

        "user_prompt_template": """## Task
Based on this {room_name} photo, generate a soft furnishing makeover rendering.

{space_analysis_section}

## Target Style: {style_name}
Core Principle: {design_principle}

Color Strategy:
- Main (60%): {color_base}
- Secondary (30%): {color_secondary}
- Accent (10%): {color_accent}

Material Language: {materials}

Recommended Items: {key_items}

Avoid: {avoid_items}

## Makeover Level: {budget_name} ({budget_range})
{budget_philosophy}

Reference Item Combo: {typical_items}

## Output Requirements
Generate the makeover rendering directly. Ensure:
1. New item sizes and proportions are realistic
2. Shadows match original environment exactly
3. Overall effect looks natural, like a real photo
4. All items are purchasable on e-commerce platforms

{custom_prompt_section}"""
    },

    "zh": {
        "system_prompt": """你是一位拥有20年经验的资深室内软装设计师，曾为顶级酒店和高端住宅完成过数百个项目。

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
    }
}

# =============================================================================
# API OPTIONS (for frontend dropdown)
# =============================================================================

API_OPTIONS = {
    "en": {
        "room_types": [
            {"value": "living_room", "label": "Living Room", "icon": "🛋️"},
            {"value": "bedroom", "label": "Bedroom", "icon": "🛏️"},
            {"value": "study", "label": "Home Office", "icon": "📚"},
            {"value": "dining_room", "label": "Dining Room", "icon": "🍽️"}
        ],
        "styles": [
            {"value": "boho", "label": "Boho", "description": "Eclectic, warm, layered textures"},
            {"value": "modern_minimalist", "label": "Modern Minimalist", "description": "Clean lines, calm neutral palette"},
            {"value": "scandinavian", "label": "Scandinavian", "description": "Bright, airy, natural wood tones"},
            {"value": "coastal", "label": "Coastal", "description": "Beach-inspired, light and breezy"},
            {"value": "industrial", "label": "Industrial", "description": "Raw textures, metal and wood"},
        ],
        "budgets": [
            {"value": "200", "label": "$200", "amount": 200, "description": "Quick makeover with key accents"},
            {"value": "400", "label": "$400", "amount": 400, "description": "Visible transformation with core items"},
            {"value": "800", "label": "$800", "amount": 800, "description": "Cohesive look for the entire room"},
            {"value": "1500", "label": "$1500", "amount": 1500, "description": "High-end redesign"},
        ]
    },
    "zh": {
        "room_types": [
            {"value": "living_room", "label": "客厅", "icon": "🛋️"},
            {"value": "bedroom", "label": "卧室", "icon": "🛏️"},
            {"value": "study", "label": "书房", "icon": "📚"},
            {"value": "balcony", "label": "阳台", "icon": "🌿"},
            {"value": "dining_room", "label": "餐厅", "icon": "🍽️"},
        ],
        "styles": [
            {"value": "nordic", "label": "北欧风格", "description": "功能主义，白+原木+莫兰迪色"},
            {"value": "japanese", "label": "日式风格", "description": "侘寂美学，低重心，留白呼吸感"},
            {"value": "vintage", "label": "复古中古", "description": "时间质感，深木+黄铜+丝绒"},
            {"value": "modern_luxury", "label": "现代轻奢", "description": "克制奢华，高级灰+金属点缀"},
            {"value": "natural", "label": "自然风格", "description": "城市绿洲，大地色系+绿植"},
            {"value": "minimalist", "label": "极简风格", "description": "Less is more，负空间设计"},
        ],
        "budgets": [
            {"value": "low", "label": "点睛改造", "amount": 300, "description": "1-2件视觉焦点"},
            {"value": "medium", "label": "氛围升级", "amount": 500, "description": "核心场景构建"},
            {"value": "high", "label": "质感重塑", "amount": 1000, "description": "四层次全面优化"},
            {"value": "premium", "label": "风格焕新", "amount": 2000, "description": "系统性空间升级"},
        ]
    }
}


def get_prompts(service: str, lang: str = "en") -> dict:
    """Get prompts for a specific service and language"""
    lang = lang if lang in ["en", "zh"] else "en"

    if service == "space_analyzer":
        return SPACE_ANALYZER_PROMPTS.get(lang, SPACE_ANALYZER_PROMPTS["en"])
    elif service == "item_identifier":
        return ITEM_IDENTIFIER_PROMPTS.get(lang, ITEM_IDENTIFIER_PROMPTS["en"])
    elif service == "image_generator":
        return IMAGE_GENERATOR_PROMPTS.get(lang, IMAGE_GENERATOR_PROMPTS["en"])
    elif service == "api_options":
        return API_OPTIONS.get(lang, API_OPTIONS["en"])
    else:
        return {}

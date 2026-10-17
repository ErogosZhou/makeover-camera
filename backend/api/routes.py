"""
换装相机 API 路由定义
支持本地存储和腾讯云 COS 存储
"""
import os
import uuid
import aiofiles
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Form
from fastapi.responses import JSONResponse, StreamingResponse
from loguru import logger

from config.settings import settings
from models.schemas import (
    GenerateRequest, UploadResponse, GenerationResult,
    TaskStatusResponse, TaskStatus, OptionsResponse,
    StyleOption, BudgetOption, StyleType, BudgetLevel, RoomType,
    ShoppingItem
)
from services.image_generator import ImageGeneratorService
from services.item_identifier import ItemIdentifierService
from services.product_matcher import ProductMatcherService
from services.product_service import unified_product_service
from services.space_analyzer import space_analyzer
from services.cos_storage import cos_storage
from services.prompts_i18n import get_prompts, API_OPTIONS

router = APIRouter()

# 内存任务存储（生产环境应使用Redis或数据库）
tasks_store: dict[str, GenerationResult] = {}

# 服务实例
image_generator = ImageGeneratorService()
item_identifier = ItemIdentifierService()
product_matcher = ProductMatcherService()


# ============ 工具函数 ============

def get_upload_path(filename: str) -> str:
    """获取上传文件保存路径"""
    upload_dir = settings.UPLOAD_DIR
    os.makedirs(upload_dir, exist_ok=True)
    return os.path.join(upload_dir, filename)


def validate_image(file: UploadFile) -> None:
    """验证上传的图片"""
    # 检查文件类型
    if file.content_type not in ["image/jpeg", "image/png", "image/webp"]:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的图片格式: {file.content_type}。支持 JPEG, PNG, WebP"
        )
    
    # 检查文件扩展名
    ext = file.filename.split(".")[-1].lower() if file.filename else ""
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件扩展名: {ext}"
        )


# ============ API 路由 ============

@router.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "ok", "service": "换装相机 API"}


@router.get("/options", response_model=OptionsResponse)
async def get_options(lang: str = "zh"):
    """
    获取配置选项（房间类型、风格、预算）

    Args:
        lang: Language code ('en' for English, 'zh' for Chinese)
    """
    # Get localized options
    options = API_OPTIONS.get(lang, API_OPTIONS.get("zh", {}))

    room_types = options.get("room_types", [])

    styles = [
        StyleOption(
            value=s["value"],
            label=s["label"],
            description=s["description"]
        )
        for s in options.get("styles", [])
    ]

    budgets = [
        BudgetOption(
            value=b["value"],
            label=b["label"],
            amount=b["amount"],
            description=b["description"]
        )
        for b in options.get("budgets", [])
    ]

    return OptionsResponse(
        room_types=room_types,
        styles=styles,
        budgets=budgets
    )


@router.get("/design-brief")
async def get_design_brief(
    room_type: str = "living_room",
    style: str = "nordic",
    budget: str = "medium"
):
    """
    获取设计简报（静态模板版本）- 已废弃，请使用 /analyze-space
    """
    try:
        room_type_enum = RoomType(room_type)
        style_enum = StyleType(style)
        budget_enum = BudgetLevel(budget)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"无效的参数: {e}")
    
    brief = image_generator.get_design_brief(room_type_enum, style_enum, budget_enum)
    return brief


@router.post("/analyze-space")
async def analyze_space(
    image_id: str = Form(...),
    room_type: str = Form(default="living_room"),
    style: str = Form(default="nordic"),
    budget: str = Form(default="medium"),
    lang: str = Form(default="zh")
):
    """
    AI 空间分析 - 已禁用以提升性能

    返回空响应，保持API兼容性
    """
    # 空间分析已禁用，返回空流式响应
    async def stream_body():
        yield ""

    return StreamingResponse(stream_body(), media_type="text/plain; charset=utf-8")


@router.post("/upload", response_model=UploadResponse)
async def upload_image(file: UploadFile = File(...)):
    """
    上传房间照片

    返回图片ID，用于后续生成请求
    支持本地存储和 COS 云存储
    """
    # 验证图片
    validate_image(file)

    # 读取文件内容
    content = await file.read()

    # 检查文件大小
    if len(content) > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"文件过大，最大支持 {settings.MAX_UPLOAD_SIZE // 1024 // 1024}MB"
        )

    # 生成唯一文件名
    ext = file.filename.split(".")[-1].lower() if file.filename else "jpg"
    image_id = str(uuid.uuid4())
    filename = f"{image_id}.{ext}"

    try:
        # 优先使用 COS 存储（Serverless 环境）
        if cos_storage.enabled:
            image_url = await cos_storage.upload_file(
                file_content=content,
                filename=filename,
                content_type=file.content_type or "image/jpeg",
                folder="uploads"
            )
            if image_url:
                logger.info(f"图片上传到 COS 成功: {image_url}")
                return UploadResponse(
                    success=True,
                    image_id=image_id,
                    image_url=image_url,
                    message="上传成功"
                )
            else:
                logger.warning("COS 上传失败，回退到本地存储")

        # 本地存储（开发环境或 COS 失败时）
        filepath = get_upload_path(filename)
        async with aiofiles.open(filepath, "wb") as f:
            await f.write(content)

        logger.info(f"图片上传到本地成功: {filepath}")

        return UploadResponse(
            success=True,
            image_id=image_id,
            image_url=f"/uploads/{filename}",
            message="上传成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"图片上传失败: {e}")
        raise HTTPException(status_code=500, detail="图片上传失败")


@router.post("/generate", response_model=TaskStatusResponse)
async def generate_renovation(
    background_tasks: BackgroundTasks,
    image_id: str = Form(...),
    room_type: str = Form(default="living_room"),
    style: str = Form(default="nordic"),
    budget: str = Form(default="medium"),
    custom_prompt: Optional[str] = Form(default=None),
    lang: str = Form(default="zh")
):
    """
    发起改造生成任务
    
    这是一个异步任务，会立即返回task_id，通过 /task/{task_id} 查询进度
    """
    # 验证参数
    try:
        room_type_enum = RoomType(room_type)
        style_enum = StyleType(style)
        budget_enum = BudgetLevel(budget)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"无效的参数: {e}")
    
    # 检查图片是否存在
    # 查找图片文件
    upload_dir = settings.UPLOAD_DIR
    image_path = None
    for ext in settings.ALLOWED_EXTENSIONS:
        potential_path = os.path.join(upload_dir, f"{image_id}.{ext}")
        if os.path.exists(potential_path):
            image_path = potential_path
            break
    
    if not image_path:
        raise HTTPException(status_code=404, detail="图片不存在，请先上传")
    
    # 创建任务
    task_id = str(uuid.uuid4())
    task = GenerationResult(
        task_id=task_id,
        status=TaskStatus.PENDING,
        original_image_url=f"/uploads/{os.path.basename(image_path)}",
        created_at=datetime.now()
    )
    tasks_store[task_id] = task
    
    # 启动后台任务
    background_tasks.add_task(
        process_generation_task,
        task_id=task_id,
        image_path=image_path,
        room_type=room_type_enum,
        style=style_enum,
        budget=budget_enum,
        custom_prompt=custom_prompt,
        lang=lang
    )
    
    return TaskStatusResponse(
        task_id=task_id,
        status=TaskStatus.PENDING,
        progress=0,
        message="任务已创建，正在处理中..."
    )


async def process_generation_task(
    task_id: str,
    image_path: str,
    room_type: RoomType,
    style: StyleType,
    budget: BudgetLevel,
    custom_prompt: Optional[str],
    lang: str = "zh"
):
    """
    后台处理生成任务
    
    流程：
    0. 调用空间分析服务分析原图（用于增强生成效果）
    1. 调用图片生成服务生成效果图
    2. 调用物品识别服务识别效果图中的物品
    3. 对每个物品调用商品匹配服务搜索相似商品
    4. 汇总结果
    """
    task = tasks_store.get(task_id)
    if not task:
        logger.error(f"任务不存在: {task_id}")
        return
    
    try:
        # Step 0: 空间分析（已禁用以提升性能）
        logger.info(f"[{task_id}] Step 0: 跳过空间分析（已禁用）")
        space_analysis = None  # 文本分析
        image_prompt = None    # 生图提示词
        # 注释掉空间分析调用
        # try:
        #     analysis_result = await space_analyzer.analyze(
        #         image_path=image_path,
        #         room_type=room_type,
        #         style=style,
        #         budget=budget,
        #         lang=lang
        #     )
        #     if analysis_result:
        #         space_analysis = analysis_result.get("analysis_text")
        #         image_prompt = analysis_result.get("image_prompt")
        #     logger.info(f"[{task_id}] 空间分析完成")
        # except Exception as e:
        #     logger.warning(f"[{task_id}] 空间分析失败，继续生成: {e}")
        
        # Step 1: 生成效果图
        task.status = TaskStatus.GENERATING
        logger.info(f"[{task_id}] Step 1: 开始生成效果图")

        # 定义进度回调函数
        async def generation_progress_callback(percentage: int, message: str):
            """图片生成进度回调"""
            logger.info(f"[{task_id}] 生成进度: {percentage}% - {message}")
            # 可以在这里更新任务的progress字段，前端轮询时会看到
            # 但目前的GenerationResult模型没有progress字段，所以只记录日志

        try:
            generated_image_url = await image_generator.generate(
                original_image_path=image_path,
                room_type=room_type,
                style=style,
                budget=budget,
                custom_prompt=custom_prompt,
                space_analysis=space_analysis,  # 传入空间分析结果（文本）
                image_prompt=image_prompt,      # 传入模型标记的提示词
                lang=lang,
                progress_callback=generation_progress_callback  # ✨ 传入进度回调
            )
            task.generated_image_url = generated_image_url
        except NotImplementedError as e:
            # API未实现，记录错误但继续流程（方便测试）
            logger.warning(f"[{task_id}] 图片生成服务未实现: {e}")
            task.error_message = str(e)
            task.status = TaskStatus.FAILED
            return
        except Exception as e:
            logger.error(f"[{task_id}] 图片生成失败: {e}")
            task.error_message = f"图片生成失败: {str(e)}"
            task.status = TaskStatus.FAILED
            return
        
        # Step 2 & 3: 流式识别物品 + 边识别边匹配
        # 使用流式API，每识别到一个物品就立即开始商品匹配
        task.status = TaskStatus.IDENTIFYING
        logger.info(f"[{task_id}] Step 2&3: 开始流式识别物品并匹配商品")

        shopping_list = []
        total_price = 0
        generated_image_path = generated_image_url
        item_count = 0

        try:
            async for item in item_identifier.identify_stream(
                generated_image_path=generated_image_path,
                original_image_path=image_path,
                lang=lang
            ):
                item_count += 1
                logger.info(f"[{task_id}] 识别到物品 #{item_count}: {item.name}，立即开始匹配")

                # 切换到匹配状态（首次）
                if task.status == TaskStatus.IDENTIFYING:
                    task.status = TaskStatus.MATCHING

                try:
                    matched_products = await unified_product_service.match_products_for_item(
                        item=item,
                        generated_image_path=generated_image_path,
                        lang=lang,
                        limit=5
                    )

                    shopping_item = ShoppingItem(
                        identified_item=item,
                        matched_products=matched_products
                    )
                    shopping_list.append(shopping_item)

                    if matched_products:
                        total_price += min(p.price for p in matched_products)

                    logger.info(f"[{task_id}] 物品 {item.name} 匹配完成，找到 {len(matched_products)} 个商品")

                except Exception as e:
                    logger.warning(f"[{task_id}] 匹配商品失败 ({item.name}): {e}")
                    shopping_item = ShoppingItem(
                        identified_item=item,
                        matched_products=[]
                    )
                    shopping_list.append(shopping_item)

        except NotImplementedError as e:
            logger.warning(f"[{task_id}] 物品识别服务未实现: {e}")
            task.error_message = str(e)
            task.status = TaskStatus.FAILED
            return
        except Exception as e:
            logger.error(f"[{task_id}] 物品识别失败: {e}")
            task.error_message = f"物品识别失败: {str(e)}"
            task.status = TaskStatus.FAILED
            return

        logger.info(f"[{task_id}] 流式识别+匹配完成，共处理 {item_count} 个物品")
        
        # Step 4: 完成
        task.shopping_list = shopping_list
        task.total_estimated_price = total_price
        task.space_analysis = space_analysis  # 保存空间分析结果
        task.status = TaskStatus.COMPLETED
        task.completed_at = datetime.now()
        
        logger.info(f"[{task_id}] 任务完成，识别 {len(shopping_list)} 个物品")
        
    except Exception as e:
        logger.error(f"[{task_id}] 任务处理异常: {e}")
        task.status = TaskStatus.FAILED
        task.error_message = str(e)


@router.get("/task/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """
    查询任务状态
    """
    task = tasks_store.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    # 计算进度
    progress_map = {
        TaskStatus.PENDING: 0,
        TaskStatus.GENERATING: 30,
        TaskStatus.IDENTIFYING: 60,
        TaskStatus.MATCHING: 80,
        TaskStatus.COMPLETED: 100,
        TaskStatus.FAILED: 0
    }
    
    message_map = {
        TaskStatus.PENDING: "任务等待处理...",
        TaskStatus.GENERATING: "正在生成效果图...",
        TaskStatus.IDENTIFYING: "正在识别物品...",
        TaskStatus.MATCHING: "正在匹配商品...",
        TaskStatus.COMPLETED: "完成！",
        TaskStatus.FAILED: f"失败: {task.error_message or '未知错误'}"
    }
    
    # 构建部分结果：VLLM生成prompt后、图片生成完成后就返回部分结果，让前端可以先展示
    partial_result = None
    # 🆕 GENERATING状态也返回结果（用于展示VLLM生成的prompt）
    if task.status in [TaskStatus.GENERATING, TaskStatus.IDENTIFYING, TaskStatus.MATCHING, TaskStatus.COMPLETED]:
        partial_result = GenerationResult(
            task_id=task_id,
            status=task.status,
            original_image_url=task.original_image_url,
            generated_image_url=task.generated_image_url,
            generation_prompt=task.generation_prompt,  # 🆕 返回VLLM生成的prompt
            shopping_list=task.shopping_list if task.status == TaskStatus.COMPLETED else [],
            total_estimated_price=task.total_estimated_price if task.status == TaskStatus.COMPLETED else None,
            space_analysis=task.space_analysis,
            created_at=task.created_at,
            completed_at=task.completed_at,
            error_message=task.error_message
        )

    return TaskStatusResponse(
        task_id=task_id,
        status=task.status,
        progress=progress_map.get(task.status, 0),
        message=message_map.get(task.status, ""),
        result=partial_result
    )


@router.get("/result/{task_id}", response_model=GenerationResult)
async def get_result(task_id: str):
    """
    获取完整结果
    """
    task = tasks_store.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    if task.status != TaskStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail=f"任务尚未完成，当前状态: {task.status.value}"
        )

    return task


# ============ V2 API - 零决策一键改造 ============

@router.post("/v2/transform", response_model=TaskStatusResponse)
async def transform_v2(
    background_tasks: BackgroundTasks,
    image_id: str = Form(...),
    lang: str = Form(default="en")
):
    """
    V2 一键改造 - 零决策

    用户只需上传图片，AI自动决定风格和预算。
    图片直接发给生图模型，省掉LLM分析环节。
    """
    # 检查图片是否存在
    upload_dir = settings.UPLOAD_DIR
    image_path = None
    for ext in settings.ALLOWED_EXTENSIONS:
        potential_path = os.path.join(upload_dir, f"{image_id}.{ext}")
        if os.path.exists(potential_path):
            image_path = potential_path
            break

    if not image_path:
        raise HTTPException(status_code=404, detail="图片不存在，请先上传")

    # 创建任务
    task_id = str(uuid.uuid4())
    task = GenerationResult(
        task_id=task_id,
        status=TaskStatus.PENDING,
        original_image_url=f"/uploads/{os.path.basename(image_path)}",
        created_at=datetime.now()
    )
    tasks_store[task_id] = task

    # 启动后台任务 - 使用v2处理流程
    background_tasks.add_task(
        process_transform_v2_task,
        task_id=task_id,
        image_path=image_path,
        lang=lang
    )

    return TaskStatusResponse(
        task_id=task_id,
        status=TaskStatus.PENDING,
        progress=0,
        message="正在为您的空间设计改造方案..."
    )


@router.post("/v2/transform/override", response_model=TaskStatusResponse)
async def transform_v2_override(
    background_tasks: BackgroundTasks,
    image_id: str = Form(...),
    style: str = Form(...),
    lang: str = Form(default="en")
):
    """
    V2 换风格 - 用户指定风格重新生成
    """
    # 验证风格参数
    try:
        style_enum = StyleType(style)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"无效的风格: {style}")

    # 检查图片是否存在
    upload_dir = settings.UPLOAD_DIR
    image_path = None
    for ext in settings.ALLOWED_EXTENSIONS:
        potential_path = os.path.join(upload_dir, f"{image_id}.{ext}")
        if os.path.exists(potential_path):
            image_path = potential_path
            break

    if not image_path:
        raise HTTPException(status_code=404, detail="图片不存在，请先上传")

    # 创建任务
    task_id = str(uuid.uuid4())
    task = GenerationResult(
        task_id=task_id,
        status=TaskStatus.PENDING,
        original_image_url=f"/uploads/{os.path.basename(image_path)}",
        created_at=datetime.now()
    )
    tasks_store[task_id] = task

    # 启动后台任务 - 使用指定风格
    background_tasks.add_task(
        process_transform_v2_task,
        task_id=task_id,
        image_path=image_path,
        lang=lang,
        override_style=style_enum
    )

    return TaskStatusResponse(
        task_id=task_id,
        status=TaskStatus.PENDING,
        progress=0,
        message=f"正在用 {style} 风格重新设计..."
    )


async def process_transform_v2_task(
    task_id: str,
    image_path: str,
    lang: str = "en",
    override_style: Optional[StyleType] = None
):
    """
    V2 后台处理任务

    流程（比v1更简化）：
    1. 图片直接发给生图模型（使用自动风格prompt或指定风格）
    2. 生成完成后，LLM识别效果图中的物品
    3. 匹配商品
    """
    import time
    start_time = time.time()
    timings = {}

    task = tasks_store.get(task_id)
    if not task:
        logger.error(f"任务不存在: {task_id}")
        return

    try:
        # Step 1: 生成效果图（直接发给生图模型）
        step1_start = time.time()
        task.status = TaskStatus.GENERATING
        logger.info(f"[{task_id}] V2 Step 1: 直接生成效果图")

        # 定义进度回调函数
        async def generation_progress_callback(percentage: int, message: str):
            """图片生成进度回调"""
            logger.info(f"[{task_id}] 🎨 生成进度: {percentage}% - {message}")

        # 🆕 定义prompt回调函数 - VLLM生成prompt后立即通知前端
        async def prompt_generated_callback(prompt_text: str):
            """VLLM生成prompt后的回调"""
            task.generation_prompt = prompt_text
            logger.info(f"[{task_id}] 📝 VLLM生成prompt完成: {len(prompt_text)}字，前端可开始打字机展示")

        # 🆕 用于存储物品匹配结果
        shopping_list = []
        total_price = 0
        match_time = 0
        items_queue = []  # 物品队列

        # 🆕 物品数组回调 - 每个物品立即开始匹配（与生图并发）
        async def items_stream_callback(item_name: str):
            """接收到物品后立即加入队列"""
            items_queue.append(item_name)
            logger.info(f"[{task_id}] 🎯 收到物品: {item_name} (队列长度: {len(items_queue)})")

        try:
            # 🆕 使用新版generate_v2_with_items，返回(图片, 设计文本, 物品数组)
            # 关键：items_callback会在VLLM生成物品数组时立即触发，与Seedream生图并发
            logger.info(f"[{task_id}] ⚡ 开始并发: VLLM生成 → Seedream生图 + 物品匹配")

            generated_image_dict, design_text, items_array = await image_generator.generate_v2_with_items(
                original_image_path=image_path,
                override_style=override_style,
                lang=lang,
                progress_callback=generation_progress_callback,
                prompt_callback=prompt_generated_callback,
                items_callback=items_stream_callback  # 🆕 物品流式回调
            )

            # 🆕 返回值现在是 dict: {"thumbnail_url": str, "full_url": str}
            task.generated_image_url = generated_image_dict.get("full_url")  # 主URL用完整图
            task.thumbnail_url = generated_image_dict.get("thumbnail_url")  # 新增缩略图URL
            task.generation_prompt = design_text
            timings['generate_image'] = time.time() - step1_start
            logger.info(f"[{task_id}] ⏱️  生成效果图耗时: {timings['generate_image']:.2f}秒")
            logger.info(f"[{task_id}] 📝 设计方案: {len(design_text)}字, 物品数量: {len(items_array)}个")

        except Exception as e:
            logger.error(f"[{task_id}] 图片生成失败: {e}")
            task.error_message = f"图片生成失败: {str(e)}"
            task.status = TaskStatus.FAILED
            return

        # Step 2: 匹配物品（使用VLLM生成的物品数组）
        step2_start = time.time()
        task.status = TaskStatus.MATCHING
        logger.info(f"[{task_id}] V2 Step 2: 流式匹配物品 (无需识别，直接用关键词搜索)")

        # 流式匹配：每个物品关键词立即搜索
        item_count = 0
        try:
            for item_name in items_queue:
                item_count += 1
                item_start = time.time()
                logger.info(f"[{task_id}] V2 匹配物品 #{item_count}: {item_name}")

                try:
                    match_start = time.time()

                    # 🆕 直接用关键词搜索商品（简化版IdentifiedItem）
                    from models.schemas import IdentifiedItem
                    import uuid
                    simple_item = IdentifiedItem(
                        id=f"item_{item_count}",  # 生成简单ID
                        name=item_name,
                        category="软装",  # 通用类别
                        description=item_name  # 使用关键词作为描述
                    )

                    matched_products = await unified_product_service.match_products_for_item(
                        item=simple_item,
                        generated_image_path=task.generated_image_url,  # 使用完整图URL
                        lang=lang,
                        limit=5
                    )
                    item_match_time = time.time() - match_start
                    match_time += item_match_time

                    shopping_item = ShoppingItem(
                        identified_item=simple_item,
                        matched_products=matched_products
                    )
                    shopping_list.append(shopping_item)

                    if matched_products:
                        total_price += min(p.price for p in matched_products)

                    item_total_time = time.time() - item_start
                    logger.info(f"[{task_id}] V2 物品 {item_name} 匹配完成 (匹配耗时: {item_match_time:.2f}秒, 总耗时: {item_total_time:.2f}秒)")

                except Exception as e:
                    logger.warning(f"[{task_id}] V2 匹配商品失败 ({item_name}): {e}")
                    # 创建失败的item对象
                    fallback_item = IdentifiedItem(
                        id=f"item_{item_count}",
                        name=item_name,
                        category="软装",
                        description=item_name
                    )
                    shopping_item = ShoppingItem(
                        identified_item=fallback_item,
                        matched_products=[]
                    )
                    shopping_list.append(shopping_item)

        except Exception as e:
            logger.error(f"[{task_id}] V2 物品识别失败: {e}")
            task.error_message = f"物品识别失败: {str(e)}"
            task.status = TaskStatus.FAILED
            return

        timings['identify_and_match'] = time.time() - step2_start
        timings['match_products'] = match_time
        logger.info(f"[{task_id}] V2 流式识别+匹配完成，共处理 {item_count} 个物品")
        logger.info(f"[{task_id}] ⏱️  识别+匹配总耗时: {timings['identify_and_match']:.2f}秒 (其中商品匹配: {match_time:.2f}秒)")

        # 完成
        task.shopping_list = shopping_list
        task.total_estimated_price = total_price
        task.status = TaskStatus.COMPLETED
        task.completed_at = datetime.now()

        total_time = time.time() - start_time
        timings['total'] = total_time

        logger.info(f"[{task_id}] V2任务完成，识别 {len(shopping_list)} 个物品")
        logger.info(f"[{task_id}] ⏱️  ========== 性能统计 ==========")
        logger.info(f"[{task_id}] ⏱️  生成效果图: {timings.get('generate_image', 0):.2f}秒 ({timings.get('generate_image', 0)/total_time*100:.1f}%)")
        logger.info(f"[{task_id}] ⏱️  识别+匹配: {timings.get('identify_and_match', 0):.2f}秒 ({timings.get('identify_and_match', 0)/total_time*100:.1f}%)")
        logger.info(f"[{task_id}] ⏱️    - 其中商品匹配: {timings.get('match_products', 0):.2f}秒")
        logger.info(f"[{task_id}] ⏱️  总耗时: {total_time:.2f}秒")
        logger.info(f"[{task_id}] ⏱️  平均每个物品: {total_time/len(shopping_list) if len(shopping_list) > 0 else 0:.2f}秒")
        logger.info(f"[{task_id}] ⏱️  ===============================")

    except Exception as e:
        logger.error(f"[{task_id}] V2任务处理异常: {e}")
        task.status = TaskStatus.FAILED
        task.error_message = str(e)


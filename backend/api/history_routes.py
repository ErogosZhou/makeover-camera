"""
历史记录 API 路由
"""
import uuid
import json
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query, Header
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, and_
from loguru import logger

from models.database import User, HistoryRecord, get_db
from services.auth import get_current_user_optional


router = APIRouter(prefix="/history", tags=["历史记录"])


# ============ 请求/响应模型 ============

class ShoppingItemBrief(BaseModel):
    """购物项简要信息"""
    name: str
    category: str
    price_estimate: Optional[str] = None


class HistoryRecordBrief(BaseModel):
    """历史记录简要信息（列表用）"""
    id: str
    created_at: datetime
    room_type: str
    style: str
    budget: str
    original_image_url: str
    generated_image_url: Optional[str] = None
    is_favorite: bool = False
    item_count: int = 0  # 识别出的物品数量


class HistoryRecordDetail(BaseModel):
    """历史记录详情"""
    id: str
    created_at: datetime
    room_type: str
    style: str
    budget: str
    original_image_url: str
    generated_image_url: Optional[str] = None
    shopping_list: Optional[List[dict]] = None
    total_price: Optional[float] = None
    is_favorite: bool = False


class HistoryListResponse(BaseModel):
    """历史记录列表响应"""
    items: List[HistoryRecordBrief]
    total: int
    page: int
    page_size: int
    has_more: bool


class CreateHistoryRequest(BaseModel):
    """创建历史记录请求"""
    original_image_url: str
    room_type: str
    style: str
    budget: str
    generated_image_url: Optional[str] = None
    shopping_list: Optional[List[dict]] = None
    total_price: Optional[float] = None


# ============ API 端点 ============

@router.get("", response_model=HistoryListResponse)
async def get_history_list(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    favorites_only: bool = Query(False),
    x_device_id: Optional[str] = Header(None),
    user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """
    获取历史记录列表

    - 登录用户：返回该用户的记录
    - 游客：根据 X-Device-ID 返回记录
    """
    # 构建查询条件
    conditions = [HistoryRecord.is_deleted == False]

    if user:
        conditions.append(HistoryRecord.user_id == user.id)
    elif x_device_id:
        conditions.append(HistoryRecord.device_id == x_device_id)
    else:
        # 无用户也无设备 ID，返回空
        return HistoryListResponse(
            items=[],
            total=0,
            page=page,
            page_size=page_size,
            has_more=False
        )

    if favorites_only:
        conditions.append(HistoryRecord.is_favorite == True)

    # 查询总数
    count_query = select(HistoryRecord).where(and_(*conditions))
    count_result = await db.execute(count_query)
    total = len(count_result.scalars().all())

    # 分页查询
    offset = (page - 1) * page_size
    query = (
        select(HistoryRecord)
        .where(and_(*conditions))
        .order_by(desc(HistoryRecord.created_at))
        .offset(offset)
        .limit(page_size)
    )
    result = await db.execute(query)
    records = result.scalars().all()

    # 转换为响应格式
    items = []
    for record in records:
        item_count = 0
        if record.shopping_list:
            try:
                shopping_data = json.loads(record.shopping_list)
                item_count = len(shopping_data)
            except:
                pass

        items.append(HistoryRecordBrief(
            id=record.id,
            created_at=record.created_at,
            room_type=record.room_type,
            style=record.style,
            budget=record.budget,
            original_image_url=record.original_image_url,
            generated_image_url=record.generated_image_url,
            is_favorite=record.is_favorite,
            item_count=item_count
        ))

    return HistoryListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        has_more=(offset + len(items)) < total
    )


@router.get("/{record_id}", response_model=HistoryRecordDetail)
async def get_history_detail(
    record_id: str,
    x_device_id: Optional[str] = Header(None),
    user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """获取历史记录详情"""
    result = await db.execute(
        select(HistoryRecord).where(HistoryRecord.id == record_id)
    )
    record = result.scalar_one_or_none()

    if not record or record.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Record not found"
        )

    # 权限检查
    if user:
        if record.user_id != user.id:
            raise HTTPException(status_code=403, detail="Permission denied")
    elif x_device_id:
        if record.device_id != x_device_id:
            raise HTTPException(status_code=403, detail="Permission denied")
    else:
        raise HTTPException(status_code=403, detail="Permission denied")

    shopping_list = None
    if record.shopping_list:
        try:
            shopping_list = json.loads(record.shopping_list)
        except:
            pass

    return HistoryRecordDetail(
        id=record.id,
        created_at=record.created_at,
        room_type=record.room_type,
        style=record.style,
        budget=record.budget,
        original_image_url=record.original_image_url,
        generated_image_url=record.generated_image_url,
        shopping_list=shopping_list,
        total_price=record.total_price,
        is_favorite=record.is_favorite
    )


@router.post("", response_model=HistoryRecordBrief)
async def create_history_record(
    request: CreateHistoryRequest,
    x_device_id: Optional[str] = Header(None),
    user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """
    创建历史记录

    通常在生成任务完成时自动调用
    """
    record = HistoryRecord(
        id=str(uuid.uuid4()),
        user_id=user.id if user else None,
        device_id=x_device_id if not user else None,
        original_image_url=request.original_image_url,
        room_type=request.room_type,
        style=request.style,
        budget=request.budget,
        generated_image_url=request.generated_image_url,
        shopping_list=json.dumps(request.shopping_list) if request.shopping_list else None,
        total_price=request.total_price
    )

    db.add(record)

    # 更新用户统计
    if user:
        user.total_generations += 1

    await db.commit()
    await db.refresh(record)

    item_count = len(request.shopping_list) if request.shopping_list else 0

    return HistoryRecordBrief(
        id=record.id,
        created_at=record.created_at,
        room_type=record.room_type,
        style=record.style,
        budget=record.budget,
        original_image_url=record.original_image_url,
        generated_image_url=record.generated_image_url,
        is_favorite=record.is_favorite,
        item_count=item_count
    )


@router.delete("/{record_id}")
async def delete_history_record(
    record_id: str,
    x_device_id: Optional[str] = Header(None),
    user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """删除历史记录（软删除）"""
    result = await db.execute(
        select(HistoryRecord).where(HistoryRecord.id == record_id)
    )
    record = result.scalar_one_or_none()

    if not record:
        raise HTTPException(status_code=404, detail="Record not found")

    # 权限检查
    if user:
        if record.user_id != user.id:
            raise HTTPException(status_code=403, detail="Permission denied")
    elif x_device_id:
        if record.device_id != x_device_id:
            raise HTTPException(status_code=403, detail="Permission denied")
    else:
        raise HTTPException(status_code=403, detail="Permission denied")

    record.is_deleted = True
    await db.commit()

    return {"message": "Record deleted"}


@router.post("/{record_id}/favorite")
async def toggle_favorite(
    record_id: str,
    x_device_id: Optional[str] = Header(None),
    user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """切换收藏状态"""
    result = await db.execute(
        select(HistoryRecord).where(HistoryRecord.id == record_id)
    )
    record = result.scalar_one_or_none()

    if not record or record.is_deleted:
        raise HTTPException(status_code=404, detail="Record not found")

    # 权限检查
    if user:
        if record.user_id != user.id:
            raise HTTPException(status_code=403, detail="Permission denied")
    elif x_device_id:
        if record.device_id != x_device_id:
            raise HTTPException(status_code=403, detail="Permission denied")
    else:
        raise HTTPException(status_code=403, detail="Permission denied")

    record.is_favorite = not record.is_favorite
    await db.commit()

    return {"is_favorite": record.is_favorite}


@router.post("/sync")
async def sync_local_history(
    records: List[CreateHistoryRequest],
    user: User = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """
    同步本地历史记录到云端

    用户登录后，将本地 localStorage 中的记录同步到服务端
    """
    if not user:
        raise HTTPException(status_code=401, detail="Login required")

    synced_count = 0
    for req in records:
        record = HistoryRecord(
            id=str(uuid.uuid4()),
            user_id=user.id,
            original_image_url=req.original_image_url,
            room_type=req.room_type,
            style=req.style,
            budget=req.budget,
            generated_image_url=req.generated_image_url,
            shopping_list=json.dumps(req.shopping_list) if req.shopping_list else None,
            total_price=req.total_price
        )
        db.add(record)
        synced_count += 1

    user.total_generations += synced_count
    await db.commit()

    return {"synced": synced_count}

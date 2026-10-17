"""
商品转链 API 路由
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from loguru import logger

from services.product_matcher import ProductMatcherService

router = APIRouter(prefix="/product", tags=["商品"])


class GenerateLinkRequest(BaseModel):
    """生成推广链接请求"""
    goods_sign: str
    platform: str = "pdd"  # pdd 或 taobao


class GenerateLinkResponse(BaseModel):
    """生成推广链接响应"""
    url: str


@router.post("/generate-link", response_model=GenerateLinkResponse)
async def generate_affiliate_link(request: GenerateLinkRequest):
    """
    生成推广链接（用户点击时调用）

    - goods_sign: 商品标识
    - platform: 平台（pdd/taobao）
    """
    if request.platform == "pdd":
        matcher = ProductMatcherService()
        try:
            url_map = await matcher._batch_generate_pdd_promotion_urls([request.goods_sign])
            url = url_map.get(request.goods_sign, "")

            if not url:
                # 如果转链失败，返回普通商品链接
                logger.warning(f"转链失败，使用普通链接: {request.goods_sign}")
                url = f"https://mobile.yangkeduo.com/goods.html?goods_sign={request.goods_sign}"

            return GenerateLinkResponse(url=url)

        except Exception as e:
            logger.error(f"生成推广链接失败: {e}")
            # 降级返回普通链接
            return GenerateLinkResponse(
                url=f"https://mobile.yangkeduo.com/goods.html?goods_sign={request.goods_sign}"
            )
        finally:
            await matcher.close()

    else:
        raise HTTPException(status_code=400, detail=f"不支持的平台: {request.platform}")

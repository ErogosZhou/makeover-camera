"""
换装相机 Product Search API — designed for LLM agents

Three endpoints:
  POST /search/keyword  — keyword search, returns product list
  POST /search/image    — image URL → identify items + search products
  POST /search/card     — pick one product by id, get back a shareable card image URL
"""
import os
import httpx
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from loguru import logger

from config.settings import settings
from models.schemas import IdentifiedItem, MatchedProduct
from services.product_matcher import ProductMatcherService
from services.item_identifier import ItemIdentifierService
from services.card_generator import generate_product_card

router = APIRouter(prefix="/search", tags=["Agent Search API"])


def _base_url(request: Request) -> str:
    """本地 demo：卡片 URL 直接由当前请求地址派生，可用 BASE_URL 环境变量覆盖"""
    override = os.getenv("BASE_URL")
    if override:
        return override.rstrip("/")
    return str(request.base_url).rstrip("/")


# ── Request / Response models ──────────────────────────────────────────────

class SearchRequest(BaseModel):
    query: str
    keywords: Optional[List[str]] = []
    category: Optional[str] = None
    limit: int = 5


class IdentifyRequest(BaseModel):
    image_url: str
    original_image_url: Optional[str] = None
    limit_per_item: int = 3


class CardRequest(BaseModel):
    """Generate a shareable product card image for one product."""
    goods_sign: str          # from search results: product.id (pdd goods_sign)
    product_name: str        # product.name
    price: float             # product.price
    original_price: Optional[float] = None
    image_url: str           # product.image_url
    platform: str = "pdd"


class ProductResult(BaseModel):
    id: str                  # goods_sign for pdd; use this in CardRequest.goods_sign
    name: str
    price: float
    original_price: Optional[float] = None
    image_url: str
    shop_name: Optional[str] = None
    sales: Optional[int] = None
    platform: str


class SearchResponse(BaseModel):
    query: str
    products: List[ProductResult]
    total: int


class ItemResult(BaseModel):
    name: str
    category: str
    description: str
    color: Optional[str] = None
    style: Optional[str] = None
    price_estimate: Optional[str] = None
    search_keywords: List[str]
    products: List[ProductResult]


class IdentifyResponse(BaseModel):
    items: List[ItemResult]
    total_items: int


class CardResponse(BaseModel):
    card_url: str            # publicly accessible image URL, send this directly to user


# ── Helpers ────────────────────────────────────────────────────────────────

def _to_product_result(p: MatchedProduct) -> ProductResult:
    return ProductResult(
        id=p.id,
        name=p.name,
        price=p.price,
        original_price=p.original_price,
        image_url=p.image_url,
        shop_name=p.shop_name,
        sales=p.sales,
        platform=p.platform,
    )


async def _download_image_to_temp(url: str) -> str:
    import tempfile
    async with httpx.AsyncClient(timeout=30.0, trust_env=False) as client:
        resp = await client.get(url)
        if resp.status_code != 200:
            raise HTTPException(status_code=400, detail=f"Cannot fetch image: {url} → {resp.status_code}")
        content_type = resp.headers.get("content-type", "image/jpeg")
        ext = "png" if "png" in content_type else "webp" if "webp" in content_type else "jpg"
        tmp = tempfile.NamedTemporaryFile(suffix=f".{ext}", delete=False)
        tmp.write(resp.content)
        tmp.close()
        return tmp.name


# ── Routes ─────────────────────────────────────────────────────────────────

@router.post("/keyword", response_model=SearchResponse, summary="Step 1: keyword product search")
async def search_by_keyword(req: SearchRequest):
    """
    Search products by keyword. Returns a ranked list.
    Use the product `id` (goods_sign) and other fields to call `/search/card` next.

    - **query**: main search string, use Chinese for best results
    - **limit**: 1-20, default 5
    """
    limit = max(1, min(req.limit, 20))
    fetch_limit = max(limit, 10)  # PDD requires pageSize >= 10

    all_keywords = [req.query] + (req.keywords or [])
    item = IdentifiedItem(
        id="search",
        name=req.query,
        category=req.category or "其他",
        description=req.query,
        search_keywords=all_keywords,
    )

    matcher = ProductMatcherService()
    try:
        products = await matcher.search_products(item, limit=fetch_limit)
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))
    finally:
        await matcher.close()

    results = [_to_product_result(p) for p in products[:limit]]
    return SearchResponse(query=req.query, products=results, total=len(results))


@router.post("/image", response_model=IdentifyResponse, summary="Identify items in image + search products")
async def search_by_image(req: IdentifyRequest):
    """
    Vision LLM identifies purchasable items in the image, then searches products for each.
    Returns items with product lists. Use product `id` to call `/search/card` next.
    """
    limit = max(1, min(req.limit_per_item, 10))
    fetch_limit = max(limit, 10)  # PDD requires pageSize >= 10

    generated_path = await _download_image_to_temp(req.image_url)
    original_path = None
    if req.original_image_url:
        original_path = await _download_image_to_temp(req.original_image_url)

    identifier = ItemIdentifierService()
    matcher = ProductMatcherService()

    try:
        identified_items = await identifier.identify(
            generated_image_path=generated_path,
            original_image_path=original_path,
        )
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Image identification failed: {e}")
        raise HTTPException(status_code=500, detail="Image identification failed")
    finally:
        try:
            os.unlink(generated_path)
        except Exception:
            pass
        if original_path:
            try:
                os.unlink(original_path)
            except Exception:
                pass

    item_results: List[ItemResult] = []
    for item in identified_items:
        try:
            products = await matcher.search_products(item, limit=fetch_limit)
        except Exception as e:
            logger.warning(f"Product search failed for {item.name}: {e}")
            products = []

        item_results.append(ItemResult(
            name=item.name,
            category=item.category,
            description=item.description,
            color=item.color,
            style=item.style,
            price_estimate=item.price_estimate,
            search_keywords=item.search_keywords,
            products=[_to_product_result(p) for p in products[:limit]],
        ))

    await matcher.close()
    return IdentifyResponse(items=item_results, total_items=len(item_results))


@router.post("/card", response_model=CardResponse, summary="Step 2: generate shareable product card")
async def generate_card(request: Request, req: CardRequest):
    """
    Takes one product (from search results), converts the PDD goods_sign into a real
    purchase URL, then generates a card image (product photo + price + QR code).

    Returns a `card_url` — an image URL you can send directly to the user in WeChat
    or any channel that doesn't support Markdown links.

    Fields come directly from a product in the `/search/keyword` or `/search/image` response:
    - **goods_sign**: product.id
    - **product_name**: product.name
    - **price**: product.price
    - **original_price**: product.original_price (optional)
    - **image_url**: product.image_url
    - **platform**: product.platform
    """
    # Step 1: convert goods_sign → real purchase URL
    matcher = ProductMatcherService()
    try:
        if req.platform == "pdd":
            url_map = await matcher._batch_generate_pdd_promotion_urls([req.goods_sign])
            purchase_url = url_map.get(req.goods_sign) or \
                f"https://mobile.yangkeduo.com/goods.html?goods_sign={req.goods_sign}"
        else:
            purchase_url = req.image_url  # fallback for other platforms
    except Exception as e:
        logger.warning(f"转链失败，使用降级链接: {e}")
        purchase_url = f"https://mobile.yangkeduo.com/goods.html?goods_sign={req.goods_sign}"
    finally:
        await matcher.close()

    # Step 2: generate card image
    upload_dir = settings.UPLOAD_DIR
    os.makedirs(upload_dir, exist_ok=True)

    try:
        card_path = await generate_product_card(
            product_name=req.product_name,
            price=req.price,
            original_price=req.original_price,
            image_url=req.image_url,
            purchase_url=purchase_url,
            platform=req.platform,
            upload_dir=upload_dir,
        )
    except Exception as e:
        logger.error(f"Card generation failed: {e}")
        raise HTTPException(status_code=500, detail="Card generation failed")

    filename = os.path.basename(card_path)
    card_url = f"{_base_url(request)}/uploads/{filename}"
    return CardResponse(card_url=card_url)

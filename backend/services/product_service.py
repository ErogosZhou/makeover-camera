"""
Unified Product Service
聚焦国内市场（中国）- 仅支持拼多多、Temu 等国内电商平台

注意：国际市场代码已归档到 _archive_international/
"""
from typing import Optional, List
from loguru import logger

from config.settings import settings
from models.schemas import IdentifiedItem, MatchedProduct
from services.product_matcher import ProductMatcherService
# 国际市场已归档：from services.amazon_product import AmazonProductService, IkeaProductService


class UnifiedProductService:
    """
    统一商品搜索服务（国内市场）

    当前仅支持国内电商平台：
    - 拼多多多多进宝（主力，5-8% 佣金）
    - Temu 国内版（高佣金，10-20%）

    国际市场（Amazon/IKEA）已归档到 _archive_international/
    """

    def __init__(self):
        self._domestic_service: Optional[ProductMatcherService] = None
        # 国际市场已归档
        # self._amazon_service: Optional[AmazonProductService] = None
        # self._ikea_service: Optional[IkeaProductService] = None

    def _get_domestic_service(self) -> ProductMatcherService:
        if self._domestic_service is None:
            self._domestic_service = ProductMatcherService()
        return self._domestic_service

    # 国际市场已归档 - 如需恢复请参考 _archive_international/CLEANUP_NOTES.md
    # def _get_amazon_service(self) -> AmazonProductService:
    #     if self._amazon_service is None:
    #         self._amazon_service = AmazonProductService()
    #     return self._amazon_service

    # def _get_ikea_service(self) -> IkeaProductService:
    #     if self._ikea_service is None:
    #         self._ikea_service = IkeaProductService()
    #     return self._ikea_service

    def _has_domestic_config(self) -> bool:
        """检查国内电商 API 是否配置（拼多多/Temu）"""
        has_pdd = settings.PDD_CLIENT_ID and settings.PDD_CLIENT_SECRET and settings.PDD_PID
        # Taobao 和 Dataoke 暂时不用
        # has_taobao = settings.TAOBAO_APP_KEY and settings.TAOBAO_APP_SECRET
        # has_dataoke = settings.DATAOKE_APP_KEY and settings.DATAOKE_APP_SECRET
        return has_pdd

    # 国际市场已归档
    # def _has_international_config(self) -> bool:
    #     """Check if international APIs are configured"""
    #     has_amazon = (
    #         (settings.AMAZON_ACCESS_KEY and settings.AMAZON_SECRET_KEY) or
    #         settings.RAPIDAPI_KEY or
    #         getattr(settings, 'SERPAPI_KEY', None)
    #     )
    #     return has_amazon

    async def search_products(
        self,
        item: IdentifiedItem,
        lang: str = "zh",  # 默认中文
        limit: int = 10
    ) -> List[MatchedProduct]:
        """
        搜索商品（仅国内市场）

        Args:
            item: 识别到的物品
            lang: 语言代码（仅支持 'zh'）
            limit: 最大结果数

        Returns:
            匹配的商品列表
        """
        # 仅支持国内市场
        if self._has_domestic_config():
            logger.info(f"使用国内商品服务搜索: {item.name}")
            service = self._get_domestic_service()
            return await service.search_products(item, limit)
        else:
            logger.error("拼多多 API 未配置")
            raise ValueError(
                "拼多多 API 未配置。请在 .env 中设置：\n"
                "- PDD_CLIENT_ID\n"
                "- PDD_CLIENT_SECRET\n"
                "- PDD_PID"
            )

    async def match_products_for_item(
        self,
        item: IdentifiedItem,
        generated_image_path: str,
        lang: str = "zh",  # 默认中文
        limit: int = 5,
        similarity_threshold: float = 60.0
    ) -> List[MatchedProduct]:
        """
        Match products for a single identified item

        Args:
            item: The identified item
            generated_image_path: Path to generated image (for future visual matching)
            lang: Language code
            limit: Maximum number of results
            similarity_threshold: Minimum similarity score (for future use)

        Returns:
            List of matched products
        """
        logger.info(f"Matching products for: {item.name} (category: {item.category}, lang: {lang})")

        # Search for candidates
        candidates = await self.search_products(item, lang=lang, limit=20)

        if not candidates:
            logger.warning(f"No products found for: {item.name}")
            return []

        # Sort by sales/reviews
        candidates.sort(key=lambda p: (p.sales or 0), reverse=True)

        return candidates[:limit]

    async def search_multiple_sources(
        self,
        item: IdentifiedItem,
        limit_per_source: int = 5
    ) -> List[MatchedProduct]:
        """
        Search from multiple sources (Amazon + IKEA) for better coverage

        Useful for furniture items where IKEA might have better matches
        """
        results = []

        # Search Amazon
        if self._has_international_config():
            try:
                amazon_results = await self._get_amazon_service().search_products(item, limit_per_source)
                results.extend(amazon_results)
            except Exception as e:
                logger.warning(f"Amazon search failed: {e}")

        # Search IKEA (good for furniture)
        furniture_categories = ["Furniture", "Textiles", "Lighting", "Storage"]
        if item.category in furniture_categories:
            try:
                ikea_service = self._get_ikea_service()
                keyword = f"{item.style or ''} {item.name}".strip()
                ikea_results = await ikea_service.search_products(keyword, limit_per_source)
                results.extend(ikea_results)
            except Exception as e:
                logger.warning(f"IKEA search failed: {e}")

        # Deduplicate and sort
        seen_ids = set()
        unique_results = []
        for p in results:
            if p.id not in seen_ids:
                seen_ids.add(p.id)
                unique_results.append(p)

        # Sort by sales/reviews
        unique_results.sort(key=lambda p: (p.sales or 0), reverse=True)

        return unique_results

    async def close(self):
        """Close all service connections"""
        if self._domestic_service:
            await self._domestic_service.close()
        if self._amazon_service:
            await self._amazon_service.close()
        if self._ikea_service:
            await self._ikea_service.close()


# Global instance
unified_product_service = UnifiedProductService()

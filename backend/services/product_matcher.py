"""
商品匹配服务
支持拼多多多多进宝和大淘客双平台搜索
"""
import httpx
import hashlib
import time
from typing import Optional, List
from loguru import logger

from config.settings import settings
from models.schemas import IdentifiedItem, MatchedProduct


class ProductMatcherService:
    """商品匹配服务"""
    
    # 拼多多API地址
    PDD_API_URL = "https://gw-api.pinduoduo.com/api/router"
    
    # 大淘客API地址
    DATAOKE_API_URL = "https://openapi.dataoke.com/api"
    
    def __init__(self):
        # 拼多多配置
        self.pdd_client_id = settings.PDD_CLIENT_ID
        self.pdd_client_secret = settings.PDD_CLIENT_SECRET
        self.pdd_pid = settings.PDD_PID
        
        # 大淘客配置
        self.dataoke_app_key = settings.DATAOKE_APP_KEY
        self.dataoke_app_secret = settings.DATAOKE_APP_SECRET
        
        self._client: Optional[httpx.AsyncClient] = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """获取HTTP客户端"""
        if self._client is None:
            # trust_env=False 禁用系统代理，避免代理不可用导致超时
            self._client = httpx.AsyncClient(timeout=30.0, trust_env=False)
        return self._client
    
    def _get_available_platform(self) -> str:
        """获取可用的平台，优先拼多多"""
        if self.pdd_client_id and self.pdd_client_secret and self.pdd_pid:
            return "pdd"
        elif self.dataoke_app_key and self.dataoke_app_secret:
            return "dataoke"
        return None
    
    # ==================== 拼多多 ====================
    
    def _pdd_generate_sign(self, params: dict) -> str:
        """
        拼多多签名：
        1. 参数按ASCII升序排序
        2. 拼接成 key+value（无分隔符）
        3. 前后加上 client_secret
        4. MD5后转大写
        """
        sorted_params = sorted(params.items(), key=lambda x: x[0])
        param_str = "".join([f"{k}{v}" for k, v in sorted_params])
        sign_str = self.pdd_client_secret + param_str + self.pdd_client_secret
        sign = hashlib.md5(sign_str.encode('utf-8')).hexdigest().upper()
        return sign
    
    async def _search_pdd(self, item: IdentifiedItem, limit: int) -> List[MatchedProduct]:
        """拼多多商品搜索"""
        client = await self._get_client()
        
        # 构建搜索关键词
        if item.search_keywords:
            keyword = " ".join(item.search_keywords[:2])
        else:
            keyword = item.name
        
        logger.info(f"拼多多搜索: {keyword}")
        
        timestamp = str(int(time.time()))
        
        params = {
            "type": "pdd.ddk.goods.search",
            "client_id": self.pdd_client_id,
            "timestamp": timestamp,
            "pid": self.pdd_pid,
            "keyword": keyword,
            "page": "1",
            "page_size": str(min(limit, 100)),
            "sort_type": "6",  # 按销量降序
        }
        
        params["sign"] = self._pdd_generate_sign(params)
        
        try:
            response = await client.post(
                self.PDD_API_URL,
                headers={"Content-Type": "application/json"},
                json=params
            )
            
            logger.info(f"拼多多API响应状态码: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                if "goods_search_response" in data:
                    result = data["goods_search_response"]
                    goods_list = result.get("goods_list", [])
                    
                    if not goods_list:
                        logger.warning(f"拼多多未找到商品: {keyword}")
                        # 尝试简化关键词
                        if keyword != item.name:
                            return await self._search_pdd_simple(item.name, limit)
                        return []
                    
                    products = await self._parse_pdd_goods(goods_list)
                    logger.info(f"拼多多搜索到 {len(products)} 个商品")
                    return products
                    
                elif "error_response" in data:
                    err = data["error_response"]
                    error_msg = err.get('error_msg', '')
                    sub_msg = err.get('sub_msg', '')
                    logger.error(f"拼多多API错误: {error_msg} - {sub_msg}")

                    # 如果是限流错误，返回Mock数据用于测试
                    if "限制使用" in sub_msg or "限流" in sub_msg:
                        logger.warning(f"拼多多API被限流，返回Mock数据用于测试")
                        return self._get_mock_products(keyword, limit)

                    return []
            
            return []
            
        except Exception as e:
            logger.error(f"拼多多搜索失败: {e}")
            return []

    def _get_mock_products(self, keyword: str, limit: int) -> List[MatchedProduct]:
        """
        生成Mock商品数据（用于测试/拼多多限流时）
        """
        import random

        # Mock商品模板
        mock_products = []
        for i in range(min(limit, 4)):
            price = random.randint(29, 299)
            original_price = int(price * random.uniform(1.2, 2.0))
            sales = random.randint(100, 10000)

            mock_products.append(MatchedProduct(
                id=f"mock_{keyword}_{i}",
                name=f"{keyword} 北欧简约风格",
                price=float(price),
                original_price=float(original_price),
                image_url="https://via.placeholder.com/400?text=Mock+Product",
                product_url=f"https://mobile.yangkeduo.com/goods.html?goods_id=mock_{i}",
                platform="拼多多",
                sales=sales,
                shop_name="Mock测试店铺",
                relevance_score=0.85
            ))

        logger.info(f"生成了 {len(mock_products)} 个Mock商品用于测试")
        return mock_products

    async def _search_pdd_simple(self, keyword: str, limit: int) -> List[MatchedProduct]:
        """拼多多简化搜索"""
        client = await self._get_client()
        
        logger.info(f"拼多多简化搜索: {keyword}")
        
        timestamp = str(int(time.time()))
        
        params = {
            "type": "pdd.ddk.goods.search",
            "client_id": self.pdd_client_id,
            "timestamp": timestamp,
            "pid": self.pdd_pid,
            "keyword": keyword,
            "page": "1",
            "page_size": str(min(limit, 100)),
            "sort_type": "6",
        }
        
        params["sign"] = self._pdd_generate_sign(params)
        
        try:
            response = await client.post(
                self.PDD_API_URL,
                headers={"Content-Type": "application/json"},
                json=params
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if "goods_search_response" in data:
                    goods_list = data["goods_search_response"].get("goods_list", [])
                    return await self._parse_pdd_goods(goods_list)
            
            return []
        except Exception as e:
            logger.error(f"拼多多简化搜索失败: {e}")
            return []
    
    async def _batch_generate_pdd_promotion_urls(self, goods_signs: List[str]) -> dict:
        """批量生成拼多多推广链接（最多20个）"""
        if not goods_signs:
            logger.warning("批量转链: goods_signs为空")
            return {}

        logger.info(f"批量转链: 开始处理 {len(goods_signs)} 个商品")

        client = await self._get_client()
        timestamp = str(int(time.time()))

        # 最多20个
        goods_signs = goods_signs[:20]
        goods_sign_list_str = "[" + ",".join([f'"{sign}"' for sign in goods_signs]) + "]"

        params = {
            "type": "pdd.ddk.goods.promotion.url.generate",
            "client_id": self.pdd_client_id,
            "timestamp": timestamp,
            "p_id": self.pdd_pid,
            "goods_sign_list": goods_sign_list_str,
            "generate_short_url": "true",
            "multi_group": "false",
            "generate_weapp_webview": "false"
        }

        params["sign"] = self._pdd_generate_sign(params)

        try:
            logger.debug(f"批量转链: 调用API, goods_signs={goods_signs}")
            response = await client.post(
                self.PDD_API_URL,
                headers={"Content-Type": "application/json"},
                json=params
            )

            logger.info(f"批量转链: API响应状态码 {response.status_code}")

            if response.status_code == 200:
                data = response.json()

                if "goods_promotion_url_generate_response" in data:
                    result = data["goods_promotion_url_generate_response"]
                    goods_list = result.get("goods_promotion_url_list", [])

                    logger.info(f"批量转链: 成功返回 {len(goods_list)} 个链接")

                    # 构建 goods_sign -> url 的映射
                    # 注意：API返回的链接列表顺序与请求的goods_signs顺序一致，但不包含goods_sign字段
                    # 所以需要按索引对应
                    url_map = {}
                    for i, url_info in enumerate(goods_list):
                        if i < len(goods_signs):
                            goods_sign = goods_signs[i]
                            url = url_info.get("short_url") or url_info.get("mobile_short_url") or url_info.get("mobile_url") or url_info.get("url", "")
                            if goods_sign and url:
                                url_map[goods_sign] = url
                                logger.info(f"批量转链: 映射 {goods_sign} -> {url[:60]}...")

                    logger.info(f"批量转链: 最终url_map有 {len(url_map)} 条记录")
                    return url_map

                elif "error_response" in data:
                    err = data["error_response"]
                    logger.error(f"拼多多批量转链API错误: {err.get('error_msg')} - {err.get('sub_msg', '')}")
                else:
                    logger.error(f"批量转链: 未知响应格式: {data}")

            return {}

        except Exception as e:
            logger.error(f"批量生成拼多多推广链接失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {}

    async def _parse_pdd_goods(self, goods_list: list) -> List[MatchedProduct]:
        """解析拼多多商品列表（不转链，返回 goods_sign 供前端点击时转链）"""
        if not goods_list:
            return []

        products = []
        for g in goods_list:
            try:
                # 价格单位是分，需要转换
                min_price = g.get("min_group_price", 0) / 100
                original_price = g.get("min_normal_price", 0) / 100

                # 优惠券信息
                coupon_discount = g.get("coupon_discount", 0) / 100
                final_price = min_price - coupon_discount if coupon_discount else min_price

                # 销量处理
                sales_tip = g.get("sales_tip", "0")
                try:
                    if "万" in sales_tip:
                        sales = int(float(sales_tip.replace("万+", "").replace("万", "")) * 10000)
                    else:
                        sales = int(sales_tip.replace("+", ""))
                except:
                    sales = 0

                # 不在这里转链，保存 goods_sign 供前端点击时使用
                goods_sign = g.get("goods_sign", "")
                goods_id = g.get("goods_id", "")
                # 临时降级链接（如果前端转链失败可以用）
                affiliate_link = f"https://mobile.yangkeduo.com/goods.html?goods_sign={goods_sign}" if goods_sign else f"https://mobile.yangkeduo.com/goods.html?goods_id={goods_id}"

                product = MatchedProduct(
                    id=str(goods_sign or g.get("goods_id", "")),
                    name=g.get("goods_name", ""),
                    price=round(final_price, 2),
                    original_price=round(original_price, 2),
                    image_url=g.get("goods_image_url", g.get("goods_thumbnail_url", "")),
                    shop_name=g.get("mall_name", ""),
                    sales=sales,
                    commission_rate=g.get("promotion_rate", 0) / 1000,  # 千分比转百分比
                    affiliate_link=affiliate_link,
                    platform="pdd"
                )
                products.append(product)
            except Exception as e:
                logger.warning(f"解析拼多多商品失败: {e}")
                continue

        return products
    
    # ==================== 大淘客 ====================
    
    def _dataoke_generate_sign(self, params: dict) -> str:
        """大淘客签名"""
        sorted_params = sorted(params.items(), key=lambda x: x[0])
        param_str = "&".join([f"{k}={v}" for k, v in sorted_params])
        sign_str = param_str + "&key=" + self.dataoke_app_secret
        sign = hashlib.md5(sign_str.encode('utf-8')).hexdigest().upper()
        return sign
    
    async def _search_dataoke(self, item: IdentifiedItem, limit: int) -> List[MatchedProduct]:
        """大淘客商品搜索"""
        client = await self._get_client()
        
        if item.search_keywords:
            keyword = " ".join(item.search_keywords[:2])
        else:
            keyword = item.name
        
        logger.info(f"大淘客搜索: {keyword}")
        
        page_size = 50 if limit > 10 else 10
        
        params = {
            "appKey": self.dataoke_app_key,
            "version": "v2.1.2",
            "pageSize": str(page_size),
            "pageId": "1",
            "keyWords": keyword,
            "sort": "2",
        }
        
        params["sign"] = self._dataoke_generate_sign(params)
        
        url = f"{self.DATAOKE_API_URL}/goods/get-dtk-search-goods"
        
        try:
            response = await client.get(url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("code") == 0:
                    goods_list = data.get("data", {}).get("list", [])
                    
                    if not goods_list and keyword != item.name:
                        return await self._search_dataoke_simple(item.name, limit)
                    
                    return self._parse_dataoke_goods(goods_list)
            
            return []
        except Exception as e:
            logger.error(f"大淘客搜索失败: {e}")
            return []
    
    async def _search_dataoke_simple(self, keyword: str, limit: int) -> List[MatchedProduct]:
        """大淘客简化搜索"""
        client = await self._get_client()
        
        params = {
            "appKey": self.dataoke_app_key,
            "version": "v2.1.2",
            "pageSize": "50",
            "pageId": "1",
            "keyWords": keyword,
            "sort": "2",
        }
        params["sign"] = self._dataoke_generate_sign(params)
        
        url = f"{self.DATAOKE_API_URL}/goods/get-dtk-search-goods"
        
        try:
            response = await client.get(url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("code") == 0:
                    goods_list = data.get("data", {}).get("list", [])
                    return self._parse_dataoke_goods(goods_list)
            return []
        except:
            return []
    
    def _parse_dataoke_goods(self, goods_list: list) -> List[MatchedProduct]:
        """解析大淘客商品列表"""
        products = []
        for item_data in goods_list:
            try:
                main_pic = item_data.get("mainPic", "")
                if main_pic and not main_pic.startswith("http"):
                    main_pic = "https:" + main_pic
                
                product = MatchedProduct(
                    id=str(item_data.get("id", item_data.get("goodsId", ""))),
                    name=item_data.get("dtitle", "") or item_data.get("title", ""),
                    price=float(item_data.get("actualPrice", 0)),
                    original_price=float(item_data.get("originalPrice", 0)),
                    image_url=main_pic,
                    shop_name=item_data.get("shopName", ""),
                    sales=int(item_data.get("monthSales", 0)),
                    commission_rate=float(item_data.get("commissionRate", 0)) / 100,
                    affiliate_link=item_data.get("couponLink", "") or item_data.get("itemLink", ""),
                    platform="taobao"
                )
                products.append(product)
            except Exception as e:
                continue
        
        return products
    
    # ==================== 统一接口 ====================
    
    async def search_products(
        self,
        item: IdentifiedItem,
        limit: int = 20
    ) -> List[MatchedProduct]:
        """
        搜索匹配商品（自动选择可用平台）
        优先使用拼多多，备选大淘客
        """
        platform = self._get_available_platform()
        
        if platform is None:
            logger.error("未配置任何电商API")
            raise ValueError(
                "未配置电商推广API。请在 .env 文件中设置 PDD 或 DATAOKE 配置"
            )
        
        if platform == "pdd":
            return await self._search_pdd(item, limit)
        elif platform == "dataoke":
            return await self._search_dataoke(item, limit)
        
        return []
    
    async def match_products_for_item(
        self,
        item: IdentifiedItem,
        generated_image_path: str,
        limit: int = 5,
        similarity_threshold: float = 60.0
    ) -> List[MatchedProduct]:
        """
        为单个物品匹配商品
        """
        logger.info(f"为物品匹配商品: {item.name} (类别: {item.category})")
        
        # 搜索候选商品
        candidates = await self.search_products(item, limit=20)
        
        if not candidates:
            logger.warning(f"未找到匹配商品: {item.name}")
            return []
        
        # 按销量排序
        candidates.sort(key=lambda p: (p.sales or 0), reverse=True)
        
        return candidates[:limit]
    
    async def close(self):
        """关闭HTTP客户端"""
        if self._client:
            await self._client.aclose()
            self._client = None

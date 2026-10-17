"""
空间分析服务 - 简化版
直接调用 Gemini 一次返回完整分析
"""
import httpx
import json
import base64
import os
from typing import Optional, Dict, Any
from loguru import logger

from config.settings import settings
from models.schemas import StyleType, BudgetLevel, RoomType
from services.prompts_i18n import get_prompts


class SpaceAnalyzerService:
    """空间分析服务 - 一次 Gemini 调用完成分析"""
    
    def __init__(self):
        self.api_key = settings.VLLM_API_KEY
        self.api_url = settings.VLLM_API_URL
        self.model = settings.VLLM_MODEL
        self._client: Optional[httpx.AsyncClient] = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            timeout = httpx.Timeout(60.0, connect=30.0, read=60.0)
            self._client = httpx.AsyncClient(timeout=timeout, trust_env=False)
        return self._client
    
    def _get_media_type(self, image_path: str) -> str:
        ext = os.path.splitext(image_path)[1].lower()
        return {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.webp': 'image/webp',
        }.get(ext, 'image/jpeg')
    
    def _build_prompt(self, room_type: RoomType, style: StyleType, budget: BudgetLevel, lang: str) -> str:
        """构造面向 Gemini 的流式分析提示，末尾带生图提示词标记块"""
        prompts = get_prompts("space_analyzer", lang)
        room_names = prompts.get("room_names", {})
        style_names = prompts.get("style_names", {})
        budget_amounts = prompts.get("budget_amounts", {})
        currency = prompts.get("currency", "$")
        template = prompts.get("prompt_template", "")

        room_name = room_names.get(room_type.value, room_type.value)
        style_name = style_names.get(style.value, style.value)
        budget_value = budget_amounts.get(budget.value, budget.value)

        return template.format(
            room_type=room_name,
            style=style_name,
            budget=budget_value,
            currency=currency
        )

    def _split_analysis_and_prompt(self, content: str) -> Dict[str, Optional[str]]:
        """从模型返回中拆出分析正文和生图提示词"""
        prompt = None
        analysis_text = content or ""
        
        start = content.find("[[IMAGE_PROMPT]]")
        end = content.find("[[/IMAGE_PROMPT]]")
        if start != -1 and end != -1 and end > start:
            prompt = content[start + len("[[IMAGE_PROMPT]]"):end].strip()
            # 去掉标记块后展示给用户的正文
            analysis_text = (content[:start] + content[end + len("[[/IMAGE_PROMPT]]"):]).strip()
        
        return {
            "analysis_text": analysis_text.strip(),
            "image_prompt": prompt
        }
    
    async def analyze(
        self,
        image_path: str,
        room_type: RoomType,
        style: StyleType,
        budget: BudgetLevel,
        lang: str = "zh"
    ) -> Optional[Dict[str, Any]]:
        """分析空间照片，返回文本分析及生图提示词"""
        
        if not self.api_key:
            logger.error("Gemini API 未配置")
            return None
        
        # 处理路径
        if image_path.startswith("/uploads/"):
            actual_path = os.path.join(settings.UPLOAD_DIR, os.path.basename(image_path))
        else:
            actual_path = image_path
            
        if not os.path.exists(actual_path):
            logger.error(f"图片不存在: {actual_path}")
            return None
        
        # 读取图片
        with open(actual_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode()
        
        media_type = self._get_media_type(actual_path)
        prompt = self._build_prompt(room_type, style, budget, lang)
        
        # 调用 Gemini
        client = await self._get_client()
        
        try:
            logger.info("调用 Gemini 分析空间...")
            
            response = await client.post(
                f"{self.api_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": [{
                        "role": "user",
                        "content": [
                            {"type": "image_url", "image_url": {"url": f"data:{media_type};base64,{image_data}"}},
                            {"type": "text", "text": prompt}
                        ]
                    }],
                    "max_tokens": 2048,
                    "temperature": 0.7,
                    # Gemini 3 Flash: 使用 minimal thinking 减少延迟
                    "thinkingConfig": {
                        "thinkingLevel": "minimal"
                    }
                }
            )
            
            logger.info(f"API 响应状态码: {response.status_code}")
            
            if response.status_code == 200:
                response_data = response.json()
                logger.info(f"API 完整响应: {str(response_data)[:500]}")
                
                content = response_data.get("choices", [{}])[0].get("message", {}).get("content", "")
                
                logger.info(f"Gemini 返回内容长度: {len(content)}")
                logger.debug(f"Gemini 原始返回: {content[:500] if content else '空'}")
                
                if not content:
                    logger.error("Gemini 返回空内容")
                    return None
                
                # 拆分正文与生图提示词
                result = self._split_analysis_and_prompt(content)
                logger.info("空间分析完成")
                logger.debug(f"提取的生图提示词: {result.get('image_prompt', '')[:120]}")
                return result
            else:
                logger.error(f"Gemini API 错误: {response.status_code} - {response.text[:200]}")
                return None
                
        except Exception as e:
            logger.error(f"空间分析失败: {e}")
            return None
    
    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None


# 全局实例
space_analyzer = SpaceAnalyzerService()

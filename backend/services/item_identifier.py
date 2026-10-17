"""
物品识别服务
使用 Gemini (gemini-3-pro-preview) 对比原图和效果图，识别新增的可购买物品
"""
import httpx
import json
import base64
import os
import re
from typing import Optional, List, AsyncGenerator
from loguru import logger

from config.settings import settings
from models.schemas import IdentifiedItem
from services.prompts_i18n import get_prompts
from services.image_compressor import image_compressor


class ItemIdentifierService:
    """物品识别服务"""
    
    # System Prompt - 角色设定
    SYSTEM_PROMPT = """你是一个专业的家居软装顾问和视觉分析专家。

你的任务是对比两张图片：
- 图片1：用户家的原始照片
- 图片2：软装改造后的效果图

你需要找出图片2中**新增**的软装物品，也就是图片1中没有、图片2中新出现的物品。

重要提醒：
1. 只识别**新增**的物品，原图中已有的物品不要识别
2. 只识别可以单独购买的软装物品（不要识别墙面、地板、门窗等固定装修）
3. 为每个新增物品提供详细的描述，便于在电商平台搜索

你的输出必须是严格的JSON格式，不要有任何其他文字。"""

    # User Prompt 模板
    USER_PROMPT = """请对比这两张图片：
- 第一张是用户家的原始照片
- 第二张是软装改造后的效果图

请找出第二张图中**新增**的软装物品（即第一张图中没有的物品），并为每个物品提供：
1. name: 物品名称（简洁准确，如"北欧风落地灯"）
2. category: 所属类别（纺织品/灯具/绿植/墙面装饰/桌面摆件/收纳用品/其他）
3. description: 详细描述（外观特征、风格、适用场景）
4. color: 颜色（主色调）
5. material: 材质（如能判断）
6. style: 风格（北欧/日式/复古/现代/自然等）
7. size_estimate: 估计尺寸
8. price_estimate: 估计价格区间（人民币）
9. search_keywords: 搜索关键词数组（3-5个，用于电商搜索）

请严格按照以下JSON格式返回，不要有任何其他文字：

{
    "items": [
        {
            "id": "item_1",
            "name": "编织地毯",
            "category": "纺织品",
            "description": "米色编织纹理地毯，北欧简约风格，适合客厅使用",
            "color": "米色",
            "material": "棉麻混纺",
            "style": "北欧",
            "size_estimate": "160cm x 230cm",
            "price_estimate": "200-500元",
            "search_keywords": ["北欧地毯", "编织地毯", "客厅地毯", "米色地毯"]
        }
    ]
}

如果没有发现新增物品，返回空数组：{"items": []}"""
    
    def __init__(self):
        self.api_key = settings.VLLM_API_KEY
        self.api_url = settings.VLLM_API_URL
        self.model = settings.VLLM_MODEL
        self.provider = (getattr(settings, "VLLM_PROVIDER", None) or "ark").lower()
        self._client: Optional[httpx.AsyncClient] = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """获取HTTP客户端"""
        if self._client is None:
            # 物品识别需要上传两张图片，数据量大，需要较长超时时间
            # trust_env=False 禁用系统代理，避免代理不可用导致超时
            self._client = httpx.AsyncClient(timeout=300.0, trust_env=False)  # 5分钟
        return self._client
    
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
    
    def _resolve_path(self, image_path: str) -> str:
        """解析图片路径"""
        if image_path.startswith("/uploads/"):
            return os.path.join(settings.UPLOAD_DIR, os.path.basename(image_path))
        return image_path
    
    def _read_image_base64(self, image_path: str) -> tuple[str, str]:
        """读取图片并返回base64和媒体类型（自动压缩优化）"""
        actual_path = self._resolve_path(image_path)

        if not os.path.exists(actual_path):
            raise FileNotFoundError(f"图片文件不存在: {actual_path}")

        # 使用压缩服务（自动优化为1024px, JPEG质量85）
        # 这能显著减少API调用时间（首Token从1.35秒降至0.73秒）
        image_data = image_compressor.compress_to_base64(actual_path)

        # 压缩后统一使用JPEG格式
        media_type = "image/jpeg"
        return image_data, media_type
    
    def _extract_json(self, text: str) -> dict:
        """从文本中提取JSON，支持markdown代码块和不完整JSON的处理"""
        
        # 1. 先清理markdown代码块标记
        cleaned_text = text.strip()
        
        # 移除开头的 ```json 或 ```
        if cleaned_text.startswith("```json"):
            cleaned_text = cleaned_text[7:]
        elif cleaned_text.startswith("```"):
            cleaned_text = cleaned_text[3:]
        
        # 移除结尾的 ```
        if cleaned_text.endswith("```"):
            cleaned_text = cleaned_text[:-3]
        
        cleaned_text = cleaned_text.strip()
        
        # 2. 尝试直接解析
        try:
            return json.loads(cleaned_text)
        except json.JSONDecodeError:
            pass
        
        # 3. 尝试提取 ```json ... ``` 代码块（贪婪匹配）
        json_match = re.search(r'```(?:json)?\s*([\s\S]+?)```', text)
        if json_match:
            try:
                return json.loads(json_match.group(1).strip())
            except json.JSONDecodeError:
                pass
        
        # 4. 尝试提取最外层的 { ... } 部分
        brace_match = re.search(r'\{[\s\S]*\}', cleaned_text)
        if brace_match:
            json_str = brace_match.group(0)
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                # 5. 如果JSON不完整，尝试修复
                repaired = self._try_repair_json(json_str)
                if repaired:
                    return repaired
        
        logger.error(f"无法从响应中提取JSON: {text[:500]}")
        return {"items": []}
    
    def _try_repair_json(self, json_str: str) -> Optional[dict]:
        """尝试修复不完整的JSON"""
        try:
            # 尝试找到最后一个完整的item
            # 查找 items 数组
            items_match = re.search(r'"items"\s*:\s*\[([\s\S]*)', json_str)
            if not items_match:
                return None
            
            items_content = items_match.group(1)
            
            # 找到所有完整的item对象（以 } 结尾，后面跟 , 或空白）
            complete_items = []
            depth = 0
            current_item = ""
            in_string = False
            escape_next = False
            
            for char in items_content:
                if escape_next:
                    current_item += char
                    escape_next = False
                    continue
                
                if char == '\\':
                    current_item += char
                    escape_next = True
                    continue
                
                if char == '"' and not escape_next:
                    in_string = not in_string
                
                if not in_string:
                    if char == '{':
                        depth += 1
                    elif char == '}':
                        depth -= 1
                        if depth == 0:
                            current_item += char
                            # 找到一个完整的item
                            try:
                                item = json.loads(current_item.strip())
                                complete_items.append(item)
                            except:
                                pass
                            current_item = ""
                            continue
                
                if depth > 0:
                    current_item += char
            
            if complete_items:
                logger.info(f"JSON修复成功，提取了 {len(complete_items)} 个完整的item")
                return {"items": complete_items}
            
            return None
        except Exception as e:
            logger.warning(f"JSON修复失败: {e}")
            return None
    
    async def identify_stream(
        self,
        generated_image_path: str,
        original_image_path: Optional[str] = None,
        lang: str = "zh"
    ) -> AsyncGenerator[IdentifiedItem, None]:
        """
        流式识别图片中新增的可购买物品

        边识别边返回，每识别到一个物品就 yield 出来，
        这样调用方可以立即开始商品匹配，不用等所有物品都识别完。

        Args:
            generated_image_path: 生成的效果图路径
            original_image_path: 原始照片路径（用于对比）
            lang: 语言

        Yields:
            识别出的物品，一个一个地返回
        """
        # 检查API配置
        if not self.api_key:
            logger.error("VLLM服务未配置API密钥")
            raise ValueError("VLLM服务未配置。请在 .env 文件中设置 VLLM_API_KEY")

        logger.info(f"开始流式识别新增物品")
        logger.info(f"  原图: {original_image_path}")
        logger.info(f"  效果图: {generated_image_path}")

        # 读取生成图
        generated_base64, generated_media_type = self._read_image_base64(generated_image_path)

        client = await self._get_client()

        # 构建消息内容
        prompts = get_prompts("item_identifier", lang)
        system_prompt = prompts.get("system_prompt", self.SYSTEM_PROMPT)
        user_prompt = prompts.get("user_prompt", self.USER_PROMPT)
        image_labels = prompts.get("image_labels", {"original": "【图片1：原始照片】", "generated": "【图片2：改造后效果图】"})

        content_parts = []

        # 如果有原图，先添加原图
        if original_image_path:
            original_base64, original_media_type = self._read_image_base64(original_image_path)
            content_parts.append({
                "type": "input_text",
                "text": image_labels.get("original", "【图片1：原始照片】")
            })
            content_parts.append({
                "type": "input_image",
                "image_url": f"data:{original_media_type};base64,{original_base64}"
            })
            content_parts.append({
                "type": "input_text",
                "text": image_labels.get("generated", "【图片2：改造后效果图】")
            })

        # 添加生成图
        content_parts.append({
            "type": "input_image",
            "image_url": f"data:{generated_media_type};base64,{generated_base64}"
        })

        # 添加提示词
        content_parts.append({
            "type": "input_text",
            "text": user_prompt
        })

        # 是否 StepFun（step-5-preview 等，OpenAI 兼容）
        is_stepfun = self.provider == "stepfun" or self.model.startswith("step-")

        # 构建请求 - 根据模型选择格式
        if "doubao-seed-1-8" in self.model:
            # 豆包1.8格式
            request_body = {
                "model": self.model,
                "input": [
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": content_parts
                    }
                ],
                "thinking": {
                    "type": "disabled"
                },
                "stream": True
            }
        elif is_stepfun:
            # StepFun step-5-preview（OpenAI 兼容，content parts 需用标准 text/image_url 类型）
            openai_parts = []
            for part in content_parts:
                if part["type"] == "input_text":
                    openai_parts.append({"type": "text", "text": part["text"]})
                else:
                    openai_parts.append({"type": "image_url", "image_url": {"url": part["image_url"]}})
            request_body = {
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": openai_parts
                    }
                ],
                "max_tokens": 8192,
                "stream": True,
                "temperature": 0.3,
                "reasoning_effort": "low"
            }
        else:
            # 标准OpenAI格式
            request_body = {
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": content_parts
                    }
                ],
                "max_tokens": 8192,
                "stream": True,
                "thinkingConfig": {
                    "thinkingLevel": "minimal"
                }
            }

        # 豆包1.8使用responses端点
        api_endpoint = f"{self.api_url}/responses" if "doubao-seed-1-8" in self.model else f"{self.api_url}/chat/completions"
        logger.info(f"调用物品识别API: {api_endpoint}, model={self.model}")

        # 调试：打印请求体（不包含图片base64）
        debug_body = {k: v if k != 'input' else '[图片数据已省略]' for k, v in request_body.items()}
        logger.debug(f"请求参数: {debug_body}")

        try:
            async with client.stream(
                "POST",
                api_endpoint,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json=request_body,
                timeout=300.0
            ) as response:
                if response.status_code != 200:
                    error_text = await response.aread()
                    logger.error(f"物品识别API调用失败: {response.status_code} - {error_text}")
                    raise Exception(f"API调用失败: {response.status_code}")

                # 累积的文本内容
                accumulated_text = ""
                thinking_text = ""
                item_index = 0
                yielded_items = set()  # 跟踪已经yield的item id
                first_content_time = None
                thinking_logged = False

                async for line in response.aiter_lines():
                    if not line.strip():
                        continue

                    # 豆包1.8使用event格式
                    if "doubao-seed-1-8" in self.model:
                        # 豆包1.8格式: event: xxx\ndata: {...}
                        if line.startswith("data: "):
                            data_str = line[6:]
                            try:
                                data = json.loads(data_str)
                                # 提取delta内容
                                if data.get("type") == "response.output_text.delta":
                                    content = data.get("delta", "")
                                    if content:
                                        if first_content_time is None:
                                            import time
                                            first_content_time = time.time()

                                        accumulated_text += content
                                        # 尝试从累积文本中提取完整的item
                                        for item in self._extract_items_from_stream(accumulated_text, yielded_items):
                                            item_index += 1
                                            item.id = f"item_{item_index}"
                                            logger.info(f"流式识别到物品: {item.name}")
                                            yielded_items.add(item.id)
                                            yield item
                                elif data.get("type") == "response.done":
                                    break
                            except json.JSONDecodeError:
                                continue
                    else:
                        # 标准OpenAI格式
                        if line.startswith("data: "):
                            data_str = line[6:]
                            if data_str.strip() == "[DONE]":
                                break
                            try:
                                data = json.loads(data_str)
                                choices = data.get("choices", [])
                                if not choices:
                                    continue
                                delta = choices[0].get("delta", {})

                                # 检查是否有 thinking 内容
                                thinking = delta.get("thinking", "")
                                if thinking:
                                    thinking_text += thinking

                                content = delta.get("content", "")
                                if content:
                                    # 记录第一个 content 的时间
                                    if first_content_time is None:
                                        import time
                                        first_content_time = time.time()
                                        if thinking_text:
                                            logger.info(f"Thinking 完成，内容长度: {len(thinking_text)} 字符")
                                            logger.debug(f"Thinking 摘要: {thinking_text[:500]}...")

                                    accumulated_text += content
                                    # 尝试从累积文本中提取完整的item
                                    for item in self._extract_items_from_stream(accumulated_text, yielded_items):
                                        item_index += 1
                                        item.id = f"item_{item_index}"
                                        logger.info(f"流式识别到物品: {item.name}")
                                        yielded_items.add(item.id)
                                        yield item
                            except json.JSONDecodeError:
                                continue

                # 流结束后，尝试从完整文本中提取剩余的items
                logger.info(f"流式接收完成，累积文本长度: {len(accumulated_text)}")

                # 最后再解析一次，确保没有遗漏
                final_data = self._extract_json(accumulated_text)
                items_data = final_data.get("items", [])

                for i, item_data in enumerate(items_data):
                    item_id = item_data.get("id", f"item_{i+1}")
                    if item_id not in yielded_items:
                        try:
                            item = IdentifiedItem(
                                id=item_id,
                                name=item_data.get("name", "未知物品"),
                                category=item_data.get("category", "其他"),
                                description=item_data.get("description", ""),
                                color=item_data.get("color"),
                                material=item_data.get("material"),
                                style=item_data.get("style"),
                                size_estimate=item_data.get("size_estimate"),
                                price_estimate=item_data.get("price_estimate"),
                                search_keywords=item_data.get("search_keywords", [])
                            )
                            logger.info(f"最终解析到物品: {item.name}")
                            yield item
                        except Exception as e:
                            logger.warning(f"解析物品数据失败: {e}")

        except httpx.TimeoutException:
            logger.error("物品识别API调用超时")
            raise Exception("物品识别超时，请重试")
        except Exception as e:
            logger.error(f"物品流式识别失败: {e}")
            raise

    def _extract_items_from_stream(self, text: str, yielded_items: set) -> List[IdentifiedItem]:
        """
        从流式累积的文本中尝试提取完整的item对象

        策略：找到所有完整的 {...} JSON 对象，尝试解析为 item
        """
        items = []

        # 查找 "items": [ 之后的内容
        items_start = text.find('"items"')
        if items_start == -1:
            return items

        # 找到数组开始的位置
        array_start = text.find('[', items_start)
        if array_start == -1:
            return items

        # 从数组开始位置提取完整的对象
        content = text[array_start + 1:]

        # 使用状态机找完整的 { ... } 对象
        depth = 0
        current_obj = ""
        in_string = False
        escape_next = False

        for char in content:
            if escape_next:
                current_obj += char
                escape_next = False
                continue

            if char == '\\':
                current_obj += char
                escape_next = True
                continue

            if char == '"' and not escape_next:
                in_string = not in_string

            if not in_string:
                if char == '{':
                    depth += 1
                elif char == '}':
                    depth -= 1
                    if depth == 0:
                        current_obj += char
                        # 尝试解析这个对象
                        try:
                            item_data = json.loads(current_obj.strip())
                            item_id = item_data.get("id", "")
                            # 检查是否已经yield过
                            if item_id and item_id not in yielded_items and item_data.get("name"):
                                item = IdentifiedItem(
                                    id=item_id,
                                    name=item_data.get("name", "未知物品"),
                                    category=item_data.get("category", "其他"),
                                    description=item_data.get("description", ""),
                                    color=item_data.get("color"),
                                    material=item_data.get("material"),
                                    style=item_data.get("style"),
                                    size_estimate=item_data.get("size_estimate"),
                                    price_estimate=item_data.get("price_estimate"),
                                    search_keywords=item_data.get("search_keywords", [])
                                )
                                items.append(item)
                        except (json.JSONDecodeError, Exception):
                            pass
                        current_obj = ""
                        continue

            if depth > 0:
                current_obj += char

        return items

    async def identify(
        self,
        generated_image_path: str,
        original_image_path: Optional[str] = None,
        lang: str = "zh"
    ) -> List[IdentifiedItem]:
        """
        识别图片中新增的可购买物品
        
        Args:
            generated_image_path: 生成的效果图路径
            original_image_path: 原始照片路径（用于对比）
            
        Returns:
            识别出的新增物品列表
        """
        # 检查API配置
        if not self.api_key:
            logger.error("VLLM服务未配置API密钥")
            raise ValueError(
                "VLLM服务未配置。请在 .env 文件中设置 VLLM_API_KEY"
            )
        
        logger.info(f"开始识别新增物品")
        logger.info(f"  原图: {original_image_path}")
        logger.info(f"  效果图: {generated_image_path}")
        
        # 读取生成图
        generated_base64, generated_media_type = self._read_image_base64(generated_image_path)
        
        client = await self._get_client()
        
        # 构建消息内容
        prompts = get_prompts("item_identifier", lang)
        system_prompt = prompts.get("system_prompt", self.SYSTEM_PROMPT)
        user_prompt = prompts.get("user_prompt", self.USER_PROMPT)
        image_labels = prompts.get("image_labels", {"original": "【图片1：原始照片】", "generated": "【图片2：改造后效果图】"})

        content_parts = []
        
        # 如果有原图，先添加原图
        if original_image_path:
            original_base64, original_media_type = self._read_image_base64(original_image_path)
            content_parts.append({
                "type": "text",
                "text": image_labels.get("original", "【图片1：原始照片】")
            })
            content_parts.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:{original_media_type};base64,{original_base64}"
                }
            })
            content_parts.append({
                "type": "text",
                "text": image_labels.get("generated", "【图片2：改造后效果图】")
            })
        
        # 添加生成图
        content_parts.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:{generated_media_type};base64,{generated_base64}"
            }
        })
        
        # 添加提示词
        content_parts.append({
            "type": "text",
            "text": user_prompt
        })
        
        # 构建请求
        request_body = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": content_parts
                }
            ],
            "max_tokens": 8192,
            "thinkingConfig": {
                "thinkingLevel": "minimal"
            }
        }
        
        logger.info(f"调用物品识别API: {self.api_url}/chat/completions, model={self.model}")
        
        try:
            response = await client.post(
                f"{self.api_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json=request_body
            )
            
            logger.info(f"API响应状态码: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                logger.debug(f"API响应: {result}")
                
                # 提取响应内容
                choices = result.get("choices", [])
                if not choices:
                    logger.error("API响应中没有choices")
                    return []
                
                message = choices[0].get("message", {})
                content = message.get("content", "")
                
                # 如果content是数组，提取文本
                if isinstance(content, list):
                    text_parts = []
                    for item in content:
                        if isinstance(item, dict) and item.get("type") == "text":
                            text_parts.append(item.get("text", ""))
                        elif isinstance(item, str):
                            text_parts.append(item)
                    content = "\n".join(text_parts)
                
                logger.info(f"模型返回内容: {content[:500]}...")
                
                # 解析JSON
                data = self._extract_json(content)
                items_data = data.get("items", [])
                
                # 转换为IdentifiedItem对象
                items = []
                for i, item_data in enumerate(items_data):
                    try:
                        item = IdentifiedItem(
                            id=item_data.get("id", f"item_{i+1}"),
                            name=item_data.get("name", "未知物品"),
                            category=item_data.get("category", "其他"),
                            description=item_data.get("description", ""),
                            color=item_data.get("color"),
                            material=item_data.get("material"),
                            style=item_data.get("style"),
                            size_estimate=item_data.get("size_estimate"),
                            price_estimate=item_data.get("price_estimate"),
                            search_keywords=item_data.get("search_keywords", [])
                        )
                        items.append(item)
                    except Exception as e:
                        logger.warning(f"解析物品数据失败: {e}, data={item_data}")
                        continue
                
                logger.info(f"成功识别 {len(items)} 个新增物品")
                return items
                
            else:
                error_text = response.text
                logger.error(f"物品识别API调用失败: {response.status_code} - {error_text}")
                raise Exception(f"API调用失败: {response.status_code} - {error_text}")
                
        except httpx.TimeoutException:
            logger.error("物品识别API调用超时")
            raise Exception("物品识别超时，请重试")
        except Exception as e:
            logger.error(f"物品识别失败: {e}")
            raise
    
    async def close(self):
        """关闭HTTP客户端"""
        if self._client:
            await self._client.aclose()
            self._client = None

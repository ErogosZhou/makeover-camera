"""
VLLM服务 - 动态生成针对性的生图提示词

职责:
- 分析用户上传的房间照片
- 根据具体情况生成定制化的Seedream生图prompt
- 基于宜家全品类软装数据库,生成丰富多样的设计方案

优势:
- 比固定prompt更精准,针对每张图片定制
- 生成的prompt会展示给用户(打字机效果),提升体验
- 涵盖宜家200+软装品类,设计方案更丰富
"""
import httpx
import base64
import json
from typing import Optional
from loguru import logger

from config.settings import settings
from services.image_compressor import ImageCompressor


class VLLMService:
    """VLLM提示词生成服务"""

    def __init__(self):
        self.api_url = settings.VLLM_API_URL
        self.api_key = settings.VLLM_API_KEY
        self.model = settings.VLLM_MODEL
        self.provider = (settings.VLLM_PROVIDER or "ark").lower()
        self.compressor = ImageCompressor(max_size=512, quality=85)
        logger.info(f"VLLM服务初始化: provider={self.provider}, model={self.model}")

    # ============================================================
    # META_PROMPT V3 - 简洁版，无品类列表，无具体物品 few shot
    # 旧版存档: backend/prompts_archive/
    # ============================================================

    META_PROMPT_V3 = """你是一位资深室内软装设计师。请仔细观察这张房间照片,生成软装改造方案。

## 输出格式

严格分两部分输出（不要输出任何标题或说明文字，直接开始内容）:

第一部分: 设计方案（300-400字，用于生图）
- 开头固定写:【重要】保持墙面地板窗户布局不变,只添加软装。
- 根据房间实际情况(光线、色调、空间感)选择最匹配的风格
- 具体描述窗帘、地毯、床品/沙发、抱枕、绿植、灯具、墙面装饰、桌面摆件的颜色、材质、数量
- 结尾描述光线氛围和摄影质感

第二部分: 物品关键词（用于商品搜索）
- 另起一行写 ---ITEMS---
- 再另起一行输出 JSON 数组,8-10个关键词
- 每个关键词格式: 颜色+材质+样式+类型，例如"深绿天鹅绒单人阅读椅"、"木质三脚架落地灯"
- 格式: ["关键词1", "关键词2", ...]

## 禁止事项
- 禁止输出"亚麻纱帘"、"白色亚麻"等亚麻类窗帘，窗帘请选择其他材质（丝绒/遮光布/棉纱/罗马帘/百叶窗等）
- 禁止在输出中写"第一部分"、"第二部分"等标题

## 输出示例（仅展示格式，内容请根据照片自由发挥）

【重要】保持墙面地板窗户布局不变,只添加软装。
[风格名](现有[墙面]+[地板]):
窗边[窗帘非亚麻材质],窗台[物品]。
绿植[植物名+花器],共[N]种。
[床/沙发][床品颜色材质],[抱枕N个+颜色组合],[毯子]。
地面[地毯]。
[桌面摆件列举6-8项]。
墙面[挂画+镜子+装饰列举]。
角落[落地灯+座椅]。
[光线描述],8k真实摄影质感,材质细节清晰。

---ITEMS---
["物品1", "物品2", ...]

现在请根据照片生成:"""

    async def generate_prompt_with_items(
        self,
        image_path: str,
        style: Optional[str] = None
    ) -> tuple[Optional[str], Optional[list[str]]]:
        """
        生成设计方案和物品关键词数组（新版V2）

        Args:
            image_path: 房间照片路径
            style: 风格(预留,当前由VLLM智能判断)

        Returns:
            tuple(设计方案文本, 物品关键词数组)
        """
        if not self.api_key:
            logger.warning("VLLM未配置,使用fallback")
            return None, None

        try:
            # 压缩图片
            logger.info(f"压缩图片用于VLLM分析: {image_path}")
            compressed_base64 = self.compressor.compress_to_base64(image_path)

            # 调用VLLM（按 provider 选择 API 格式）
            generated_output = await self._call_vllm(compressed_base64, self.META_PROMPT_V3) or ""

            # 验证生成结果
            if not generated_output or len(generated_output) < 150:
                logger.warning(f"VLLM生成输出过短({len(generated_output)}字)")
                return None, None

            # 解析输出：分离设计方案和物品数组
            if "---ITEMS---" in generated_output:
                parts = generated_output.split("---ITEMS---")
                design_text = parts[0].strip()
                items_text = parts[1].strip()

                # 清洗设计方案文本
                cleaned_design = self._clean_prompt(design_text)

                # 解析物品数组
                import re
                json_match = re.search(r'\[.*?\]', items_text, re.DOTALL)
                if json_match:
                    try:
                        items_array = json.loads(json_match.group())
                        logger.info(f"VLLM生成成功: 设计方案{len(cleaned_design)}字, 物品数组{len(items_array)}个")
                        return cleaned_design, items_array
                    except json.JSONDecodeError as e:
                        logger.warning(f"物品数组JSON解析失败: {e}")
                        # 返回设计方案，物品数组为空
                        return cleaned_design, []
                else:
                    logger.warning("未找到物品数组JSON格式")
                    return cleaned_design, []
            else:
                logger.warning("输出中未找到 ---ITEMS--- 分隔符")
                cleaned_output = self._clean_prompt(generated_output)
                return cleaned_output, []

        except Exception as e:
            logger.error(f"VLLM生成prompt失败: {e}")
            return None, None

    async def generate_prompt(
        self,
        image_path: str,
        style: Optional[str] = None
    ) -> Optional[str]:
        """
        根据房间照片生成针对性的Seedream生图prompt

        Args:
            image_path: 房间照片路径
            style: 风格(预留,当前由VLLM智能判断)

        Returns:
            生成的prompt字符串(300-400字)
        """
        if not self.api_key:
            logger.warning("VLLM未配置,使用fallback prompt")
            return None

        try:
            # 压缩图片
            logger.info(f"压缩图片用于VLLM分析: {image_path}")
            compressed_base64 = self.compressor.compress_to_base64(image_path)

            # 调用VLLM（按 provider 选择 API 格式）
            generated_prompt = await self._call_vllm(compressed_base64, self.META_PROMPT_V3) or ""

            # 验证生成结果
            if not generated_prompt or len(generated_prompt) < 150:
                logger.warning(f"VLLM生成prompt过短({len(generated_prompt)}字),使用fallback")
                return None

            # 清洗提示词：去除markdown格式、多余换行、多余空格
            cleaned_prompt = self._clean_prompt(generated_prompt)

            logger.info(f"VLLM生成prompt成功: {len(cleaned_prompt)}字 (原始{len(generated_prompt)}字)")
            logger.debug(f"生成的prompt: {cleaned_prompt[:200]}...")

            return cleaned_prompt

        except Exception as e:
            logger.error(f"VLLM生成prompt失败: {e}")
            return None

    # ============================================================
    # VLLM 调用层 - 按 provider 分发（ark 豆包 / stepfun）
    # ============================================================

    async def _call_vllm(self, compressed_base64: str, prompt_text: str) -> Optional[str]:
        """调用 VLLM 返回原始文本（ark=豆包 Responses API，stepfun=OpenAI 兼容）"""
        if self.provider == "stepfun":
            return await self._call_stepfun(compressed_base64, prompt_text)
        return await self._call_ark(compressed_base64, prompt_text)

    async def _call_stepfun(self, compressed_base64: str, prompt_text: str) -> Optional[str]:
        """StepFun / Step Plan（step-5-preview，OpenAI 兼容 chat/completions，非流式）"""
        request_body = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{compressed_base64}"}
                        },
                        {
                            "type": "text",
                            "text": prompt_text
                        }
                    ]
                }
            ],
            "temperature": 0.9,
            "stream": False,
            "reasoning_effort": "low"  # 最低思考强度，保速度
        }

        api_endpoint = f"{self.api_url}/chat/completions"
        logger.info(f"调用 StepFun VLLM: {api_endpoint}, model={self.model}")

        try:
            async with httpx.AsyncClient(timeout=120.0, trust_env=False) as client:
                response = await client.post(
                    api_endpoint,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json=request_body
                )

                if response.status_code != 200:
                    logger.error(f"StepFun VLLM API调用失败: {response.status_code} - {response.text}")
                    return None

                result = response.json()
                choices = result.get("choices", [])
                if not choices:
                    logger.error(f"StepFun VLLM 响应中没有choices: {result}")
                    return None

                content = choices[0].get("message", {}).get("content", "")
                logger.info(f"StepFun VLLM 返回 {len(content)} 字")
                return content

        except Exception as e:
            logger.error(f"StepFun VLLM调用异常: {e}")
            return None

    async def _call_ark(self, compressed_base64: str, prompt_text: str) -> Optional[str]:
        """豆包（ark Responses API，流式）"""
        request_body = {
            "model": self.model,
            "input": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_image",
                            "image_url": f"data:image/jpeg;base64,{compressed_base64}"
                        },
                        {
                            "type": "input_text",
                            "text": prompt_text
                        }
                    ]
                }
            ],
            "thinking": {
                "type": "disabled"
            },
            "stream": True,
            "temperature": 0.9
        }

        api_endpoint = f"{self.api_url}/responses"
        logger.info(f"调用 ark VLLM: {api_endpoint}, model={self.model}")
        generated_output = ""

        async with httpx.AsyncClient(timeout=120.0, trust_env=False) as client:
            async with client.stream(
                "POST",
                api_endpoint,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json=request_body
            ) as response:
                if response.status_code != 200:
                    error_text = await response.aread()
                    logger.error(f"VLLM API调用失败: {response.status_code} - {error_text}")
                    return None

                # 流式读取
                async for line in response.aiter_lines():
                    if not line.strip():
                        continue

                    if line.startswith("data: "):
                        data_str = line[6:]
                        try:
                            data = json.loads(data_str)
                            if data.get("type") == "response.output_text.delta":
                                delta = data.get("delta", "")
                                generated_output += delta
                            elif data.get("type") == "response.done":
                                break
                        except json.JSONDecodeError:
                            continue

        return generated_output

    def _clean_prompt(self, prompt: str) -> str:
        """
        清洗VLLM生成的提示词

        去除：
        - markdown格式（```、**等）
        - 多余的换行（保留必要的段落分隔）
        - 多余的空格和缩进
        - 首尾空白
        """
        import re

        # 1. 去除markdown代码块标记
        prompt = re.sub(r'```[a-z]*\n?', '', prompt)
        prompt = re.sub(r'```', '', prompt)

        # 2. 去除markdown加粗/斜体
        prompt = re.sub(r'\*\*([^*]+)\*\*', r'\1', prompt)
        prompt = re.sub(r'\*([^*]+)\*', r'\1', prompt)

        # 3. 去除markdown标题标记
        prompt = re.sub(r'^#+\s+', '', prompt, flags=re.MULTILINE)

        # 4. 处理换行：连续多个换行合并为一个
        prompt = re.sub(r'\n{3,}', '\n\n', prompt)

        # 5. 去除每行开头的空格和制表符（保持文本紧凑）
        lines = [line.lstrip() for line in prompt.split('\n')]
        prompt = '\n'.join(lines)

        # 6. 将多个连续空格合并为一个
        prompt = re.sub(r' {2,}', ' ', prompt)

        # 7. 去除首尾空白
        prompt = prompt.strip()

        return prompt

    def get_fallback_prompt(self, style: Optional[str] = None) -> str:
        """
        获取fallback prompt (当VLLM失败时使用)

        基于宜家全品类的通用方案
        """
        return """【重要】保持墙面地板窗户布局不变,只添加软装。

北欧风(现有墙面地板):
窗边棉麻纱帘,木质换鞋凳,窗台尤加利干花。
绿植琴叶榕+龟背竹+虎皮兰,搭配陶瓷花瓶+玻璃瓶+水泥花器。
床配纯色亚麻四件套,抱枕6个(米白、浅灰、驼色、奶油、藕粉、雾蓝),床尾针织流苏毯。
地面手工编织地毯,米色调。
床头柜木质台灯+精装书3本+咖啡杯+香薰蜡烛+眼镜+水瓶+木质收纳盒+多肉植物。
墙面黑白摄影三联画+圆形藤编挂盘+一字置物架+木质挂钩+圆形镜+墙面时钟。
角落三脚架落地灯+单人阅读椅+移动推车。
自然光柔和均衡,色温3500-4000K,真实日常氛围。8k摄影质感,材质纹理清晰。"""


# 全局单例
vllm_service = VLLMService()

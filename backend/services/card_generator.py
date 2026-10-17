"""
商品购买卡片生成服务

合成一张包含商品图、标题、价格、二维码的图片，
适合直接在微信等不支持 Markdown 链接的场景中发送。
"""
import os
import uuid
import httpx
import qrcode
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from loguru import logger


# 卡片尺寸（高度自适应内容）
CARD_W = 600
PRODUCT_IMG_SIZE = 400   # 商品图区域高度
QR_SIZE = 140            # 二维码尺寸
PADDING = 24

# 字体路径（服务器上找系统字体）
FONT_PATHS = [
    "/usr/share/fonts/wqy-microhei/wqy-microhei.ttc",
    "/usr/share/fonts/wqy-zenhei/wqy-zenhei.ttc",
    "/usr/share/fonts/chinese/simsun.ttc",
    "/System/Library/Fonts/PingFang.ttc",       # macOS
    "/System/Library/Fonts/STHeiti Light.ttc",  # macOS fallback
]


def _get_font(size: int):
    for path in FONT_PATHS:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


def _wrap_text(text: str, font, max_width: int, draw: ImageDraw) -> list[str]:
    """按像素宽度折行"""
    lines = []
    current = ""
    for char in text:
        test = current + char
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] > max_width and current:
            lines.append(current)
            current = char
        else:
            current = test
    if current:
        lines.append(current)
    return lines


async def generate_product_card(
    product_name: str,
    price: float,
    original_price: float | None,
    image_url: str,
    purchase_url: str,
    platform: str,
    upload_dir: str,
) -> str:
    """
    生成商品卡片图片，返回本地文件路径。

    卡片布局（从上到下）：
    ┌────────────────────────┐
    │      商品主图           │  400px
    ├────────────────────────┤
    │  商品名称（最多2行）     │
    │  ¥价格  原价（划线）     │
    │  平台标签               │
    ├──────────────┬─────────┤
    │              │  二维码  │  扫码购买
    └──────────────┴─────────┘
    """
    async with httpx.AsyncClient(timeout=20.0, trust_env=False) as client:
        # 下载商品图
        try:
            resp = await client.get(image_url)
            product_img = Image.open(BytesIO(resp.content)).convert("RGB")
        except Exception as e:
            logger.warning(f"商品图下载失败: {e}，使用占位图")
            product_img = Image.new("RGB", (PRODUCT_IMG_SIZE, PRODUCT_IMG_SIZE), "#f0f0f0")

    # ── 预计算文字高度，确定画布总高 ──────────────────────────
    font_name = _get_font(22)
    font_price = _get_font(28)
    font_original = _get_font(18)
    font_tag = _get_font(16)
    font_hint = _get_font(14)

    # 用临时画布量文字
    _tmp = ImageDraw.Draw(Image.new("RGB", (CARD_W, 1)))
    name_lines = _wrap_text(product_name, font_name, CARD_W - PADDING * 2 - QR_SIZE - PADDING, _tmp)[:2]
    text_block_h = (
        12                          # 商品图下间距
        + len(name_lines) * 30 + 6  # 名称行
        + 40                         # 价格行
        + 34                         # 标签行
        + PADDING                    # 底部留白
    )
    qr_block_h = PADDING + QR_SIZE + 20 + PADDING  # 二维码区域
    info_h = max(text_block_h, qr_block_h)
    CARD_H = PRODUCT_IMG_SIZE + info_h

    # 创建画布
    card = Image.new("RGB", (CARD_W, CARD_H), "#ffffff")
    draw = ImageDraw.Draw(card)

    # ── 商品图 ──────────────────────────────────────────────
    img_w, img_h = product_img.size
    scale = max(CARD_W / img_w, PRODUCT_IMG_SIZE / img_h)
    new_w = int(img_w * scale)
    new_h = int(img_h * scale)
    product_img = product_img.resize((new_w, new_h), Image.LANCZOS)
    left = (new_w - CARD_W) // 2
    top = (new_h - PRODUCT_IMG_SIZE) // 2
    product_img = product_img.crop((left, top, left + CARD_W, top + PRODUCT_IMG_SIZE))
    card.paste(product_img, (0, 0))

    # ── 文字区域 ────────────────────────────────────────────
    text_y = PRODUCT_IMG_SIZE + 12

    # 商品名称（最多2行，右侧留出二维码位置）
    name_max_w = CARD_W - PADDING * 2 - QR_SIZE - PADDING
    for line in name_lines:
        draw.text((PADDING, text_y), line, font=font_name, fill="#1a1a1a")
        text_y += 30
    text_y += 6

    # 价格
    price_text = f"¥{price:.0f}"
    draw.text((PADDING, text_y), price_text, font=font_price, fill="#e4393c")

    if original_price and original_price > price:
        orig_text = f"¥{original_price:.0f}"
        px = PADDING + draw.textbbox((0, 0), price_text, font=font_price)[2] + 10
        py = text_y + 8
        draw.text((px, py), orig_text, font=font_original, fill="#999999")
        bbox = draw.textbbox((px, py), orig_text, font=font_original)
        mid_y = (bbox[1] + bbox[3]) // 2
        draw.line([(bbox[0], mid_y), (bbox[2], mid_y)], fill="#999999", width=1)

    text_y += 40

    # 平台标签
    platform_label = {"pdd": "拼多多", "taobao": "淘宝", "jd": "京东"}.get(platform, platform)
    tag_text = f" {platform_label} "
    tag_color = {"pdd": "#e02020", "taobao": "#ff6600", "jd": "#cc0000"}.get(platform, "#666666")
    bbox = draw.textbbox((0, 0), tag_text, font=font_tag)
    tag_w = bbox[2] - bbox[0] + 8
    tag_h = bbox[3] - bbox[1] + 6
    draw.rounded_rectangle(
        [PADDING, text_y, PADDING + tag_w, text_y + tag_h],
        radius=4, fill=tag_color
    )
    draw.text((PADDING + 4, text_y + 3), tag_text.strip(), font=font_tag, fill="#ffffff")

    # ── 二维码（右侧垂直居中于信息区） ────────────────────────
    qr = qrcode.QRCode(box_size=4, border=2)
    qr.add_data(purchase_url)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    qr_img = qr_img.resize((QR_SIZE, QR_SIZE), Image.LANCZOS)

    qr_x = CARD_W - QR_SIZE - PADDING
    qr_y = PRODUCT_IMG_SIZE + PADDING
    card.paste(qr_img, (qr_x, qr_y))

    hint = "扫码购买"
    hint_bbox = draw.textbbox((0, 0), hint, font=font_hint)
    hint_w = hint_bbox[2] - hint_bbox[0]
    hint_x = qr_x + (QR_SIZE - hint_w) // 2
    draw.text((hint_x, qr_y + QR_SIZE + 4), hint, font=font_hint, fill="#666666")

    # ── 底部分隔线 ──────────────────────────────────────────
    draw.line([(0, CARD_H - 1), (CARD_W, CARD_H - 1)], fill="#eeeeee", width=1)

    # ── 保存 ────────────────────────────────────────────────
    filename = f"card_{uuid.uuid4().hex[:12]}.jpg"
    filepath = os.path.join(upload_dir, filename)
    card.save(filepath, "JPEG", quality=88, optimize=True)
    logger.info(f"商品卡片已生成: {filepath}")
    return filepath

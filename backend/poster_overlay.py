"""
给 Seedream 生成的海报候选图叠加文字（标题/副标题/slogan/参赛角标）
输入: posters/0X_*.jpg（gen_posters.py 的产物）
输出: posters/final_0X_*.jpg（保留原图）

用法: ./venv/bin/python poster_overlay.py
"""
import os

from PIL import Image, ImageDraw, ImageFont

POSTER_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "posters")

FONT_CANDIDATES = [
    "/System/Library/Fonts/Supplemental/Songti.ttc",   # 宋体（衬线，海报感）
    "/System/Library/Fonts/PingFang.ttc",              # 苹方（兜底）
    "/System/Library/Fonts/STHeiti Light.ttc",
]

INK = (31, 31, 31)          # 主文字
SUB = (90, 90, 90)          # 次要文字
SAGE = (74, 93, 78)         # 品牌绿（取自 App 主题色）
WHITE = (255, 255, 255)


def load_font(size: int, serif: bool = True) -> ImageFont.FreeTypeFont:
    paths = FONT_CANDIDATES if serif else [FONT_CANDIDATES[1], FONT_CANDIDATES[2], FONT_CANDIDATES[0]]
    for p in paths:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
    return ImageFont.load_default()


def draw_tracked_text(draw, xy, text, font, fill, tracking=0, anchor_center_x=None):
    """逐字绘制以实现字距；anchor_center_x 给定时整行居中"""
    widths = [draw.textlength(ch, font=font) for ch in text]
    total = sum(widths) + tracking * (len(text) - 1)
    x = anchor_center_x - total / 2 if anchor_center_x is not None else xy[0]
    for ch, w in zip(text, widths):
        draw.text((x, xy[1]), ch, font=font, fill=fill)
        x += w + tracking


def draw_badge(draw, cx, y, text, font):
    """居中圆角角标"""
    pad_x, pad_y = 28, 14
    tw = draw.textlength(text, font=font)
    th = font.size
    x0, y0 = cx - tw / 2 - pad_x, y
    x1, y1 = cx + tw / 2 + pad_x, y + th + pad_y * 2
    draw.rounded_rectangle([x0, y0, x1, y1], radius=(y1 - y0) / 2, fill=SAGE)
    draw.text((cx - tw / 2, y + pad_y), text, font=font, fill=WHITE)


# 每张图的排版配置（基于实际观察到的留白区）
LAYOUTS = {
    "01_hero_camera": dict(title_y=150, sub_y=340, slogan_y=2200, badge_y=2320),
    "02_before_after": dict(title_y=120, sub_y=310, slogan_y=2230, badge_y=2350),
    "03_magic_moment": dict(title_y=160, sub_y=350, slogan_y=2210, badge_y=2330),
    "04_minimal_collage": dict(title_y=740, sub_y=950, slogan_y=2160, badge_y=2280),
}

TITLE = "换装相机"
SUBTITLE = "MAKEOVER CAMERA"
SLOGAN = "一张照片，看见家的另一种可能"
BADGE = "阶跃星辰 Hackathon 参赛作品 · Powered by Step 5 Preview"


def overlay(src: str, dst: str, cfg: dict):
    img = Image.open(src).convert("RGB")
    w, _ = img.size
    cx = w // 2
    draw = ImageDraw.Draw(img)

    f_title = load_font(168)
    f_sub = load_font(46, serif=False)
    f_slogan = load_font(52)
    f_badge = load_font(34, serif=False)

    # 柔和投影，保证任何背景上的可读性
    shadow = (0, 0, 0, 60)
    for dx, dy in ((2, 3), (0, 2), (2, 2)):
        draw.text((cx + dx, cfg["title_y"] + dy), TITLE, font=f_title, fill=shadow[:3], anchor="mm")
    draw.text((cx, cfg["title_y"]), TITLE, font=f_title, fill=INK, anchor="mm")

    draw_tracked_text(draw, (0, cfg["sub_y"]), SUBTITLE, f_sub, SUB, tracking=10, anchor_center_x=cx)

    sw = draw.textlength(SLOGAN, font=f_slogan)
    draw.text((cx + 1, cfg["slogan_y"] + 2), SLOGAN, font=f_slogan, fill=(0, 0, 0), anchor="mm")
    draw.text((cx, cfg["slogan_y"]), SLOGAN, font=f_slogan, fill=SUB, anchor="mm")

    draw_badge(draw, cx, cfg["badge_y"], BADGE, f_badge)

    img.save(dst, "JPEG", quality=92)
    print(f"[OK] {dst}")


def main():
    used = next((p for p in FONT_CANDIDATES if os.path.exists(p)), "load_default")
    print(f"字体: {used}")
    for name, cfg in LAYOUTS.items():
        src = os.path.join(POSTER_DIR, f"{name}.jpg")
        dst = os.path.join(POSTER_DIR, f"final_{name}.jpg")
        if not os.path.exists(src):
            print(f"[SKIP] 缺少 {src}")
            continue
        overlay(src, dst, cfg)


if __name__ == "__main__":
    main()

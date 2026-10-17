"""
黑客松参赛海报候选图生成（Seedream 文生图）

用法:
    ./venv/bin/python gen_posters.py

输出:
    ../posters/<概念名>.jpg

说明:
    - 密钥经 config.settings 从 .env 读取，不在任何输出中打印
    - 优先尝试竖版尺寸，API 不支持时自动回退 2K
"""
import asyncio
import os
import sys

import httpx

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config.settings import settings

# (文件名, 提示词) —— 全部要求画面无文字，文字后续用 PIL 叠加，避免模型渲染乱码
CONCEPTS = [
    (
        "01_hero_camera",
        "竖版产品海报主视觉：一台极具未来感的圆形相机悬浮在明亮现代的北欧风客厅中央，"
        "相机镜头发出柔和的青绿色光晕，镜头中映出改造后的精美房间景象；"
        "背景晨光透过白色纱帘，米色沙发、编织地毯、大型绿植、陶瓷花瓶；"
        "苹果发布会式的极简高级审美，大量留白，干净明亮的浅色背景，电影级柔光，"
        "超现实产品摄影质感，竖构图，画面中没有任何文字",
    ),
    (
        "02_before_after",
        "竖版海报：同一个客厅被一道发光的竖线分成左右两半，左边是改造前的朴素空荡房间，"
        "右边是改造后的精致温馨房间，新旧对比强烈；分割线中央悬浮一台小巧的相机发出柔和光芒；"
        "暖色调，生活气息，室内设计杂志摄影质感，竖构图，画面中没有任何文字",
    ),
    (
        "03_magic_moment",
        "竖版海报：一只手拿着一台精致的相机对准房间按下快门的瞬间，柔和的光波从镜头扩散开来，"
        "所到之处房间焕然一新，抱枕、地毯、窗帘、绿植如魔法般浮现；"
        "温暖的午后阳光，梦幻氛围，电影感光影，超现实主义，竖构图，画面中没有任何文字",
    ),
    (
        "04_minimal_collage",
        "竖版平面设计海报：大面积米白色留白背景，中央一个细线条的相机轮廓线稿，"
        "从镜头中飞出一张小小的精美房间照片和几件家居小物（抱枕、花瓶、地毯），"
        "构图轻盈优雅，莫兰迪色系，极简北欧风，高级感，竖构图，画面中没有任何文字",
    ),
]

OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "posters")
PORTRAIT_SIZE = "1664x2496"  # 竖版优先，API 不支持则回退 2K


async def generate_one(client: httpx.AsyncClient, headers: dict, name: str, prompt: str):
    for size in (PORTRAIT_SIZE, "2K"):
        body = {
            "model": settings.SEEDREAM_MODEL,
            "prompt": prompt,
            "response_format": "url",
            "size": size,
            "stream": False,
            "watermark": False,
        }
        resp = await client.post(
            f"{settings.SEEDREAM_API_URL}/images/generations",
            headers=headers,
            json=body,
        )
        if resp.status_code != 200:
            print(f"[retry] {name}: size={size} -> HTTP {resp.status_code} {resp.text[:150]}")
            continue
        url = (resp.json().get("data") or [{}])[0].get("url")
        if not url:
            print(f"[retry] {name}: size={size} -> 响应中没有图片 URL")
            continue
        img = await client.get(url)
        path = os.path.join(OUT_DIR, f"{name}.jpg")
        with open(path, "wb") as f:
            f.write(img.content)
        print(f"[OK] {name} (size={size}): {path} ({len(img.content) // 1024} KB)")
        return
    print(f"[FAIL] {name}: 所有尺寸均失败")


async def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    headers = {
        "Authorization": f"Bearer {settings.SEEDREAM_API_KEY}",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient(timeout=300.0, trust_env=False) as client:
        for name, prompt in CONCEPTS:
            await generate_one(client, headers, name, prompt)


if __name__ == "__main__":
    asyncio.run(main())

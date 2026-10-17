"""
腾讯云 SCF 云函数入口
使用 Mangum 将 FastAPI 适配为云函数
"""
import sys
import os

# 确保当前目录在 path 中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mangum import Mangum
from main import app

# 云函数入口 handler
handler = Mangum(app, lifespan="off")

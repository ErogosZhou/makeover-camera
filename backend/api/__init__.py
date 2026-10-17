"""
换装相机 API 路由
"""
from fastapi import APIRouter
from .routes import router as main_router
from .auth_routes import router as auth_router
from .history_routes import router as history_router
from .product_routes import router as product_router
from .search_routes import router as search_router

api_router = APIRouter()
api_router.include_router(main_router)
api_router.include_router(auth_router)
api_router.include_router(history_router)
api_router.include_router(product_router)
api_router.include_router(search_router)


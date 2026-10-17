"""
腾讯云 COS 存储服务
替代本地文件存储，用于 Serverless 环境
"""
import os
import uuid
from typing import Optional
from datetime import datetime
from loguru import logger

try:
    from qcloud_cos import CosConfig, CosS3Client
    HAS_COS_SDK = True
except ImportError:
    HAS_COS_SDK = False
    logger.warning("cos-python-sdk-v5 未安装，COS 功能不可用")


class COSStorageService:
    """腾讯云 COS 对象存储服务"""

    def __init__(self):
        self.enabled = False
        self.client = None
        self.bucket = None
        self.region = None
        self.cdn_domain = None

        # 从环境变量读取配置
        secret_id = os.getenv("COS_SECRET_ID")
        secret_key = os.getenv("COS_SECRET_KEY")
        self.region = os.getenv("COS_REGION", "ap-guangzhou")
        self.bucket = os.getenv("COS_BUCKET")
        self.cdn_domain = os.getenv("COS_CDN_DOMAIN")  # 可选：CDN 加速域名

        if not HAS_COS_SDK:
            logger.warning("COS SDK 未安装，将使用本地存储")
            return

        if not all([secret_id, secret_key, self.bucket]):
            logger.warning("COS 配置不完整，将使用本地存储")
            return

        try:
            config = CosConfig(
                Region=self.region,
                SecretId=secret_id,
                SecretKey=secret_key,
                Token=os.getenv("COS_TOKEN"),  # 使用临时密钥时需要
                Scheme="https"
            )
            self.client = CosS3Client(config)
            self.enabled = True
            logger.info(f"COS 存储已启用: {self.bucket}")
        except Exception as e:
            logger.error(f"COS 初始化失败: {e}")

    async def upload_file(
        self,
        file_content: bytes,
        filename: str,
        content_type: str = "image/jpeg",
        folder: str = "uploads"
    ) -> Optional[str]:
        """
        上传文件到 COS

        Args:
            file_content: 文件内容
            filename: 文件名
            content_type: MIME 类型
            folder: 存储文件夹

        Returns:
            文件访问 URL，失败返回 None
        """
        if not self.enabled:
            return None

        # 生成唯一文件名
        ext = filename.split(".")[-1].lower() if "." in filename else "jpg"
        unique_id = str(uuid.uuid4())
        key = f"{folder}/{unique_id}.{ext}"

        try:
            self.client.put_object(
                Bucket=self.bucket,
                Body=file_content,
                Key=key,
                ContentType=content_type
            )

            # 返回访问 URL
            if self.cdn_domain:
                url = f"https://{self.cdn_domain}/{key}"
            else:
                url = f"https://{self.bucket}.cos.{self.region}.myqcloud.com/{key}"

            logger.info(f"文件上传成功: {url}")
            return url

        except Exception as e:
            logger.error(f"COS 上传失败: {e}")
            return None

    async def upload_from_url(
        self,
        image_url: str,
        folder: str = "generated"
    ) -> Optional[str]:
        """
        从 URL 下载图片并上传到 COS
        用于保存 AI 生成的图片
        """
        if not self.enabled:
            return None

        import httpx

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(image_url, timeout=30)
                response.raise_for_status()

                content_type = response.headers.get("content-type", "image/jpeg")
                ext = "jpg"
                if "png" in content_type:
                    ext = "png"
                elif "webp" in content_type:
                    ext = "webp"

                return await self.upload_file(
                    file_content=response.content,
                    filename=f"image.{ext}",
                    content_type=content_type,
                    folder=folder
                )
        except Exception as e:
            logger.error(f"从 URL 上传失败: {e}")
            return None

    def get_presigned_url(self, key: str, expires: int = 3600) -> Optional[str]:
        """
        获取预签名 URL，用于临时访问私有文件

        Args:
            key: 对象键
            expires: 过期时间（秒）
        """
        if not self.enabled:
            return None

        try:
            url = self.client.get_presigned_url(
                Method="GET",
                Bucket=self.bucket,
                Key=key,
                Expired=expires
            )
            return url
        except Exception as e:
            logger.error(f"获取预签名 URL 失败: {e}")
            return None


# 全局实例
cos_storage = COSStorageService()

"""
性能监控中间件

记录每个API请求的：
- 请求开始时间戳
- 响应时间戳
- 耗时
- 状态码
"""
import time
from fastapi import Request
from loguru import logger


async def performance_logging_middleware(request: Request, call_next):
    """
    性能监控中间件

    记录格式：
    [PERF] GET /api/v1/task/xxx | 开始: 1708425600.123 | 结束: 1708425600.456 | 耗时: 333ms | 状态: 200
    """
    # 记录请求开始时间
    start_time = time.time()
    start_timestamp = time.time()

    # 记录请求信息
    method = request.method
    path = request.url.path
    client_ip = request.client.host if request.client else "unknown"

    logger.info(
        f"[PERF] ⏱️  请求开始 | {method} {path} | "
        f"客户端: {client_ip} | "
        f"时间戳: {start_timestamp:.3f}"
    )

    try:
        # 执行请求
        response = await call_next(request)

        # 记录响应信息
        end_time = time.time()
        end_timestamp = time.time()
        duration_ms = (end_time - start_time) * 1000

        # 根据耗时使用不同的日志级别
        if duration_ms < 100:
            log_level = "INFO"
            emoji = "✅"
        elif duration_ms < 500:
            log_level = "INFO"
            emoji = "⚠️"
        elif duration_ms < 2000:
            log_level = "WARNING"
            emoji = "🐌"
        else:
            log_level = "WARNING"
            emoji = "🚨"

        log_msg = (
            f"[PERF] {emoji} 请求完成 | {method} {path} | "
            f"状态: {response.status_code} | "
            f"耗时: {duration_ms:.2f}ms | "
            f"开始: {start_timestamp:.3f} | "
            f"结束: {end_timestamp:.3f}"
        )

        if log_level == "WARNING":
            logger.warning(log_msg)
        else:
            logger.info(log_msg)

        return response

    except Exception as e:
        # 记录错误
        end_time = time.time()
        duration_ms = (end_time - start_time) * 1000

        logger.error(
            f"[PERF] ❌ 请求失败 | {method} {path} | "
            f"错误: {str(e)} | "
            f"耗时: {duration_ms:.2f}ms"
        )
        raise


def log_external_api_call(service_name: str, operation: str):
    """
    装饰器：记录外部API调用的性能

    用法：
    @log_external_api_call("VLLM", "生成prompt")
    async def generate_prompt(...):
        ...
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            start_timestamp = time.time()

            logger.info(
                f"[API] 🚀 开始调用 | {service_name}.{operation} | "
                f"时间戳: {start_timestamp:.3f}"
            )

            try:
                result = await func(*args, **kwargs)

                end_time = time.time()
                end_timestamp = time.time()
                duration_ms = (end_time - start_time) * 1000

                # 根据耗时标记
                if duration_ms < 1000:
                    emoji = "⚡"
                elif duration_ms < 5000:
                    emoji = "✅"
                elif duration_ms < 10000:
                    emoji = "🐌"
                else:
                    emoji = "🚨"

                logger.info(
                    f"[API] {emoji} 调用完成 | {service_name}.{operation} | "
                    f"耗时: {duration_ms:.2f}ms | "
                    f"开始: {start_timestamp:.3f} | "
                    f"结束: {end_timestamp:.3f}"
                )

                return result

            except Exception as e:
                end_time = time.time()
                duration_ms = (end_time - start_time) * 1000

                logger.error(
                    f"[API] ❌ 调用失败 | {service_name}.{operation} | "
                    f"错误: {str(e)} | "
                    f"耗时: {duration_ms:.2f}ms"
                )
                raise

        return wrapper
    return decorator


class PerformanceTimer:
    """
    性能计时器上下文管理器

    用法：
    async with PerformanceTimer("数据库查询"):
        result = await db.query(...)
    """

    def __init__(self, operation_name: str):
        self.operation_name = operation_name
        self.start_time = None
        self.start_timestamp = None

    def __enter__(self):
        self.start_time = time.time()
        self.start_timestamp = time.time()
        logger.info(
            f"[TIMER] ⏱️  开始 | {self.operation_name} | "
            f"时间戳: {self.start_timestamp:.3f}"
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        end_time = time.time()
        end_timestamp = time.time()
        duration_ms = (end_time - self.start_time) * 1000

        if exc_type is None:
            emoji = "✅" if duration_ms < 1000 else "🐌"
            logger.info(
                f"[TIMER] {emoji} 完成 | {self.operation_name} | "
                f"耗时: {duration_ms:.2f}ms | "
                f"开始: {self.start_timestamp:.3f} | "
                f"结束: {end_timestamp:.3f}"
            )
        else:
            logger.error(
                f"[TIMER] ❌ 失败 | {self.operation_name} | "
                f"错误: {exc_val} | "
                f"耗时: {duration_ms:.2f}ms"
            )

        return False  # 不抑制异常

    async def __aenter__(self):
        return self.__enter__()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return self.__exit__(exc_type, exc_val, exc_tb)

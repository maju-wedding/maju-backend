from time import perf_counter_ns

from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware


class LoggingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        logger.info("Service started initializing")

    async def dispatch(self, request, call_next):
        start_time = perf_counter_ns()

        # 요청 경로 로깅
        path = request.url.path
        method = request.method
        host = request.client.host or "unknown"

        try:
            response = await call_next(request)
            end_time = perf_counter_ns()

            duration_ns = end_time - start_time

            # 시간 단위를 동적으로 조정
            if duration_ns < 1000:
                duration_str = f"{duration_ns}ns"
            elif duration_ns < 1_000_000:
                duration_str = f"{duration_ns/1000:.2f}μs"
            elif duration_ns < 1_000_000_000:
                duration_str = f"{duration_ns/1_000_000:.2f}ms"
            else:
                duration_str = f"{duration_ns/1_000_000_000:.2f}s"

            # 상태 코드에 따라 로그 레벨 조정
            format = f"{host} {method} {path} {response.status_code} {duration_str}"
            if 200 <= response.status_code < 400:
                logger.info(format)
            elif 400 <= response.status_code < 500:
                logger.warning(format)
            else:
                logger.error(format)

            return response

        except Exception as e:
            end_time = perf_counter_ns()
            duration_ns = end_time - start_time

            # 시간 단위 조정
            if duration_ns < 1000:
                duration_str = f"{duration_ns}ns"
            elif duration_ns < 1_000_000:
                duration_str = f"{duration_ns/1000:.2f}μs"
            elif duration_ns < 1_000_000_000:
                duration_str = f"{duration_ns/1_000_000:.2f}ms"
            else:
                duration_str = f"{duration_ns/1_000_000_000:.2f}s"

            logger.exception(f"{host} {method} {path} 500 {duration_str} - {str(e)}")
            raise

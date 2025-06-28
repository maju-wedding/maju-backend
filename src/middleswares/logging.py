from time import perf_counter_ns

from fastapi import HTTPException
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware


class LoggingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)

    async def dispatch(self, request, call_next):
        start_time = perf_counter_ns()

        # 요청 경로 로깅
        path = request.url.path
        method = request.method
        host = request.client.host or "unknown"

        # 건강체크나 정적파일 요청은 로깅 제외
        if path in ["/health", "/"] or path.startswith("/static"):
            return await call_next(request)

        try:
            response = await call_next(request)
            end_time = perf_counter_ns()
            duration_ns = end_time - start_time

            # 시간 단위를 동적으로 조정
            duration_str = self._format_duration(duration_ns)

            # 상태 코드에 따라 로그 레벨 조정 - 단순하게
            log_format = f"{method} {path} {response.status_code} {duration_str}"

            if 200 <= response.status_code < 400:
                logger.info(log_format)
            elif 400 <= response.status_code < 500:
                # 4xx 에러는 경고 레벨 (클라이언트 문제)
                logger.warning(log_format)
            else:
                # 5xx 에러는 에러 레벨 (서버 문제)
                logger.error(log_format)

            return response

        except HTTPException:
            # HTTPException은 이미 exception handler에서 처리되므로 
            # 여기서는 re-raise만 하고 로깅하지 않음
            raise

        except Exception as e:
            end_time = perf_counter_ns()
            duration_ns = end_time - start_time
            duration_str = self._format_duration(duration_ns)

            # 미들웨어에서는 간단한 에러 로깅만
            error_name = e.__class__.__name__
            logger.error(f"{method} {path} 500 {duration_str} - {error_name}")

            # Exception을 re-raise해서 exception handler가 처리하도록
            raise

    def _format_duration(self, duration_ns: int) -> str:
        """duration을 읽기 쉬운 형태로 포맷"""
        if duration_ns < 1000:
            return f"{duration_ns}ns"
        elif duration_ns < 1_000_000:
            return f"{duration_ns/1000:.2f}μs"
        elif duration_ns < 1_000_000_000:
            return f"{duration_ns/1_000_000:.2f}ms"
        else:
            return f"{duration_ns/1_000_000_000:.2f}s"
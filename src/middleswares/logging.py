from time import perf_counter

from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        start_time = perf_counter()
        response = await call_next(request)
        end_time = perf_counter()

        logger.info(
            f"{request.method} {request.url} {response.status_code} {end_time - start_time:.2f}s"
        )
        return response

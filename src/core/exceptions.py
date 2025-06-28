from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import ORJSONResponse
from loguru import logger


class CustomHTTPException(HTTPException):
    """커스텀 HTTP 예외 - 로깅 제어를 위함"""

    def __init__(self, status_code: int, detail: str, log_error: bool = True):
        super().__init__(status_code=status_code, detail=detail)
        self.log_error = log_error


class InvalidToken(Exception):
    pass


class InvalidAuthorizationCode(Exception):
    pass


async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP 예외 처리 - 간단한 에러 응답만"""
    # 4xx 에러는 INFO 레벨로, 5xx 에러는 ERROR 레벨로
    if 400 <= exc.status_code < 500:
        logger.info(
            f"Client error {exc.status_code}: {exc.detail} - {request.method} {request.url.path}"
        )
    else:
        logger.error(
            f"Server error {exc.status_code}: {exc.detail} - {request.method} {request.url.path}"
        )

    return ORJSONResponse(
        content={"detail": exc.detail},
        status_code=exc.status_code,
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """입력 검증 예외 처리 - 필요한 정보만 로깅"""
    error_details = []
    for error in exc.errors():
        field = " -> ".join(str(loc) for loc in error.get("loc", []))
        message = error.get("msg", "Invalid input")
        error_details.append(f"{field}: {message}")

    error_summary = "; ".join(error_details)
    logger.warning(
        f"Validation error: {error_summary} - {request.method} {request.url.path}"
    )

    return ORJSONResponse(
        content={"detail": "입력 데이터가 올바르지 않습니다.", "errors": error_details},
        status_code=422,
    )


async def unknown_exception_handler(request: Request, exc: Exception):
    """알 수 없는 예외 처리 - 간단한 로깅"""
    # 에러의 핵심 정보만 로깅
    error_name = exc.__class__.__name__
    error_message = str(exc)

    # 개발 환경에서만 상세 스택트레이스 로깅
    import os

    if os.getenv("ENVIRONMENT") == "development":
        logger.exception(
            f"Unhandled {error_name}: {error_message} - {request.method} {request.url.path}"
        )
    else:
        logger.error(
            f"Unhandled {error_name}: {error_message} - {request.method} {request.url.path}"
        )

    return ORJSONResponse(
        content={"detail": "서버 내부 오류가 발생했습니다."},
        status_code=500,
    )


exception_handlers = {
    HTTPException: http_exception_handler,
    RequestValidationError: validation_exception_handler,
    Exception: unknown_exception_handler,
}

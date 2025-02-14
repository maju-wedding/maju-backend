from fastapi import HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import ORJSONResponse


class InvalidToken(Exception):
    pass


class InvalidAuthorizationCode(Exception):
    pass


async def http_exception_handler(request, exc: HTTPException):
    return ORJSONResponse(
        content={"detail": exc.detail},
        status_code=exc.status_code,
    )


async def validation_exception_handler(request, exc: RequestValidationError):
    return ORJSONResponse(
        content={"detail": exc.errors()},
        status_code=400,
    )


async def unknown_exception_handler(request, exc: Exception):
    return ORJSONResponse(
        content={"detail": "Internal server error"},
        status_code=500,
    )


exception_handlers = {
    HTTPException: http_exception_handler,
    RequestValidationError: validation_exception_handler,
    Exception: unknown_exception_handler,
}

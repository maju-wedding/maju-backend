import sys

from loguru import logger

from core.config import settings


def setup_logging():
    """로깅 설정"""
    # 기본 로거 제거
    logger.remove()

    # 개발 환경과 운영 환경에 따른 로그 레벨 설정
    if settings.ENVIRONMENT != "production":
        log_level = "DEBUG"
        log_format = (
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        )
    else:
        log_level = "INFO"
        log_format = "{time:YYYY-MM-DD HH:mm:ss} | " "{level: <8} | " "{message}"

    # 콘솔 로거 추가
    logger.add(
        sys.stderr,
        format=log_format,
        level=log_level,
        colorize=True,
        backtrace=False,  # 스택트레이스 간소화
        diagnose=False,  # 변수 값 표시 비활성화
    )

    # 파일 로거 추가 (선택사항)
    # if settings.ENVIRONMENT == "production":
    #     logger.add(
    #         "logs/app.log",
    #         format=log_format,
    #         level=log_level,
    #         rotation="1 day",
    #         retention="30 days",
    #         compression="zip",
    #         backtrace=False,
    #         diagnose=False,
    #     )

    return logger


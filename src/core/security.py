from datetime import datetime, timedelta
from typing import Any

import jwt
from fastapi.security import OAuth2PasswordBearer, HTTPBearer
from passlib.context import CryptContext

from core.config import settings
from core.enums import UserTypeEnum

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = "HS256"


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="api/v1/auth/login",  # 로그인 엔드포인트 경로
    scheme_name="User Login",  # 스웨거에 표시될 이름
    description="Use email and password to login",  # 스웨거에 표시될 설명
)

# Bearer 토큰을 위한 스키마 (기존 코드)
bearer_scheme = HTTPBearer(
    auto_error=True,
    description="JWT token from social/guest login",
)


def create_access_token(
    subject: str | Any,
    expires_delta: timedelta,
    user_type: UserTypeEnum = UserTypeEnum.local,
    extra_claims: dict | None = None,
) -> str:
    """
    Create JWT access token with enhanced claims

    Args:
        subject: Primary identifier (user ID or email)
        expires_delta: Token expiration time
        user_type: Type of user (e.g., "guest", "social", "local")
        extra_claims: Additional claims to include in token
    """
    expire = datetime.utcnow() + expires_delta

    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "type": user_type.value,
        "iat": datetime.utcnow(),
    }

    if extra_claims:
        to_encode.update(extra_claims)

    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

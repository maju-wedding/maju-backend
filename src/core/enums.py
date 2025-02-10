from enum import Enum


class SocialProviderEnum(Enum):
    naver = "naver"
    kakao = "kakao"

class UserTypeEnum(Enum):
    guest = "guest"
    local = "local"
    social = "social"

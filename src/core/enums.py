from enum import Enum


class SocialProviderEnum(Enum):
    naver = "naver"
    kakao = "kakao"


class UserTypeEnum(Enum):
    guest = "guest"
    local = "local"
    social = "social"


class CategoryTypeEnum(Enum):
    hall = "hall"
    studio = "studio"
    dress = "dress"
    makeup = "makeup"

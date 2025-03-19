from enum import Enum


class SocialProviderEnum(str, Enum):
    naver = "naver"
    kakao = "kakao"


class UserTypeEnum(str, Enum):
    guest = "guest"
    local = "local"
    social = "social"


class CategoryTypeEnum(str, Enum):
    hall = "hall"
    studio = "studio"
    dress = "dress"
    makeup = "makeup"


class GenderEnum(str, Enum):
    male = "male"
    female = "female"

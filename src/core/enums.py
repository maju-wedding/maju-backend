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
    suit = "suit"
    wsuit = "wsuit"
    gift = "gift"
    tour = "tour"
    hanbok = "hanbok"
    main_snap = "main_snap"
    main_movie = "main_movie"
    etc = "etc"


class GenderEnum(str, Enum):
    male = "male"
    female = "female"

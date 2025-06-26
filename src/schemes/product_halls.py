from pydantic import computed_field
from sqlmodel import SQLModel, Field

from models import ProductImage
from schemes.products import ProductCreate


class ProductHallCreate(ProductCreate):
    address: str
    latitude: float
    longitude: float
    min_capacity: int
    max_capacity: int
    parking_capacity: int


class ProductHallCreateInternal(ProductHallCreate):
    product_id: int


class ProductHallListRead(SQLModel):
    id: int
    hashtags: list[str]
    name: str
    sido: str
    gugun: str
    address: str
    image_urls: list[str] | None


class ProductHallSearchRead(SQLModel):
    id: int
    name: str
    sido: str
    gugun: str
    address: str
    thumbnail_url: str
    subway_line: str | None
    subway_name: str | None


class HallAmenitiesRead(SQLModel):
    elevator_count: int
    atm_count: int
    has_family_waiting_room: bool
    has_pyebaek_room: bool


class HallVenueAmenitiesRead(SQLModel):
    has_bride_room: bool = False
    has_pyebaek_room: bool = False
    has_banquet_hall: bool = False
    bride_room_image_urls: list[str] | None = None
    pyebaek_room_image_urls: list[str] | None = None
    banquet_hall_image_urls: list[str] | None = None


class HallAIReviewRead(SQLModel):
    review_type: str
    content: str | None


class ProductHallImage(SQLModel):
    image_type: str
    image_url: str


class HallVenueRead(SQLModel):
    id: int
    name: str
    wedding_interval: int
    wedding_times: str
    wedding_type: str
    hall_styles: str
    hall_types: str
    guaranteed_min_count: int
    min_capacity: int
    max_capacity: int
    basic_price: int
    peak_season_price: int
    ceiling_height: int
    virgin_road_length: int
    include_drink: bool
    include_alcohol: bool
    include_service_fee: bool
    include_vat: bool
    bride_room_entry_methods: str
    bride_room_makeup_room: bool
    food_menu: str
    food_cost_per_adult: int
    food_cost_per_child: int
    banquet_hall_running_time: int
    banquet_hall_max_capacity: int
    additional_info: str
    special_notes: str

    # images 필드는 숨김
    images: list["ProductImage"] = Field(default=[], exclude=True)

    @computed_field
    @property
    def image_urls(self) -> list[str]:
        return [img.image_url for img in self.images] if self.images else []

    amenities_info: HallVenueAmenitiesRead = None


class HallScoreRead(SQLModel):
    score_type: str
    value: float


# 점수 통계 스키마
class ScoreStatistics(SQLModel):
    """점수 통계 정보"""

    average: float
    min_score: float
    max_score: float
    total_count: int


# 점수 비교 정보
class HallScoreComparison(SQLModel):
    """웨딩홀 점수와 평균 비교"""

    score_type: str
    hall_score: float | None = None
    average: float
    difference: float  # 평균 대비 차이 (양수면 평균 이상, 음수면 평균 이하)


# 전체 점수 요약
class HallScoreSummary(SQLModel):
    """웨딩홀 점수 요약"""

    overall_score: float | None = 0  # 전체 평균 점수
    overall_average: float  # 전체 평균
    score_comparisons: list[HallScoreComparison]  # 카테고리별 점수 비교


class HallBlogRead(SQLModel):
    title: str
    description: str
    link_url: str
    thumbnail_url: str


class ProductHallRead(SQLModel):
    id: int
    name: str
    hashtags: list[str]
    subway_line: str | None
    subway_name: str | None
    way_text: str | None
    park_limit: int
    park_free_hours: int
    sido: str
    gugun: str
    dong: str
    address: str

    has_single_hall: bool
    max_price: int
    min_price: int

    hall_amenities_info: HallAmenitiesRead
    venues: list[HallVenueRead]

    ai_reviews: list[HallAIReviewRead]
    ai_score_summary: HallScoreSummary

    blogs: list[HallBlogRead] = []

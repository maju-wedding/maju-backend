from sqlmodel import SQLModel

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


class HallRead(SQLModel):
    elevator_count: int
    atm_count: int
    has_family_waiting_room: bool
    has_pyebaek_room: bool


class HallAIReviewRead(SQLModel):
    review_type: str
    content: str


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
    images: list[ProductHallImage] = []
    # facility_images: list[str] = []


class HallScoreRead(SQLModel):
    score_type: str
    value: float


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

    hall: HallRead
    ai_reviews: list[HallAIReviewRead]
    venues: list[HallVenueRead]
    scores: list[HallScoreRead]

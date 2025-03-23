import datetime
import json
import re
import traceback
from typing import Any, List, Tuple

import psycopg2
from psycopg2.extras import RealDictCursor
from sqlalchemy import text
from sqlmodel import Session, select, create_engine

from core.config import settings
from models.product_ai_review import ProductAIReview
from models.product_hall_venues import (
    ProductHallStyle,
    ProductHallType,
    ProductHallFoodType,
    ProductHallVenueTypeLink,
    ProductHallStyleLink,
    ProductHallVenue,
)
from models.product_halls import ProductHall
from models.products import Product, ProductImage

PROD_PG_CONNECTION = {
    "host": settings.POSTGRES_SERVER,
    "database": settings.POSTGRES_DB,
    "user": settings.POSTGRES_USER,
    "password": settings.POSTGRES_PASSWORD,
    "port": settings.POSTGRES_PORT,
}


reference_engine = create_engine(settings.DATABASE_URI)
target_engine = create_engine(settings.DATABASE_URI)


def connect_to_reference_postgres():
    """PostgreSQL 데이터베이스에 연결"""
    try:
        conn = psycopg2.connect(**PROD_PG_CONNECTION, cursor_factory=RealDictCursor)
        return conn
    except Exception as e:
        print(f"데이터베이스 연결 오류: {e}")
        raise


def fetch_source_data() -> tuple[list[dict], list[dict], list[dict], list[dict]]:
    """소스 테이블에서 데이터 가져오기"""
    conn = connect_to_reference_postgres()
    cursor = conn.cursor()

    # iw_wedding_hall_info 데이터 가져오기
    cursor.execute("SELECT * FROM reference.iw_wedding_hall_info")
    hall_infos = cursor.fetchall()
    print(f"iw_wedding_hall_info 데이터 수: {len(hall_infos)}")

    # iw_wedding_halls 데이터 가져오기
    cursor.execute("SELECT * FROM reference.iw_wedding_halls")
    iw_halls = cursor.fetchall()
    print(f"iw_wedding_halls 데이터 수: {len(iw_halls)}")

    # wb_wedding_halls 데이터 가져오기
    cursor.execute("SELECT * FROM reference.wb_wedding_halls")
    wb_halls = cursor.fetchall()
    print(f"wb_wedding_halls 데이터 수: {len(wb_halls)}")

    # iw_wedding_hall_type 데이터 가져오기 (venue 정보)
    cursor.execute("SELECT * FROM reference.iw_wedding_hall_type")
    hall_venues = cursor.fetchall()
    print(f"iw_wedding_hall_type 데이터 수: {len(hall_venues)}")

    cursor.close()
    conn.close()

    return hall_infos, iw_halls, wb_halls, hall_venues


def create_hall_mapping(
    hall_infos: list[dict],
    iw_halls: list[dict],
    wb_halls: list[dict],
    hall_venues: list[dict],
) -> dict[int, dict[str, Any]]:
    """결혼식장 데이터 매핑 생성"""
    # banquet_code를 키로 사용하여 hall_info 매핑
    hall_info_mapping = {
        info["banquet_code"]: info for info in hall_infos if info["banquet_code"]
    }

    # banquet_code를 키로 venue 정보 매핑
    hall_venue_mapping = {}
    for venue in hall_venues:
        banquet_code = venue.get("banquet_code")
        if banquet_code:
            if banquet_code not in hall_venue_mapping:
                hall_venue_mapping[banquet_code] = []
            hall_venue_mapping[banquet_code].append(venue)

    # banquet_code와 매칭되는 iw_halls 매핑
    hall_mapping = {}

    for iw_hall in iw_halls:
        banquet_code = iw_hall.get("wedding_hall_banquet_code")
        if not banquet_code:
            continue

        hall_info = hall_info_mapping.get(banquet_code)
        if not hall_info:
            continue

        # 기본 매핑 생성
        hall_mapping[banquet_code] = {
            "hall_info": hall_info,
            "iw_hall": iw_hall,
            "wb_hall": None,
            "venues": hall_venue_mapping.get(banquet_code, []),
        }

    # wb_wedding_halls 데이터 추가 매핑 (이름 기반)
    for wb_hall in wb_halls:
        for banquet_code, mapping in hall_mapping.items():
            hall_info = mapping["hall_info"]
            # 이름이 일치하는 경우 매핑
            if (
                wb_hall["name"]
                and hall_info["name"]
                and wb_hall["name"].lower() == hall_info["name"].lower()
            ):
                mapping["wb_hall"] = wb_hall
                break

    return hall_mapping


def parse_hall_types(hall_info: dict, iw_hall: dict, wb_hall: dict | None) -> List[str]:
    """결혼식장 유형 파싱 (여러 타입 반환)"""
    # 허용된 hall_type 값들
    ALLOWED_HALL_TYPES = [
        "채플",
        "호텔",
        "컨벤션",
        "하우스",
        "야외",
        "한옥",
        "소규모",
        "기타",
    ]

    result_types = []

    # wb_wedding_halls에서 타입 추출
    if wb_hall and wb_hall.get("tag_타입"):
        wb_type = wb_hall["tag_타입"]
        # 허용된 타입과 일치하는지 확인
        for allowed_type in ALLOWED_HALL_TYPES:
            if allowed_type in wb_type and allowed_type not in result_types:
                result_types.append(allowed_type)

    # 스타일과 해시태그에서 타입 추출
    styles = hall_info.get("styles") or hall_info.get("style") or ""
    hashtag = iw_hall.get("hashtag", "").lower() if iw_hall else ""

    # 허용된 타입 순서대로 확인
    for allowed_type in ALLOWED_HALL_TYPES:
        if allowed_type == "기타":  # 기타는 마지막에 확인
            continue

        if (
            allowed_type in styles or allowed_type in hashtag
        ) and allowed_type not in result_types:
            result_types.append(allowed_type)

        # 영문명이나 다른 표현 확인
        if (
            allowed_type == "호텔"
            and ("호텔" in styles or "호텔" in hashtag)
            and "호텔" not in result_types
        ):
            result_types.append("호텔")
        elif (
            allowed_type == "야외"
            and ("가든" in styles or "가든" in hashtag or "야외" in hashtag)
            and "야외" not in result_types
        ):
            result_types.append("야외")
        elif (
            allowed_type == "소규모"
            and ("스몰" in styles or "스몰" in hashtag)
            and "소규모" not in result_types
        ):
            result_types.append("소규모")

    # 결과가 없으면 기타 추가
    if not result_types:
        result_types.append("기타")

    return result_types


def parse_hall_styles(wb_hall: dict) -> List[str]:
    """결혼식장 스타일 파싱 (여러 스타일 반환)"""
    result_styles = []

    if not wb_hall:
        return ["모던"]  # 기본 스타일

    styles = wb_hall.get("tag_타입") or ""

    # 스타일 매핑
    style_mappings = {
        "밝은": ["밝은", "화이트", "화사한"],
        "어두운": ["어두운", "블랙", "시크한"],
        "모던": ["모던", "심플", "미니멀"],
        "클래식": ["클래식", "전통", "앤틱"],
        "럭셔리": ["럭셔리", "고급", "호화"],
    }

    # 스타일 키워드 확인
    for style_key, keywords in style_mappings.items():
        for keyword in keywords:
            if keyword in styles and style_key not in result_styles:
                result_styles.append(style_key)

    # 결과가 없으면 기본 스타일 추가
    if not result_styles:
        result_styles.append("모던")

    return result_styles


def parse_wedding_type(hall_info: dict, iw_hall: dict, wb_hall: dict | None) -> str:
    """웨딩 진행 방식 파싱"""
    # 예시 데이터에서 확인한 형식 처리
    # "동시;분리" 형태로 저장된 경우의 처리

    if wb_hall and wb_hall.get("tag_예식형태"):
        if "분리" in wb_hall["tag_예식형태"]:
            return "분리"
        elif "동시" in wb_hall["tag_예식형태"]:
            return "동시"

    # iw_wedding_halls의 hashtag 필드 확인
    hashtag = iw_hall.get("hashtag", "").lower() if iw_hall else ""
    if "분리예식" in hashtag:
        return "분리"
    elif "동시예식" in hashtag:
        return "동시"

    # 기본값
    return "동시"


def parse_food_type_and_cost(
    hall_info: dict, iw_hall: dict, wb_hall: dict | None, venue_data: dict
) -> Tuple[str, float]:
    """음식 유형과 비용 파싱"""
    food_type = "뷔페"  # 기본값
    food_cost = 0

    # wb_wedding_halls에서 메뉴 정보 확인
    if wb_hall and wb_hall.get("tag_메뉴"):
        menu_tag = wb_hall.get("tag_메뉴").lower()
        if "뷔페" in menu_tag:
            food_type = "뷔페"
        elif "코스" in menu_tag:
            food_type = "코스"
        elif "한상" in menu_tag:
            food_type = "한상"

    # iw_wedding_hall_info의 foodDisplay 확인
    if food_type == "뷔페" and hall_info.get("foodDisplay"):
        food_display = hall_info.get("foodDisplay").lower()
        if "코스" in food_display:
            food_type = "코스"
        elif "한상" in food_display:
            food_type = "한상"

    # 해시태그 확인
    hashtag = iw_hall.get("hashtag", "").lower() if iw_hall else ""
    if food_type == "뷔페" and "한상차림" in hashtag:
        food_type = "한상"
    elif food_type == "뷔페" and "코스" in hashtag:
        food_type = "코스"

    # 음식 비용 확인
    # 먼저 venue_data 확인
    if venue_data and venue_data.get("min_meal"):
        food_cost = float(venue_data.get("min_meal"))
    elif venue_data and venue_data.get("min_food_fee"):
        food_cost = float(venue_data.get("min_food_fee"))

    # wb_hall의 식대 정보 확인
    elif wb_hall and wb_hall.get("tag_식대_최소"):
        try:
            cost_str = "".join(c for c in wb_hall.get("tag_식대_최소") if c.isdigit())
            if cost_str:
                food_cost = int(cost_str)
        except:
            pass

    # hall_info의 min_food 확인
    elif hall_info.get("min_food"):
        food_cost = float(hall_info.get("min_food"))

    # 최소 기본값 설정
    if food_cost <= 0:
        food_cost = {"뷔페": 60000, "코스": 80000, "한상": 100000}.get(food_type, 70000)

    return food_type, food_cost


def parse_wedding_times_and_interval(
    venue_data: dict, hall_info: dict
) -> Tuple[int, str]:
    """웨딩 시간 및 간격 파싱"""
    # 기본값
    wedding_interval = 60

    # timeDisplay 필드에서 시간 정보 확인
    time_display = venue_data.get("timeDisplay", "")

    # 간격 정보 추출 시도
    interval_match = re.search(r"(\d+)분", str(time_display))
    if interval_match:
        wedding_interval = int(interval_match.group(1))

    # time_val 확인
    if venue_data.get("time_val") and str(venue_data.get("time_val")).isdigit():
        wedding_interval = int(venue_data.get("time_val"))

    # 해시태그에서 확인
    hashtag = venue_data.get("hashtag", "").lower() if venue_data else ""
    if "60분이하" in hashtag:
        wedding_interval = 60
    elif "70~90분" in hashtag:
        wedding_interval = 80
    elif "100~120분" in hashtag:
        wedding_interval = 110
    elif "130~180분" in hashtag:
        wedding_interval = 150
    elif "240분이상" in hashtag:
        wedding_interval = 240

    # 웨딩 시간 생성
    start_time = datetime.time(11, 0)
    wedding_times = []

    # 간격에 따라 4개 시간대 생성
    for i in range(4):
        hour = (
            start_time.hour + ((start_time.minute + i * wedding_interval) // 60)
        ) % 24
        minute = (start_time.minute + i * wedding_interval) % 60
        wedding_times.append(f"{hour:02d}:{minute:02d}")

    return wedding_interval, ", ".join(wedding_times)


def parse_hall_pricing(
    venue_data: dict, hall_info: dict, iw_hall: dict
) -> Tuple[int, int]:
    """홀 가격 정보 파싱"""
    # 기본값
    basic_price = 0

    # min_grand 확인 (가장 정확한 출처)
    if venue_data.get("min_grand"):
        basic_price = float(venue_data.get("min_grand"))
    # fees JSON에서 확인
    elif venue_data.get("fees"):
        fees = sanitize_json(venue_data.get("fees"))
        if fees and "grand" in fees and "minFee" in fees["grand"]:
            basic_price = float(fees["grand"]["minFee"])
    # 음식 비용 기반 추정
    elif hall_info.get("min_food"):
        food_cost = float(hall_info.get("min_food", 0))
        # 평균 손님 수 * 음식 비용
        avg_guests = (
            int(hall_info.get("min_person", 100))
            + int(hall_info.get("max_person", 200))
        ) / 2
        basic_price = avg_guests * food_cost

    # 여전히 가격 정보가 없다면 기본값 사용
    if basic_price <= 0:
        basic_price = 5000000

    # 성수기 가격 확인
    peak_season_price = 0
    if venue_data.get("max_grand") and float(venue_data.get("max_grand")) > basic_price:
        peak_season_price = float(venue_data.get("max_grand"))
    else:
        # 기본 가격의 1.2배로 추정
        peak_season_price = int(basic_price * 1.2)

    return int(basic_price), peak_season_price


def parse_amenities(
    hall_info: dict, iw_hall: dict, wb_hall: dict = None
) -> dict[str, bool]:
    """편의시설 정보 파싱"""
    hashtag = iw_hall.get("hashtag", "").lower() if iw_hall else ""
    sell_point = hall_info.get("sell_point", "")
    sell_point_data = sanitize_json(sell_point)

    # wb_hall 태그 데이터 확인
    wb_tags = ""
    if wb_hall:
        wb_tags = f"{wb_hall.get('tag_타입', '')} {wb_hall.get('tag_예식형태', '')} {wb_hall.get('tag_메뉴', '')}"

    # 기본값 설정
    amenities = {
        "elevator": False,
        "valet_parking": False,
        "pyebaek_room": False,
        "family_waiting_room": False,
        "atm": False,
        "dress_room": False,
        "smoking_area": False,
        "photo_zone": False,
        "include_drink": False,
        "include_alcohol": False,
        "include_service_fee": True,
        "include_vat": True,
        "bride_room_makeup_room": False,
    }

    # 키워드 매핑
    amenity_keywords = {
        "elevator": ["엘리베이터", "리프트", "elevator", "승강기"],
        "valet_parking": [
            "발렛",
            "주차",
            "셔틀",
            "valet",
            "parking",
            "주차장",
            "주차시설",
        ],
        "pyebaek_room": ["폐백", "피로연", "pyebaek", "폐백실", "전통혼례"],
        "family_waiting_room": ["가족", "대기실", "가족실", "waiting room", "웨이팅"],
        "atm": ["ATM", "현금인출기", "입출금기", "현금서비스"],
        "dress_room": [
            "드레스",
            "드레스룸",
            "파우더",
            "파우더룸",
            "dress room",
            "탈의실",
        ],
        "smoking_area": ["흡연", "흡연실", "smoking", "흡연구역"],
        "photo_zone": ["포토", "사진", "photo zone", "포토존", "사진촬영", "웨딩촬영"],
        "include_drink": [
            "음료",
            "드링크",
            "drink",
            "주스",
            "소프트드링크",
            "웰컴드링크",
        ],
        "include_alcohol": ["주류", "알코올", "와인", "맥주", "alcohol", "위스키"],
        "bride_room_makeup_room": [
            "신부대기실",
            "메이크업",
            "화장실",
            "makeup room",
            "신부실",
        ],
    }

    # 모든 텍스트 소스 확인
    all_text = f"{hashtag} {sell_point} {wb_tags}"

    # sell_point_data가 리스트인 경우 항목 추가
    if isinstance(sell_point_data, list):
        for item in sell_point_data:
            if isinstance(item, str):
                all_text += " " + item
            elif isinstance(item, dict) and "text" in item:
                all_text += " " + item["text"]

    # 전체 텍스트에서 키워드 확인
    for amenity, keywords in amenity_keywords.items():
        for keyword in keywords:
            if keyword in all_text.lower():
                amenities[amenity] = True
                break

    return amenities


def parse_bride_room_info(hall_info: dict, iw_hall: dict, wb_hall: dict = None) -> str:
    """신부실 정보 파싱"""
    # 기본값
    entry_methods = "일반 입구"

    hashtag = iw_hall.get("hashtag", "").lower() if iw_hall else ""
    sell_point = hall_info.get("sell_point", "")
    sell_point_data = sanitize_json(sell_point)

    # 결합 텍스트
    all_text = f"{hashtag} {sell_point}"
    if wb_hall:
        all_text += f" {wb_hall.get('tag_타입', '')}"

    # sell_point_data가 리스트인 경우 항목 추가
    if isinstance(sell_point_data, list):
        for item in sell_point_data:
            if isinstance(item, str):
                all_text += " " + item

    # 입구 방법 키워드
    entry_method_keywords = {
        "전용 엘리베이터": [
            "전용 엘리베이터",
            "신부 전용",
            "전용 리프트",
            "신부 엘리베이터",
        ],
        "VIP 입구": ["VIP 입구", "VIP 통로", "별도 입구", "VIP 동선"],
        "비공개 입구": ["비공개 입구", "프라이빗 입구", "독립 입구", "별도 통로"],
    }

    # 입구 방법 키워드 확인
    for method, keywords in entry_method_keywords.items():
        for keyword in keywords:
            if keyword in all_text.lower():
                entry_methods = method
                return entry_methods

    return entry_methods


def parse_hall_physical_attributes(
    venue_data: dict, hall_info: dict, iw_hall: dict
) -> tuple[int, int]:
    """홀 물리적 속성 파싱"""
    # 기본값
    ceiling_height = 5
    virgin_road_length = 15

    # sell_point 확인
    sell_point = hall_info.get("sell_point", "")
    sell_point_data = sanitize_json(sell_point)

    # 결합 텍스트
    all_text = ""
    if isinstance(sell_point_data, list):
        for item in sell_point_data:
            if isinstance(item, str):
                all_text += " " + item
    elif isinstance(sell_point, str):
        all_text = sell_point

    # 천장 높이 정보 검색
    ceiling_matches = re.findall(r"천장\s*높이\s*(\d+(?:\.\d+)?)", all_text)
    ceiling_matches += re.findall(r"층고\s*(\d+(?:\.\d+)?)", all_text)

    if ceiling_matches:
        for match in ceiling_matches:
            height = float(match)
            if 3 <= height <= 20:  # 합리적인 천장 높이
                ceiling_height = height
                break

    # 버진로드 길이 검색
    road_matches = re.findall(r"버진로드\s*(\d+(?:\.\d+)?)", all_text)
    road_matches += re.findall(r"길이\s*(\d+(?:\.\d+)?)\s*[미]?", all_text)

    if road_matches:
        for match in road_matches:
            length = float(match)
            if 5 <= length <= 50:  # 합리적인 도로 길이
                virgin_road_length = length
                break

    return int(ceiling_height), int(virgin_road_length)


def parse_wedding_running_time(iw_hall: dict) -> int:
    """웨딩 진행 시간 파싱 (분 단위)"""
    hashtag = iw_hall.get("hashtag", "").lower() if iw_hall else ""

    # 해시태그에서 시간 정보 추출
    if "60분이하" in hashtag:
        return 60
    elif "70~90분" in hashtag:
        return 80  # 평균값
    elif "100~120분" in hashtag:
        return 110  # 평균값
    elif "130~180분" in hashtag:
        return 150  # 평균값
    elif "240분이상" in hashtag:
        return 240

    return 60  # 기본값


def parse_park_free_hours(hall_info: dict) -> int | None:
    """무료 주차 시간 파싱"""
    park_frtime = hall_info.get("park_frtime") or ""

    # 숫자만 추출 시도
    try:
        hours = "".join(c for c in park_frtime if c.isdigit())
        if hours:
            return int(hours)
    except:
        pass

    # 특정 패턴 확인 (예: "2시간")
    if "시간" in park_frtime:
        try:
            hours = park_frtime.split("시간")[0].strip()
            return int(hours)
        except:
            pass

    return None  # 기본값


def safe_truncate(value: str | None, max_length: int) -> str | None:
    """문자열을 안전하게 최대 길이로 자름"""
    if value and isinstance(value, str):
        return value[:max_length]
    return value


def sanitize_json(value):
    """JSON 데이터 정제"""
    if not value:
        return None

    # 이미 리스트나 딕셔너리인 경우 그대로 반환
    if isinstance(value, (list, dict)):
        return value

    if isinstance(value, str):
        try:
            # 문자열에서 작은따옴표를 큰따옴표로 변경 (JSON 표준)
            value = value.replace("'", '"')
            # 문자열이 이미 JSON 객체인 경우 파싱
            return json.loads(value)
        except json.JSONDecodeError:
            # 유효한 JSON이 아닌 경우 None 반환
            return None

    return None


def clean_wedding_hall_names(name: str):
    # 도시 이름 목록 (제거 대상)
    city_names = [
        "서울",
        "인천",
        "부산",
        "대구",
        "대전",
        "광주",
        "울산",
        "세종",
        "수원",
        "안산",
        "안양",
        "부천",
        "광명",
        "평택",
        "파주",
        "이천",
        "김해",
        "창원",
        "마산",
        "거제",
        "전주",
        "제주",
        "천안",
        "청주",
        "제천",
        "여주",
        "양평",
        "포천",
        "원주",
    ]

    dirty_patterns = {"_": " ", " ": ""}

    # 도시 이름을 위한 정규식 패턴 생성
    city_pattern = "^(" + "|".join(city_names) + ")"

    # 괄호 내용 제거
    cleaned = re.sub(r"\([^)]*\)", "", name)

    # 도시 이름 제거
    cleaned = re.sub(city_pattern, "", cleaned)

    # 더러운 패턴 제거
    for pattern in dirty_patterns:
        cleaned = cleaned.replace(pattern, dirty_patterns[pattern])

    return cleaned.strip()


def get_or_create_entity(session, model_class, **kwargs):
    """주어진 조건에 맞는 엔티티를 조회하거나 없으면 생성하여 반환"""
    instance = session.exec(select(model_class).filter_by(**kwargs)).first()
    if instance:
        return instance
    else:
        instance = model_class(**kwargs)
        session.add(instance)
        session.flush()
        return instance


def migrate_data():
    """데이터 마이그레이션 실행"""
    hall_infos, iw_halls, wb_halls, hall_venues = fetch_source_data()
    hall_mapping = create_hall_mapping(hall_infos, iw_halls, wb_halls, hall_venues)

    with Session(target_engine) as session:
        product_category_id = 1  # 결혼식장 카테고리 ID (사전에 생성 필요)

        # 기존 데이터 삭제
        session.execute(text("TRUNCATE TABLE products CASCADE"))
        session.execute(text("TRUNCATE TABLE product_images CASCADE"))
        session.execute(text("TRUNCATE TABLE product_halls CASCADE"))
        session.execute(text("TRUNCATE TABLE product_hall_styles CASCADE"))
        session.execute(text("TRUNCATE TABLE product_hall_types CASCADE"))
        session.execute(text("TRUNCATE TABLE product_hall_food_types CASCADE"))
        session.execute(text("TRUNCATE TABLE product_hall_style_links CASCADE"))
        session.execute(text("TRUNCATE TABLE product_hall_venue_type_links CASCADE"))
        session.execute(text("TRUNCATE TABLE product_hall_venues CASCADE"))
        session.execute(text("TRUNCATE TABLE product_ai_reviews CASCADE"))

        # 스타일, 타입, 음식 타입 초기화
        hall_styles = {
            "모던": get_or_create_entity(session, ProductHallStyle, name="모던"),
            "클래식": get_or_create_entity(session, ProductHallStyle, name="클래식"),
            "럭셔리": get_or_create_entity(session, ProductHallStyle, name="럭셔리"),
            "밝은": get_or_create_entity(session, ProductHallStyle, name="밝은"),
            "어두운": get_or_create_entity(session, ProductHallStyle, name="어두운"),
        }

        hall_types = {
            "채플": get_or_create_entity(session, ProductHallType, name="채플"),
            "호텔": get_or_create_entity(session, ProductHallType, name="호텔"),
            "컨벤션": get_or_create_entity(session, ProductHallType, name="컨벤션"),
            "하우스": get_or_create_entity(session, ProductHallType, name="하우스"),
            "야외": get_or_create_entity(session, ProductHallType, name="야외"),
            "한옥": get_or_create_entity(session, ProductHallType, name="한옥"),
            "소규모": get_or_create_entity(session, ProductHallType, name="소규모"),
            "기타": get_or_create_entity(session, ProductHallType, name="기타"),
        }

        food_types = {
            "뷔페": get_or_create_entity(session, ProductHallFoodType, name="뷔페"),
            "코스": get_or_create_entity(session, ProductHallFoodType, name="코스"),
            "한상": get_or_create_entity(session, ProductHallFoodType, name="한상"),
        }

        # 각 결혼식장 데이터 처리
        for banquet_code, mapping in hall_mapping.items():
            hall_info = mapping["hall_info"]
            iw_hall = mapping["iw_hall"]
            wb_hall = mapping["wb_hall"]
            venues = mapping["venues"]

            clean_name = clean_wedding_hall_names(hall_info.get("name_new", ""))

            try:
                # 기본 제품 정보 생성
                product = Product(
                    product_category_id=product_category_id,
                    name=safe_truncate(clean_name, 100),
                    description=hall_info.get("contents_text", "").strip()
                    or iw_hall.get("contents_text", "")
                    or "",
                    hashtag=safe_truncate(iw_hall.get("hashtag", "") or "", 100),
                    direct_link=safe_truncate(
                        iw_hall.get("direct_link", "") or "", 500
                    ),
                    thumbnail=safe_truncate(
                        hall_info.get("thumbnail", "")
                        or iw_hall.get("thumbnail", "")
                        or "",
                        500,
                    ),
                    logo_url=safe_truncate(hall_info.get("logo", "") or "", 500),
                    enterprise_name=safe_truncate(
                        iw_hall.get("enterprise_name", "") or "", 100
                    ),
                    enterprise_code=safe_truncate(
                        iw_hall.get("enterprise_code", "") or "", 100
                    ),
                    tel=safe_truncate(hall_info.get("rep_tel", "") or "", 30),
                    fax_tel=safe_truncate(hall_info.get("fax_tel", "") or "", 30),
                    sido=safe_truncate(hall_info.get("sido", "") or "", 30),
                    gugun=safe_truncate(hall_info.get("gugun", "") or "", 30),
                    dong=safe_truncate(hall_info.get("dong", "") or "", 30),
                    address=safe_truncate(
                        hall_info.get("addr", "")
                        or hall_info.get("new_addr", "")
                        or "",
                        100,
                    ),
                    lat=float(hall_info.get("lat", 0) or 0),
                    lng=float(hall_info.get("lng", 0) or 0),
                    subway_line=safe_truncate(
                        hall_info.get("subway_line", "") or None, 30
                    ),
                    subway_name=safe_truncate(
                        hall_info.get("subway_name", "") or None, 30
                    ),
                    subway_exit=safe_truncate(
                        hall_info.get("subway_exit", "") or None, 30
                    ),
                    park_limit=hall_info.get("park_limit"),
                    park_free_hours=parse_park_free_hours(hall_info),
                    way_text=safe_truncate(hall_info.get("way_text", "") or None, 100),
                    holiday=safe_truncate(hall_info.get("holiday", "") or None, 100),
                    business_hours="",  # 소스 데이터에 없는 필드
                    available=True,
                )

                session.add(product)
                session.flush()  # 제품 ID 생성을 위해 flush

                # 편의시설 정보 파싱
                amenities = parse_amenities(hall_info, iw_hall, wb_hall)

                # 결혼식장 상세 정보 생성
                product_hall = ProductHall(
                    product_id=product.id,
                    name=safe_truncate(clean_name, 100),
                    # 편의시설 정보
                    elevator=amenities["elevator"],
                    valet_parking=amenities["valet_parking"],
                    pyebaek_room=amenities["pyebaek_room"],
                    family_waiting_room=amenities["family_waiting_room"],
                    atm=amenities["atm"],
                    dress_room=amenities["dress_room"],
                    smoking_area=amenities["smoking_area"],
                    photo_zone=amenities["photo_zone"],
                )

                session.add(product_hall)
                session.flush()  # hall_id 생성을 위해 flush

                # 이미지 추가
                if hall_info.get("thumbnail"):
                    product_image = ProductImage(
                        product_id=product.id,
                        image_url=safe_truncate(hall_info["thumbnail"], 500),
                        order=0,
                    )
                    session.add(product_image)

                # iw_hall의 fb_thumbnail 이미지가 있다면 추가
                if iw_hall.get("fb_thumbnail"):
                    product_image = ProductImage(
                        product_id=product.id,
                        image_url=safe_truncate(iw_hall["fb_thumbnail"], 500),
                        order=1,
                    )
                    session.add(product_image)

                # sell_point가 있으면 추가 처리
                sanitized_sell_point = sanitize_json(hall_info.get("sell_point"))
                if sanitized_sell_point:
                    try:
                        # sanitized_sell_point가 이미 리스트이므로 다시 json.loads()를 호출할 필요 없음
                        sell_points = (
                            sanitized_sell_point
                            if isinstance(sanitized_sell_point, list)
                            else [sanitized_sell_point]
                        )
                        for i, point in enumerate(sell_points):
                            if isinstance(point, dict) and point.get("img"):
                                product_image = ProductImage(
                                    product_id=product.id,
                                    image_url=safe_truncate(point["img"], 500),
                                    order=i + 2,  # thumbnail과 fb_thumbnail 다음 순서
                                )
                                session.add(product_image)
                    except Exception as e:
                        print(
                            f"sell_point JSON 파싱 오류 (banquet_code: {banquet_code}): {str(e)}"
                        )

                # AI 리뷰 추가 (예시 데이터)
                review_types = ["시설", "접근성", "음식"]
                for i, review_type in enumerate(review_types):
                    review_content = f"{clean_name}의 {review_type}에 대한 AI 리뷰입니다. 이 내용은 예시입니다."
                    ai_review = ProductAIReview(
                        product_id=product.id,
                        review_type=review_type,
                        content=review_content,
                    )
                    session.add(ai_review)

                # venue 정보 추가
                if venues:
                    for venue_data in venues:
                        try:
                            venue_name = venue_data.get("name") or f"{clean_name} 홀"

                            # 웨딩 타입 정보 파싱
                            wedding_type_value = parse_wedding_type(
                                hall_info, iw_hall, wb_hall
                            )

                            # 홀 크기 정보
                            min_capacity = venue_data.get("min_person") or 0
                            max_capacity = venue_data.get("max_person") or 0

                            # 개선된 파서 사용
                            wedding_interval, wedding_times = (
                                parse_wedding_times_and_interval(venue_data, hall_info)
                            )
                            basic_price, peak_season_price = parse_hall_pricing(
                                venue_data, hall_info, iw_hall
                            )
                            ceiling_height, virgin_road_length = (
                                parse_hall_physical_attributes(
                                    venue_data, hall_info, iw_hall
                                )
                            )
                            bride_room_entry = parse_bride_room_info(
                                hall_info, iw_hall, wb_hall
                            )
                            food_type_name, food_cost = parse_food_type_and_cost(
                                hall_info, iw_hall, wb_hall, venue_data
                            )

                            venue = ProductHallVenue(
                                product_hall_id=product_hall.id,
                                name=safe_truncate(venue_name, 100),
                                wedding_interval=wedding_interval,
                                wedding_times=wedding_times,
                                wedding_type=wedding_type_value,
                                guaranteed_min_count=min_capacity,
                                min_capacity=min_capacity,
                                max_capacity=max_capacity,
                                basic_price=basic_price,
                                peak_season_price=peak_season_price,
                                ceiling_height=ceiling_height,
                                virgin_road_length=virgin_road_length,
                                include_drink=amenities["include_drink"],
                                include_alcohol=amenities["include_alcohol"],
                                include_service_fee=amenities["include_service_fee"],
                                include_vat=amenities["include_vat"],
                                bride_room_entry_methods=bride_room_entry,
                                bride_room_makeup_room=amenities[
                                    "bride_room_makeup_room"
                                ],
                                food_type_id=food_types.get(food_type_name).id,
                                food_cost_per_adult=int(food_cost),
                                food_cost_per_child=int(
                                    food_cost * 0.6
                                ),  # 성인 비용의 60%
                                banquet_hall_running_time=parse_wedding_running_time(
                                    iw_hall
                                ),
                                banquet_hall_max_capacity=max_capacity,
                                additional_info="",  # 더 많은 파싱으로 개선 가능
                                special_notes="",  # 더 많은 파싱으로 개선 가능
                            )

                            session.add(venue)
                            session.flush()  # venue_id 생성을 위해 flush

                            # venue에 스타일 연결
                            hall_style_names = parse_hall_styles(wb_hall)
                            for style_name in hall_style_names:
                                if style_name in hall_styles:
                                    style_link = ProductHallStyleLink(
                                        venue_id=venue.id,
                                        hall_style_id=hall_styles[style_name].id,
                                    )
                                    session.add(style_link)

                            # venue에 타입 연결
                            hall_type_names = parse_hall_types(
                                hall_info, iw_hall, wb_hall
                            )
                            for type_name in hall_type_names:
                                if type_name in hall_types:
                                    type_link = ProductHallVenueTypeLink(
                                        venue_id=venue.id,
                                        hall_type_id=hall_types[type_name].id,
                                    )
                                    session.add(type_link)

                        except Exception as e:
                            print(
                                f"Venue 생성 오류 (banquet_code: {banquet_code}, name: {venue_data.get('name')}): {str(e)}"
                            )
                            traceback.print_exc()
                            # venue 생성 실패해도 전체 마이그레이션은 계속 진행
                            continue

                # venue 정보가 없는 경우 기본 venue 생성 (간단한 정보로)
                if not venues:
                    try:
                        wedding_type_value = parse_wedding_type(
                            hall_info, iw_hall, wb_hall
                        )

                        min_capacity = hall_info.get("min_person") or 0
                        max_capacity = hall_info.get("max_person") or 0

                        # 개선된 파서 사용
                        # 기본 데이터로 빈 딕셔너리 전달
                        wedding_interval = parse_wedding_running_time(iw_hall)
                        wedding_times = "11:00, 13:00, 15:00, 17:00"  # 기본값
                        basic_price, peak_season_price = parse_hall_pricing(
                            {}, hall_info, iw_hall
                        )
                        ceiling_height, virgin_road_length = (
                            parse_hall_physical_attributes({}, hall_info, iw_hall)
                        )
                        bride_room_entry = parse_bride_room_info(
                            hall_info, iw_hall, wb_hall
                        )
                        food_type_name, food_cost = parse_food_type_and_cost(
                            hall_info, iw_hall, wb_hall, {}
                        )

                        venue = ProductHallVenue(
                            product_hall_id=product_hall.id,
                            name=f"{clean_name} 메인홀",
                            wedding_interval=wedding_interval,
                            wedding_times=wedding_times,
                            wedding_type=wedding_type_value,
                            guaranteed_min_count=min_capacity,
                            min_capacity=min_capacity,
                            max_capacity=max_capacity,
                            basic_price=basic_price,
                            peak_season_price=peak_season_price,
                            ceiling_height=ceiling_height,
                            virgin_road_length=virgin_road_length,
                            include_drink=amenities["include_drink"],
                            include_alcohol=amenities["include_alcohol"],
                            include_service_fee=amenities["include_service_fee"],
                            include_vat=amenities["include_vat"],
                            bride_room_entry_methods=bride_room_entry,
                            bride_room_makeup_room=amenities["bride_room_makeup_room"],
                            food_type_id=food_types.get(food_type_name).id,
                            food_cost_per_adult=int(food_cost),
                            food_cost_per_child=int(food_cost * 0.6),  # 성인 비용의 60%
                            banquet_hall_running_time=wedding_interval,
                            banquet_hall_max_capacity=max_capacity,
                            additional_info="",
                            special_notes="",
                        )

                        session.add(venue)
                        session.flush()

                        # venue에 스타일 연결
                        hall_style_names = parse_hall_styles(wb_hall)
                        for style_name in hall_style_names:
                            if style_name in hall_styles:
                                style_link = ProductHallStyleLink(
                                    venue_id=venue.id,
                                    hall_style_id=hall_styles[style_name].id,
                                )
                                session.add(style_link)

                        # venue에 타입 연결
                        hall_type_names = parse_hall_types(hall_info, iw_hall, wb_hall)
                        for type_name in hall_type_names:
                            if type_name in hall_types:
                                type_link = ProductHallVenueTypeLink(
                                    venue_id=venue.id,
                                    hall_type_id=hall_types[type_name].id,
                                )
                                session.add(type_link)

                    except Exception as e:
                        print(
                            f"기본 Venue 생성 오류 (banquet_code: {banquet_code}): {str(e)}"
                        )
                        traceback.print_exc()

                    print(
                        f"결혼식장 데이터 추가 완료: {hall_info.get('name')} (ID: {product.id})"
                    )

            except Exception as e:
                traceback.print_exc()
                print(
                    f"데이터 마이그레이션 오류 (banquet_code: {banquet_code}): {str(e)}"
                )
                session.rollback()
                continue

        session.commit()
        print("데이터 마이그레이션 완료")


if __name__ == "__main__":
    migrate_data()

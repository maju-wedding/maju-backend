import json
import re
import traceback
from typing import Any

import psycopg2
from psycopg2.extras import RealDictCursor
from sqlalchemy import text
from sqlmodel import Session, create_engine

from core.config import settings
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


def fetch_source_data() -> (
    tuple[list[tuple[Any, ...]], list[tuple[Any, ...]], list[tuple[Any, ...]]]
):
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

    cursor.close()
    conn.close()

    return hall_infos, iw_halls, wb_halls


def create_hall_mapping(
    hall_infos: list[dict], iw_halls: list[dict], wb_halls: list[dict]
) -> dict[int, dict[str, Any]]:
    """결혼식장 데이터 매핑 생성"""
    # banquet_code를 키로 사용하여 hall_info 매핑
    hall_info_mapping = {
        info["banquet_code"]: info for info in hall_infos if info["banquet_code"]
    }

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


def parse_hall_type(hall_info: dict, iw_hall: dict, wb_hall: dict | None) -> str:
    """결혼식장 유형 파싱"""
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

    # 우선순위: wb_wedding_halls > iw_wedding_hall_info > iw_wedding_halls
    if wb_hall and wb_hall.get("tag_타입"):
        wb_type = wb_hall["tag_타입"]
        # 허용된 타입과 일치하는지 확인
        for allowed_type in ALLOWED_HALL_TYPES:
            if allowed_type in wb_type:
                return allowed_type

    # 스타일과 해시태그에서 타입 추출
    styles = hall_info.get("styles") or hall_info.get("style") or ""
    hashtag = iw_hall.get("hashtag", "").lower() if iw_hall else ""

    # 허용된 타입 순서대로 확인 (순서가 중요할 수 있음)
    for allowed_type in ALLOWED_HALL_TYPES:
        if allowed_type == "기타":  # 기타는 마지막에 확인
            continue

        if allowed_type in styles or allowed_type in hashtag:
            return allowed_type

        # 영문명이나 다른 표현 확인
        if allowed_type == "호텔" and ("호텔" in styles or "호텔" in hashtag):
            return "호텔"
        elif allowed_type == "야외" and (
            "가든" in styles or "가든" in hashtag or "야외" in hashtag
        ):
            return "야외"
        elif allowed_type == "소규모" and ("스몰" in styles or "스몰" in hashtag):
            return "소규모"

    return "기타"  # 매칭되는 타입이 없으면 기타 반환


def parse_hall_style(wb_hall: dict) -> str:
    """결혼식장 스타일 파싱"""
    if not wb_hall:
        return "밝은"

    styles = wb_hall.get("tag_타입") or ""
    styles = styles.split(";") if styles else []

    # 명확한 "밝은" 스타일 확인
    if "밝은" in styles:
        return "밝은"

    # 명확한 "어두운" 스타일 확인
    if "어두운" in styles:
        return "어두운"

    # 기본값은 "밝은"으로 설정
    return "밝은"


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


def parse_food_type(hall_info: dict, iw_hall: dict, wb_hall: dict | None) -> str:
    """음식 유형 파싱"""
    if wb_hall and wb_hall.get("tag_메뉴"):
        if "뷔페" in wb_hall["tag_메뉴"]:
            return "뷔페"
        elif "코스" in wb_hall["tag_메뉴"]:
            return "코스"
        elif "한상" in wb_hall["tag_메뉴"]:
            return "한상"

    # 예시 데이터에서 확인한 형식 처리
    food_display = hall_info.get("foodDisplay", "").lower()
    if "뷔페" in food_display:
        return "뷔페"
    elif "코스" in food_display:
        return "코스"
    elif "한상" in food_display:
        return "한상"

    # iw_wedding_halls의 hashtag 필드 확인
    hashtag = iw_hall.get("hashtag", "").lower() if iw_hall else ""
    if "뷔페" in hashtag:
        return "뷔페"
    elif "코스" in hashtag:
        return "코스"
    elif "한상" in hashtag:
        return "한상"

    return "뷔페"  # 기본값


def parse_food_cost(hall_info: dict, iw_hall: dict, wb_hall: dict | None) -> int:
    """음식 비용 파싱"""
    # wb_wedding_halls의 tag_식대_최소 필드 확인
    if wb_hall and wb_hall.get("tag_식대_최소"):
        try:
            # 문자열에서 숫자만 추출 (예: "식대 82,000" -> 82000)
            cost_str = "".join(c for c in wb_hall["tag_식대_최소"] if c.isdigit())
            if cost_str:
                return int(cost_str)
        except:
            pass

    # iw_wedding_hall_info의 min_food 필드 확인
    min_food = hall_info.get("min_food")
    if min_food and isinstance(min_food, (int, float)):
        return int(min_food)

    # iw_wedding_halls의 정보 확인
    if iw_hall:
        try:
            return int(iw_hall.get("min_food", 0))
        except:
            pass

    return 0  # 기본값


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


def parse_wedding_running_time(iw_hall: dict) -> int:
    """웨딩 진행 시간 파싱 (분 단위)"""
    hashtag = iw_hall.get("hashtag", "").lower() if iw_hall else ""

    # 해시태그에서 시간 정보 추출
    if "60분이하" in hashtag:
        return 60
    elif "70~90분" in hashtag:
        return 80  # 평균값
    elif "100~120분" in hashtag or "130~180분" in hashtag:
        return 120
    elif "240분이상" in hashtag:
        return 240

    return 60  # 기본값


def parse_amenities(hall_info: dict, iw_hall: dict) -> dict[str, bool]:
    """편의시설 정보 파싱"""
    hashtag = iw_hall.get("hashtag", "").lower() if iw_hall else ""
    sell_point = hall_info.get("sell_point", "")

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
    }

    # 해시태그 및 sell_point에서 정보 추출
    if isinstance(sell_point, str):
        if "셔틀" in hashtag or "셔틀" in sell_point:
            amenities["valet_parking"] = True

        if "파우더룸" in sell_point or "드레스룸" in sell_point:
            amenities["dress_room"] = True

        # 일부 값은 확률적으로 설정 (실제 데이터에 없을 경우)
        if "엘리베이터" in sell_point:
            amenities["elevator"] = True

        if "폐백" in sell_point:
            amenities["pyebaek_room"] = True

    return amenities


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
    # List of city names to remove
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

    dirty_patterns = {"_": " ", " ": ""}

    # Create regex pattern for city names
    city_pattern = "^(" + "|".join(city_names) + ")"

    # Remove content in parentheses
    cleaned = re.sub(r"\([^)]*\)", "", name)

    # Remove city names
    cleaned = re.sub(city_pattern, "", cleaned)

    # Remove dirty patterns
    for pattern in dirty_patterns:
        cleaned = cleaned.replace(pattern, dirty_patterns[pattern])

    return cleaned.strip()


def migrate_data():
    """데이터 마이그레이션 실행"""
    hall_infos, iw_halls, wb_halls = fetch_source_data()
    hall_mapping = create_hall_mapping(hall_infos, iw_halls, wb_halls)

    with Session(target_engine) as session:
        product_category_id = 1  # 결혼식장 카테고리 ID (사전에 생성 필요)

        session.execute(text("TRUNCATE TABLE products CASCADE"))
        session.execute(text("TRUNCATE TABLE product_images CASCADE"))
        session.execute(text("TRUNCATE TABLE product_halls CASCADE"))

        # 각 결혼식장 데이터 처리
        for banquet_code, mapping in hall_mapping.items():
            hall_info = mapping["hall_info"]
            iw_hall = mapping["iw_hall"]
            wb_hall = mapping["wb_hall"]

            clean_name = clean_wedding_hall_names(hall_info.get("name_new"))

            try:
                # 기본 제품 정보 생성
                product = Product(
                    product_category_id=product_category_id,
                    name=safe_truncate(clean_name, 100),
                    description=hall_info.get("contents_text").strip()
                    or iw_hall.get("contents_text")
                    or "",
                    hashtag=safe_truncate(iw_hall.get("hashtag") or "", 100),
                    direct_link=safe_truncate(iw_hall.get("direct_link") or "", 500),
                    thumbnail=safe_truncate(
                        hall_info.get("thumbnail") or iw_hall.get("thumbnail") or "",
                        500,
                    ),
                    logo_url="",
                    enterprise_name=safe_truncate(
                        iw_hall.get("enterprise_name") or "", 100
                    ),
                    enterprise_code=safe_truncate(
                        iw_hall.get("enterprise_code") or "", 100
                    ),
                    tel=safe_truncate(hall_info.get("rep_tel") or "", 30),
                    fax_tel=safe_truncate(hall_info.get("fax_tel") or "", 30),
                    sido=safe_truncate(hall_info.get("sido") or "", 20),
                    gugun=safe_truncate(hall_info.get("gugun") or "", 20),
                    dong=safe_truncate(hall_info.get("dong") or "", 20),
                    address=safe_truncate(
                        hall_info.get("addr") or hall_info.get("new_addr") or "", 100
                    ),
                    lat=float(hall_info.get("lat") or 0),
                    lng=float(hall_info.get("lng") or 0),
                    subway_line=safe_truncate(hall_info.get("subway_line") or None, 20),
                    subway_name=safe_truncate(hall_info.get("subway_name") or None, 20),
                    subway_exit=safe_truncate(hall_info.get("subway_exit") or None, 20),
                    park_limit=hall_info.get("park_limit"),
                    park_free_hours=parse_park_free_hours(hall_info),
                    way_text=safe_truncate(hall_info.get("way_text") or None, 100),
                    holiday=safe_truncate(hall_info.get("holiday") or None, 100),
                    business_hours="",  # 소스 데이터에 없는 필드
                    available=True,
                )

                session.add(product)
                session.flush()  # 제품 ID 생성을 위해 flush

                # 결혼식장 상세 정보 생성
                min_capacity = hall_info.get("min_person") or 0
                max_capacity = hall_info.get("max_person") or 0

                # 편의시설 정보 파싱
                amenities = parse_amenities(hall_info, iw_hall)

                product_hall = ProductHall(
                    product_id=product.id,
                    name=safe_truncate(clean_name, 100),
                    hall_type=parse_hall_type(hall_info, iw_hall, wb_hall),
                    hall_style=parse_hall_style(wb_hall),
                    min_capacity=min_capacity,
                    max_capacity=max_capacity,
                    guaranteed_min_count=min_capacity,  # 최소 인원을 보증 인원으로 설정
                    wedding_type=parse_wedding_type(hall_info, iw_hall, wb_hall),
                    wedding_running_time=parse_wedding_running_time(iw_hall),
                    food_type=parse_food_type(hall_info, iw_hall, wb_hall),
                    food_cost=parse_food_cost(hall_info, iw_hall, wb_hall),
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

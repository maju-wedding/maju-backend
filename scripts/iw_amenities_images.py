from datetime import datetime

import psycopg2
import requests
from psycopg2.extras import RealDictCursor
from sqlalchemy import create_engine

from core.config import settings

PROD_PG_CONNECTION = {
    "host": settings.POSTGRES_SERVER,
    "database": settings.POSTGRES_DB,
    "user": settings.POSTGRES_USER,
    "password": settings.POSTGRES_PASSWORD,
    "port": settings.POSTGRES_PORT,
}
target_env = "prod"
target_database = (
    settings.DATABASE_URI.replace("postgresql+asyncpg", "postgresql")
    if target_env == "prod"
    else "postgresql://reborn:reborn@postgres-container.orb.local:5432/reborn"
)

reference_engine = create_engine(settings.DATABASE_URI)
target_engine = create_engine(target_database)


def connect_to_reference_postgres():
    """PostgreSQL 데이터베이스에 연결"""
    try:
        conn = psycopg2.connect(**PROD_PG_CONNECTION, cursor_factory=RealDictCursor)
        return conn
    except Exception as e:
        print(f"데이터베이스 연결 오류: {e}")
        raise


def get_image_type_from_category(category_name):
    """카테고리명을 그대로 image_type으로 사용"""
    if not category_name:
        return "기타"

    # 카테고리명을 그대로 반환 (최대 50자로 제한)
    return str(category_name)[:50]


def insert_product_image(
    cursor, product_id, image_url, image_type, title=None, order=0
):
    """이미지를 product_images 테이블에 저장"""
    try:
        # 중복 체크
        cursor.execute(
            """
            SELECT id FROM product_images 
            WHERE product_id = %s AND image_url = %s AND is_deleted = false
            """,
            (product_id, image_url),
        )

        existing = cursor.fetchone()
        if existing:
            # print(f"  ⚠️  이미지가 이미 존재합니다: {image_url}")
            return existing["id"]

        # 새 이미지 삽입
        insert_query = """
            INSERT INTO product_images 
            (product_id, image_url, image_type, "order", is_deleted, created_datetime, updated_datetime)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """

        current_time = datetime.now()

        cursor.execute(
            insert_query,
            (
                product_id,
                image_url,
                image_type,
                order,
                False,  # is_deleted
                current_time,  # created_datetime
                current_time,  # updated_datetime
            ),
        )

        result = cursor.fetchone()
        image_id = result["id"]

        print(f"  ✅ 이미지 저장 완료: ID={image_id}, Type={image_type}")
        return image_id

    except Exception as e:
        print(f"  ❌ 이미지 저장 실패: {e}")
        return None


def process_facility_images(cursor, product_id, hall_type_etc_list):
    """부대시설 이미지 처리"""
    print(f"  🏢 부대시설 이미지 처리 중...")

    BASE_URL = "https://www.iwedding.co.kr"

    for hall_type_etc in hall_type_etc_list:
        if "data" not in hall_type_etc:
            continue

        for idx, image_data in enumerate(hall_type_etc["data"]):
            category = image_data.get("category", "기타")

            # 이미지 URL 생성
            image_url = (
                BASE_URL
                + image_data.get("url", "")
                + str(image_data.get("banquet_code", ""))
                + "/"
                + image_data.get("filename", "")
            )

            # 이미지 타입은 카테고리명 그대로 사용
            image_type = get_image_type_from_category(category)

            # 이미지 저장 (부대시설은 product_venue_id 없음)
            insert_product_image(
                cursor=cursor,
                product_id=product_id,
                image_url=image_url,
                image_type=image_type,
                title=f"{category} 이미지",
                order=idx,
            )


if __name__ == "__main__":
    conn = connect_to_reference_postgres()

    try:
        cursor = conn.cursor()

        # iw_wedding_halls 데이터 가져오기
        cursor.execute("SELECT * FROM reference.iw_wedding_halls")
        iw_halls = cursor.fetchall()
        print(f"🏛️  처리할 웨딩홀 수: {len(iw_halls)}")

        API_URL = "https://com.ifamily.co.kr:6900/api/v1/detail/hall/"

        success_count = 0
        error_count = 0

        for idx, hall in enumerate(iw_halls, 1):
            enterprise_code = hall["enterprise_code"]
            print(
                f"\n[{idx}/{len(iw_halls)}] 🏛️  처리 중: enterprise_code = {enterprise_code}"
            )

            try:
                # 제품 조회
                cursor.execute(
                    "SELECT id, name FROM products WHERE enterprise_code = %s AND is_deleted = false",
                    (str(enterprise_code),),
                )

                product = cursor.fetchone()
                if not product:
                    print(f"  ❌ 제품을 찾을 수 없습니다: {enterprise_code}")
                    error_count += 1
                    continue

                product_id = product["id"]
                product_name = product["name"]
                print(f"  📍 제품 발견: {product_name} (ID: {product_id})")

                # API 호출
                try:
                    res = requests.get(API_URL + str(enterprise_code), timeout=10)
                except requests.exceptions.RequestException as e:
                    print(f"  ❌ API 호출 실패: {e}")
                    error_count += 1
                    continue

                if res.status_code != 200:
                    print(f"  ❌ API 응답 오류: {res.status_code}")
                    error_count += 1
                    continue

                try:
                    data = res.json()
                except ValueError as e:
                    print(f"  ❌ JSON 파싱 실패: {e}")
                    error_count += 1
                    continue

                # 부대시설 데이터 추출
                hall_type_etc_list = data.get("hallTypeEtcList", [])

                print(f"  📊 데이터 요약:")
                print(f"    - 부대시설: {len(hall_type_etc_list)}개")

                # 이미지 저장 시작
                images_saved = 0

                # 부대시설 이미지 처리
                if hall_type_etc_list:
                    process_facility_images(cursor, product_id, hall_type_etc_list)
                    images_saved += sum(
                        len(hte.get("data", [])) for hte in hall_type_etc_list
                    )

                # 변경사항 커밋
                conn.commit()

                print(f"  ✅ 완료: 약 {images_saved}개 이미지 처리됨")
                success_count += 1

            except Exception as e:
                print(f"  ❌ 처리 실패: {e}")
                conn.rollback()
                error_count += 1
                continue

        # 최종 결과
        print(f"\n🎉 처리 완료!")
        print(f"  ✅ 성공: {success_count}개")
        print(f"  ❌ 실패: {error_count}개")

    except Exception as e:
        print(f"❌ 전체 프로세스 오류: {e}")
        conn.rollback()

    finally:
        cursor.close()
        conn.close()
        print("🔌 데이터베이스 연결 종료")

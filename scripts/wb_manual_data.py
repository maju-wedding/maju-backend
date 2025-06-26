"""
웨딩홀 데이터 업데이트 스크립트
CSV 파일의 웨딩홀 데이터를 기존 데이터베이스에 반영합니다.
"""

import csv
import logging
import re
from typing import Dict, Optional, Tuple

from sqlalchemy import create_engine
from sqlmodel import Session, select

from core.config import settings
from models.product_hall_venues import ProductHallVenue
from models.product_halls import ProductHall
from models.products import Product

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 데이터베이스 연결
target_database = settings.DATABASE_URI.replace("postgresql+asyncpg", "postgresql")
target_engine = create_engine(target_database)


def parse_height_measurement(height_str: str) -> float:
    """높이 문자열을 미터 단위 float로 변환"""
    if not height_str or height_str.strip() == "":
        return 0.0

    # 숫자와 'm' 추출
    match = re.search(r"(\d+(?:\.\d+)?)m?", str(height_str))
    if match:
        return float(match.group(1))
    return 0.0


def parse_length_measurement(length_str: str) -> float:
    """길이 문자열을 미터 단위 float로 변환"""
    if not length_str or length_str.strip() == "":
        return 0.0

    # 숫자와 'm' 추출
    match = re.search(r"(\d+(?:\.\d+)?)m?", str(length_str))
    if match:
        return float(match.group(1))
    return 0.0


def parse_stage_info(stage_str: str) -> Tuple[bool, str]:
    """단상 정보 파싱 - (단상 존재 여부, 단상 높이)"""
    if not stage_str or stage_str.strip() == "" or stage_str == "-":
        return False, "없음"

    stage_str = stage_str.strip()
    if stage_str == "없음":
        return False, "없음"
    elif "있음" in stage_str:
        if "낮음" in stage_str:
            return True, "낮음"
        elif "높음" in stage_str:
            return True, "높음"
        else:
            return True, "있음"

    return False, "없음"


def parse_elevator_count(elevator_str: str) -> int:
    """엘리베이터 개수 파싱"""
    if not elevator_str or elevator_str.strip() == "" or elevator_str == "-":
        return 0

    try:
        return int(elevator_str)
    except (ValueError, TypeError):
        return 0


def parse_boolean_amenity(amenity_str: str) -> bool:
    """편의시설 존재 여부 파싱 (있음/없음)"""
    if not amenity_str or amenity_str.strip() == "" or amenity_str == "-":
        return False

    amenity_str = amenity_str.strip()
    return amenity_str == "있음"


def find_matching_venue(
    session: Session, hall_name: str, code: str
) -> Optional[tuple[ProductHallVenue, ProductHall]]:
    """웨딩홀 이름과 코드로 매칭되는 venue와 product_hall 찾기"""

    # 1. 코드로 직접 매칭 시도
    if code:
        # Product 테이블에서 banquet_code로 찾기
        product_stmt = select(Product).where(Product.banquet_code == int(code))
        product_result = session.exec(product_stmt).first()

        if product_result:
            # 해당 product의 product_hall 찾기
            hall_stmt = select(ProductHall).where(
                ProductHall.product_id == product_result.id
            )
            hall_result = session.exec(hall_stmt).first()

            if hall_result:
                # 첫 번째 venue 반환 (대부분의 홀은 하나의 주요 venue를 가짐)
                venue_stmt = (
                    select(ProductHallVenue)
                    .where(ProductHallVenue.product_hall_id == hall_result.id)
                    .limit(1)
                )
                venue_result = session.exec(venue_stmt).first()
                if venue_result:
                    return venue_result, hall_result

    # 2. 이름으로 매칭 시도
    if hall_name:
        # 정확한 이름 매치
        product_stmt = select(Product).where(Product.name == hall_name)
        product_result = session.exec(product_stmt).first()

        if not product_result:
            # 부분 이름 매치 시도
            product_stmt = select(Product).where(Product.name.ilike(f"%{hall_name}%"))
            product_result = session.exec(product_stmt).first()

        if product_result:
            hall_stmt = select(ProductHall).where(
                ProductHall.product_id == product_result.id
            )
            hall_result = session.exec(hall_stmt).first()

            if hall_result:
                venue_stmt = (
                    select(ProductHallVenue)
                    .where(ProductHallVenue.product_hall_id == hall_result.id)
                    .limit(1)
                )
                venue_result = session.exec(venue_stmt).first()
                if venue_result:
                    return venue_result, hall_result

    return None


def update_venue_with_csv_data(
    venue: ProductHallVenue, product_hall: ProductHall, csv_row: Dict[str, str]
) -> bool:
    """CSV 데이터로 venue와 product_hall 정보 업데이트"""
    updated = False

    # venue 필드 업데이트
    # 천고 (ceiling height) 업데이트
    ceiling_height = parse_height_measurement(csv_row.get("천고", ""))
    if ceiling_height > 0 and venue.ceiling_height != ceiling_height:
        venue.ceiling_height = ceiling_height
        updated = True
        logger.info(f"  - 천고 업데이트: {venue.ceiling_height}m -> {ceiling_height}m")

    # 버진로드 길이 업데이트
    virgin_road_length = parse_length_measurement(csv_row.get("버진로드", ""))
    if virgin_road_length > 0 and venue.virgin_road_length != virgin_road_length:
        venue.virgin_road_length = virgin_road_length
        updated = True
        logger.info(
            f"  - 버진로드 길이 업데이트: {venue.virgin_road_length}m -> {virgin_road_length}m"
        )

    # 단상 정보 업데이트
    has_stage, stage_height = parse_stage_info(csv_row.get("단상", ""))
    if venue.has_stage != has_stage:
        venue.has_stage = has_stage
        updated = True
        logger.info(f"  - 단상 존재 여부 업데이트: {venue.has_stage} -> {has_stage}")

    # product_hall 필드 업데이트
    # 엘리베이터 개수
    elevator_count = parse_elevator_count(csv_row.get("엘리베이터", ""))
    if product_hall.elevator_count != elevator_count:
        product_hall.elevator_count = elevator_count
        updated = True
        logger.info(
            f"  - 엘리베이터 개수 업데이트: {product_hall.elevator_count}개 -> {elevator_count}개"
        )

    # 발렛파킹 정보
    has_valet = parse_boolean_amenity(csv_row.get("발렛", ""))
    if product_hall.has_valet_parking != has_valet:
        product_hall.has_valet_parking = has_valet
        updated = True
        logger.info(
            f"  - 발렛파킹 정보 업데이트: {product_hall.has_valet_parking} -> {has_valet}"
        )

    # 폐백실 정보
    # has_pyebaek = parse_boolean_amenity(csv_row.get("폐백", ""))
    # if product_hall.has_pyebaek_room != has_pyebaek:
    #     product_hall.has_pyebaek_room = has_pyebaek
    #     updated = True
    #     logger.info(
    #         f"  - 폐백실 정보 업데이트: {product_hall.has_pyebaek_room} -> {has_pyebaek}"
    #     )

    # 혼주대기실 정보
    has_family_waiting_room = parse_boolean_amenity(csv_row.get("혼주대기실", ""))
    if product_hall.has_family_waiting_room != has_family_waiting_room:
        product_hall.has_family_waiting_room = has_family_waiting_room
        updated = True
        logger.info(
            f"  - 혼주대기실 정보 업데이트: {product_hall.has_family_waiting_room} -> {has_family_waiting_room}"
        )

    return updated


def process_mvp1_csv_data(csv_file_path: str = "MVP1 Wedding Hall Data.csv"):
    """CSV 파일 처리하여 데이터베이스 업데이트"""

    with Session(target_engine) as session:
        total_processed = 0
        total_updated = 0
        not_found = []

        logger.info("MVP1 웨딩홀 데이터 업데이트 시작...")

        # CSV 파일 읽기
        try:
            with open(csv_file_path, "r", encoding="utf-8") as file:
                csv_reader = csv.DictReader(file)

                for row in csv_reader:
                    total_processed += 1
                    hall_name = row.get("name", "").strip()
                    hall_code = row.get("code", "").strip()

                    logger.info(f"\n처리 중: {hall_name} (코드: {hall_code})")

                    # 매칭되는 venue와 product_hall 찾기
                    result = find_matching_venue(session, hall_name, hall_code)

                    if result:
                        venue, product_hall = result
                        # 데이터 업데이트
                        if update_venue_with_csv_data(venue, product_hall, row):
                            total_updated += 1
                            logger.info(f"  ✓ 업데이트 완료")
                        else:
                            logger.info(f"  - 변경사항 없음")
                    else:
                        not_found.append(f"{hall_name} (코드: {hall_code})")
                        logger.warning(f"  ✗ 매칭되는 venue를 찾을 수 없음")

                # 변경사항 커밋
                session.commit()
                logger.info(f"\n=== 처리 완료 ===")
                logger.info(f"총 처리된 홀: {total_processed}")
                logger.info(f"업데이트된 홀: {total_updated}")
                logger.info(f"찾을 수 없는 홀: {len(not_found)}")

                if not_found:
                    logger.info("\n찾을 수 없는 웨딩홀 목록:")
                    for hall in not_found:
                        logger.info(f"  - {hall}")

        except FileNotFoundError:
            logger.error(f"CSV 파일을 찾을 수 없습니다: {csv_file_path}")
        except Exception as e:
            logger.error(f"CSV 처리 중 오류 발생: {e}")
            session.rollback()
            raise


def validate_csv_data(csv_file_path: str = "MVP1 Wedding Hall Data.csv"):
    """CSV 데이터 유효성 검증"""

    logger.info("CSV 데이터 유효성 검증 시작...")

    try:
        with open(csv_file_path, "r", encoding="utf-8") as file:
            csv_reader = csv.DictReader(file)

            total_rows = 0
            issues = []

            for row in csv_reader:
                total_rows += 1
                hall_name = row.get("name", "").strip()
                hall_code = row.get("code", "").strip()

                # 필수 데이터 검증
                if not hall_name:
                    issues.append(f"행 {total_rows}: 웨딩홀 이름이 없음")

                if not hall_code:
                    issues.append(f"행 {total_rows}: 웨딩홀 코드가 없음")

                # 천고 데이터 검증
                ceiling_height = parse_height_measurement(row.get("천고", ""))
                if ceiling_height < 0 or ceiling_height > 50:  # 0-50m 범위
                    issues.append(
                        f"행 {total_rows} ({hall_name}): 천고 데이터 이상 - {row.get('천고', '')}"
                    )

                # 버진로드 데이터 검증
                virgin_road = parse_length_measurement(row.get("버진로드", ""))
                if virgin_road < 0 or virgin_road > 100:  # 0-100m 범위
                    issues.append(
                        f"행 {total_rows} ({hall_name}): 버진로드 길이 데이터 이상 - {row.get('버진로드', '')}"
                    )

                # 엘리베이터 개수 검증
                elevator_count = parse_elevator_count(row.get("엘리베이터", ""))
                if elevator_count < 0 or elevator_count > 20:  # 0-20개 범위
                    issues.append(
                        f"행 {total_rows} ({hall_name}): 엘리베이터 개수 데이터 이상 - {row.get('엘리베이터', '')}"
                    )

            logger.info(f"총 {total_rows}개 행 검증 완료")

            if issues:
                logger.warning(f"{len(issues)}개 이슈 발견:")
                for issue in issues[:10]:  # 처음 10개만 출력
                    logger.warning(f"  - {issue}")
                if len(issues) > 10:
                    logger.warning(f"  ... 및 {len(issues) - 10}개 추가 이슈")
            else:
                logger.info("검증 완료: 이슈 없음")

    except FileNotFoundError:
        logger.error(f"CSV 파일을 찾을 수 없습니다: {csv_file_path}")
    except Exception as e:
        logger.error(f"CSV 검증 중 오류 발생: {e}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="MVP1 웨딩홀 데이터 업데이트")
    parser.add_argument(
        "--csv-file",
        default="MVP1 Wedding Hall Data.csv",
        help="CSV 파일 경로 (기본값: MVP1 Wedding Hall Data.csv)",
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="데이터 검증만 수행하고 업데이트하지 않음",
    )

    args = parser.parse_args()

    if args.validate_only:
        validate_csv_data(args.csv_file)
    else:
        # 먼저 검증 수행
        validate_csv_data(args.csv_file)

        # 사용자 확인
        response = input("\n데이터를 업데이트하시겠습니까? (y/N): ")
        if response.lower() in ["y", "yes"]:
            process_mvp1_csv_data(args.csv_file)
        else:
            logger.info("업데이트가 취소되었습니다.")

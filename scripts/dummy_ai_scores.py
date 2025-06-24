import random

from sqlalchemy import text
from sqlmodel import Session, create_engine, select

from core.config import settings
from models.product_scores import ProductScore
from models.products import Product
from utils.utils import utc_now

# 데이터베이스 연결 설정
target_database = (
    settings.DATABASE_URI.replace("postgresql+asyncpg", "postgresql")
    if settings.ENVIRONMENT == "production"
    else "postgresql://reborn:reborn@postgres-container.orb.local:5432/reborn"
)

# 점수 타입과 범위 정의 (10점 만점)
SCORE_TYPES = {
    "overall": (7.0, 9.5),  # 전체 평점: 7.0 ~ 9.5
    "분위기": (7.0, 10.0),  # 분위기: 7.0 ~ 10.0
    "위치": (6.8, 9.2),  # 위치: 6.8 ~ 9.2
    "식사": (7.2, 9.7),  # 식사: 7.2 ~ 9.7
    "서비스": (7.1, 9.3),  # 서비스: 7.1 ~ 9.3
    "가격": (6.5, 8.9),  # 가격: 6.5 ~ 8.9
    "주차": (6.8, 9.2),  # 주차: 6.8 ~ 9.2
}


def generate_realistic_score(score_type: str) -> float:
    """점수 타입에 따라 현실적인 점수 생성"""
    min_score, max_score = SCORE_TYPES.get(score_type, (3.0, 5.0))

    # 정규분포를 사용하여 더 현실적인 점수 분포 생성
    # 대부분의 점수가 중간~높은 범위에 몰리도록 설정
    mid_point = (min_score + max_score) / 2
    std_dev = (max_score - min_score) / 6  # 99.7%가 범위 내에 들어오도록

    score = random.normalvariate(mid_point, std_dev)

    # 범위 내로 제한
    score = max(min_score, min(max_score, score))

    # 소수점 1자리로 반올림
    return round(score, 1)


def generate_correlated_scores() -> dict[str, float]:
    """상관관계를 고려한 점수 세트 생성 (10점 만점)"""
    # 기준이 되는 전체 점수 생성
    overall_score = generate_realistic_score("overall")

    scores = {}

    # 전체 점수를 기준으로 다른 점수들 생성 (상관관계 고려)
    base_adjustment = (
        overall_score - 8.0
    ) * 0.4  # 전체 점수에 따른 기본 조정 (10점 기준으로 8.0을 중간값으로 설정)

    for score_type in SCORE_TYPES:
        if score_type == "overall":
            continue

        # 기본 점수 생성
        base_score = generate_realistic_score(score_type)

        # 전체 점수와의 상관관계 적용 (40% 정도 영향)
        adjusted_score = base_score + base_adjustment

        # 범위 내로 제한
        min_score, max_score = SCORE_TYPES[score_type]
        adjusted_score = max(min_score, min(max_score, adjusted_score))

        scores[score_type] = round(adjusted_score, 1)

    return scores


def populate_ai_scores():
    """모든 웨딩홀에 AI 점수 데이터 추가"""
    engine = create_engine(target_database)

    with Session(engine) as session:
        try:
            # 카테고리 ID 1 (웨딩홀)인 모든 제품 조회
            query = select(Product).where(
                Product.product_category_id == 1, Product.is_deleted == False
            )
            result = session.execute(query)
            products = result.scalars().all()

            print(f"총 {len(products)}개의 웨딩홀을 발견했습니다.")

            # 기존 점수 데이터 삭제 (중복 방지)
            print("기존 점수 데이터를 삭제하는 중...")
            session.execute(
                text(
                    "DELETE FROM product_scores WHERE product_id IN (SELECT id FROM products WHERE product_category_id = 1)"
                )
            )

            scores_created = 0

            for product in products:
                print(f"처리 중: {product.name}")

                # 상관관계를 고려한 점수 세트 생성
                scores = generate_correlated_scores()

                # 각 점수 타입별로 ProductScore 생성
                for score_type, score_value in scores.items():
                    product_score = ProductScore(
                        product_id=product.id,
                        score_type=score_type,
                        value=score_value,
                        is_deleted=False,
                        created_datetime=utc_now(),
                        updated_datetime=utc_now(),
                    )

                    session.add(product_score)
                    scores_created += 1

                # 중간중간 커밋 (메모리 효율성)
                if scores_created % 50 == 0:
                    session.commit()
                    print(f"진행상황: {scores_created}개 점수 생성됨")

            # 최종 커밋
            session.commit()

            print(f"\n✅ 완료!")
            print(
                f"총 {len(products)}개 웨딩홀에 대해 {scores_created}개의 점수를 생성했습니다."
            )
            print(
                f"웨딩홀당 평균 {scores_created/len(products):.1f}개의 점수가 생성되었습니다."
            )

        except Exception as e:
            session.rollback()
            print(f"❌ 오류 발생: {str(e)}")
            raise
        finally:
            session.close()


if __name__ == "__main__":
    # 모든 웨딩홀에 새로운 점수 생성
    populate_ai_scores()

from sqlalchemy import and_, select, func
from sqlalchemy.ext.asyncio import AsyncSession

from models.product_scores import ProductScore
from schemes.product_halls import HallScoreComparison, HallScoreSummary, ScoreStatistics
from .base import CRUDBase


class CRUDProductScore(CRUDBase[ProductScore, dict, dict, int]):
    async def get_by_product(
        self, db: AsyncSession, *, product_id: int
    ) -> list[ProductScore]:
        """Get scores by product ID"""
        query = select(ProductScore).where(
            and_(
                ProductScore.product_id == product_id,
                ProductScore.is_deleted == False,
            )
        )
        result = await db.stream(query)
        return await result.scalars().all()

    async def get_by_product_and_type(
        self, db: AsyncSession, *, product_id: int, score_type: str
    ) -> ProductScore | None:
        """Get score by product ID and score type"""
        query = select(ProductScore).where(
            and_(
                ProductScore.product_id == product_id,
                ProductScore.score_type == score_type,
                ProductScore.is_deleted == False,
            )
        )
        result = await db.stream(query)
        return await result.scalar_one_or_none()

    async def update_or_create_score(
        self, db: AsyncSession, *, product_id: int, score_type: str, value: float
    ) -> ProductScore:
        """Update or create a score for a product"""
        score = await self.get_by_product_and_type(
            db=db, product_id=product_id, score_type=score_type
        )

        if score:
            # Update existing score
            score.value = value
            db.add(score)
            await db.commit()
            await db.refresh(score)
            return score
        else:
            # Create new score
            new_score = ProductScore(
                product_id=product_id,
                score_type=score_type,
                value=value,
            )
            db.add(new_score)
            await db.commit()
            await db.refresh(new_score)
            return new_score

    async def get_score_statistics(
        self, db: AsyncSession, *, score_type: str = None
    ) -> dict[str, ScoreStatistics]:
        """점수 통계 조회"""
        query = select(
            ProductScore.score_type,
            func.avg(ProductScore.value).label("average"),
            func.min(ProductScore.value).label("min_score"),
            func.max(ProductScore.value).label("max_score"),
            func.count(ProductScore.id).label("total_count"),
        ).where(ProductScore.is_deleted == False)

        if score_type:
            query = query.where(ProductScore.score_type == score_type)

        query = query.group_by(ProductScore.score_type)

        result = await db.execute(query)
        rows = result.fetchall()

        statistics = {}
        for row in rows:
            statistics[row.score_type] = ScoreStatistics(
                average=round(float(row.average or 0), 1),
                min_score=round(float(row.min_score or 0), 1),
                max_score=round(float(row.max_score or 0), 1),
                total_count=row.total_count,
            )

        return statistics

    async def get_hall_score_comparison(
        self, db: AsyncSession, *, product_id: int
    ) -> HallScoreSummary:
        """웨딩홀 점수와 평균 비교"""

        # 1. 해당 웨딩홀의 점수들 조회
        hall_scores_query = select(ProductScore).where(
            and_(
                ProductScore.product_id == product_id, ProductScore.is_deleted == False
            )
        )
        hall_scores_result = await db.execute(hall_scores_query)
        hall_scores = {
            score.score_type: score.value for score in hall_scores_result.scalars()
        }

        # 2. 전체 평균 통계 조회
        statistics = await self.get_score_statistics(db)

        # 3. 비교 데이터 생성
        score_comparisons = []
        total_hall_score = 0
        total_average = 0
        valid_scores = 0

        for score_type, stats in statistics.items():
            hall_score = hall_scores.get(score_type)
            # 차이 계산
            difference = (hall_score - stats.average) if hall_score is not None else 0

            score_comparisons.append(
                HallScoreComparison(
                    score_type=score_type,
                    hall_score=round(hall_score, 1) if hall_score is not None else 0,
                    average=stats.average,
                    difference=round(difference, 1),
                )
            )

            # 전체 평균 계산을 위한 누적
            if hall_score is not None:
                total_hall_score += hall_score
                valid_scores += 1
            total_average += stats.average

        # 전체 점수 계산
        overall_score = (
            round(total_hall_score / valid_scores, 1) if valid_scores > 0 else 0.0
        )
        overall_average = (
            round(total_average / len(statistics), 1) if statistics else 0.0
        )

        return HallScoreSummary(
            overall_score=overall_score,
            overall_average=overall_average,
            score_comparisons=score_comparisons,
        )

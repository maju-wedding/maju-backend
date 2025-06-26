"""데이터 보존하는 안전한 마이그레이션

Revision ID: f17f50a7df9d
Revises: 5ec15f039915
Create Date: 2025-06-26 18:05:31.126092

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f17f50a7df9d"
down_revision: Union[str, None] = "5ec15f039915"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. 새 컬럼들을 먼저 추가 (기본값과 함께)
    op.add_column(
        "product_hall_venues",
        sa.Column("has_stage", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.add_column(
        "product_halls",
        sa.Column(
            "has_valet_parking", sa.Boolean(), nullable=False, server_default="false"
        ),
    )
    op.add_column(
        "product_halls",
        sa.Column(
            "has_dress_room", sa.Boolean(), nullable=False, server_default="false"
        ),
    )
    op.add_column(
        "product_halls",
        sa.Column(
            "has_smoking_area", sa.Boolean(), nullable=False, server_default="false"
        ),
    )
    op.add_column(
        "product_halls",
        sa.Column(
            "has_photo_zone", sa.Boolean(), nullable=False, server_default="false"
        ),
    )

    # 2. 기존 데이터를 새 컬럼으로 복사
    op.execute(
        """
        UPDATE product_halls 
        SET 
            has_valet_parking = valet_parking,
            has_dress_room = dress_room,
            has_smoking_area = smoking_area,
            has_photo_zone = photo_zone
    """
    )

    # 3. 이제 안전하게 기존 컬럼들을 삭제
    op.drop_column("product_halls", "photo_zone")
    op.drop_column("product_halls", "smoking_area")
    op.drop_column("product_halls", "dress_room")
    op.drop_column("product_halls", "valet_parking")


def downgrade() -> None:
    # 다운그레이드 시에도 데이터 보존
    # 1. 기존 컬럼들을 다시 추가
    op.add_column(
        "product_halls",
        sa.Column(
            "valet_parking", sa.BOOLEAN(), nullable=False, server_default="false"
        ),
    )
    op.add_column(
        "product_halls",
        sa.Column("dress_room", sa.BOOLEAN(), nullable=False, server_default="false"),
    )
    op.add_column(
        "product_halls",
        sa.Column("smoking_area", sa.BOOLEAN(), nullable=False, server_default="false"),
    )
    op.add_column(
        "product_halls",
        sa.Column("photo_zone", sa.BOOLEAN(), nullable=False, server_default="false"),
    )

    # 2. 데이터를 다시 복사
    op.execute(
        """
        UPDATE product_halls 
        SET 
            valet_parking = has_valet_parking,
            dress_room = has_dress_room,
            smoking_area = has_smoking_area,
            photo_zone = has_photo_zone
    """
    )

    # 3. 새 컬럼들 삭제
    op.drop_column("product_halls", "has_photo_zone")
    op.drop_column("product_halls", "has_smoking_area")
    op.drop_column("product_halls", "has_dress_room")
    op.drop_column("product_halls", "has_valet_parking")
    op.drop_column("product_hall_venues", "has_stage")

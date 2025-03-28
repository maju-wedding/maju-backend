"""empty message

Revision ID: ce6d2c304cfe
Revises: 0e403e679141
Create Date: 2025-03-06 11:25:30.958265

"""

from typing import Sequence, Union

from alembic import op
import sqlmodel
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "ce6d2c304cfe"
down_revision: Union[str, None] = "0e403e679141"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column(
        "products", "subway_line", existing_type=sa.VARCHAR(length=30), nullable=True
    )
    op.alter_column(
        "products", "subway_name", existing_type=sa.VARCHAR(length=30), nullable=True
    )
    op.alter_column(
        "products", "subway_exit", existing_type=sa.VARCHAR(length=30), nullable=True
    )
    op.alter_column("products", "park_limit", existing_type=sa.INTEGER(), nullable=True)
    op.alter_column(
        "products", "park_free_hours", existing_type=sa.INTEGER(), nullable=True
    )
    op.alter_column(
        "products", "holiday", existing_type=sa.VARCHAR(length=100), nullable=True
    )
    op.alter_column(
        "products",
        "business_hours",
        existing_type=sa.VARCHAR(length=100),
        nullable=True,
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column(
        "products",
        "business_hours",
        existing_type=sa.VARCHAR(length=100),
        nullable=False,
    )
    op.alter_column(
        "products", "holiday", existing_type=sa.VARCHAR(length=100), nullable=False
    )
    op.alter_column(
        "products", "park_free_hours", existing_type=sa.INTEGER(), nullable=False
    )
    op.alter_column(
        "products", "park_limit", existing_type=sa.INTEGER(), nullable=False
    )
    op.alter_column(
        "products", "subway_exit", existing_type=sa.VARCHAR(length=30), nullable=False
    )
    op.alter_column(
        "products", "subway_name", existing_type=sa.VARCHAR(length=30), nullable=False
    )
    op.alter_column(
        "products", "subway_line", existing_type=sa.VARCHAR(length=30), nullable=False
    )
    # ### end Alembic commands ###

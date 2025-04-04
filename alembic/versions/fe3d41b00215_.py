"""empty message

Revision ID: fe3d41b00215
Revises: eeb09c16b5e5
Create Date: 2025-03-21 15:23:43.884001

"""
from typing import Sequence, Union

from alembic import op
import sqlmodel
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fe3d41b00215'
down_revision: Union[str, None] = 'eeb09c16b5e5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('product_hall_food_types',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('product_hall_styles',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('product_hall_types',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('product_ai_reviews',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('product_id', sa.Integer(), nullable=False),
    sa.Column('review_type', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('content', sa.Text(), nullable=True),
    sa.Column('is_deleted', sa.Boolean(), nullable=False),
    sa.Column('created_datetime', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_datetime', sa.DateTime(timezone=True), nullable=True),
    sa.Column('deleted_datetime', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['product_id'], ['products.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('product_images',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('product_id', sa.Integer(), nullable=False),
    sa.Column('image_url', sqlmodel.sql.sqltypes.AutoString(length=500), nullable=False),
    sa.Column('order', sa.Integer(), nullable=False),
    sa.Column('is_deleted', sa.Boolean(), nullable=False),
    sa.Column('created_datetime', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_datetime', sa.DateTime(timezone=True), nullable=True),
    sa.Column('deleted_datetime', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['product_id'], ['products.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('product_hall_venues',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('product_hall_id', sa.Integer(), nullable=False),
    sa.Column('name', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('wedding_interval', sa.Integer(), nullable=False),
    sa.Column('wedding_times', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('wedding_type', sqlmodel.sql.sqltypes.AutoString(length=10), nullable=False),
    sa.Column('guaranteed_min_count', sa.Integer(), nullable=False),
    sa.Column('min_capacity', sa.Integer(), nullable=False),
    sa.Column('max_capacity', sa.Integer(), nullable=False),
    sa.Column('basic_price', sa.Integer(), nullable=False),
    sa.Column('peak_season_price', sa.Integer(), nullable=False),
    sa.Column('ceiling_height', sa.Integer(), nullable=False),
    sa.Column('virgin_road_length', sa.Integer(), nullable=False),
    sa.Column('include_drink', sa.Boolean(), nullable=False),
    sa.Column('include_alcohol', sa.Boolean(), nullable=False),
    sa.Column('include_service_fee', sa.Boolean(), nullable=False),
    sa.Column('include_vat', sa.Boolean(), nullable=False),
    sa.Column('bride_room_entry_methods', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('bride_room_makeup_room', sa.Boolean(), nullable=False),
    sa.Column('food_type_id', sa.Integer(), nullable=False),
    sa.Column('food_cost_per_adult', sa.Integer(), nullable=False),
    sa.Column('food_cost_per_child', sa.Integer(), nullable=False),
    sa.Column('banquet_hall_running_time', sa.Integer(), nullable=False),
    sa.Column('banquet_hall_max_capacity', sa.Integer(), nullable=False),
    sa.Column('additional_info', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
    sa.Column('special_notes', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
    sa.Column('is_deleted', sa.Boolean(), nullable=False),
    sa.Column('created_datetime', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_datetime', sa.DateTime(timezone=True), nullable=True),
    sa.Column('deleted_datetime', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['food_type_id'], ['product_hall_food_types.id'], ),
    sa.ForeignKeyConstraint(['product_hall_id'], ['product_halls.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('product_hall_style_links',
    sa.Column('venue_id', sa.Integer(), nullable=False),
    sa.Column('hall_style_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['hall_style_id'], ['product_hall_styles.id'], ),
    sa.ForeignKeyConstraint(['venue_id'], ['product_hall_venues.id'], ),
    sa.PrimaryKeyConstraint('venue_id', 'hall_style_id')
    )
    op.create_table('product_hall_venue_type_links',
    sa.Column('venue_id', sa.Integer(), nullable=False),
    sa.Column('hall_type_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['hall_type_id'], ['product_hall_types.id'], ),
    sa.ForeignKeyConstraint(['venue_id'], ['product_hall_venues.id'], ),
    sa.PrimaryKeyConstraint('venue_id', 'hall_type_id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('product_hall_venue_type_links')
    op.drop_table('product_hall_style_links')
    op.drop_table('product_hall_venues')
    op.drop_table('product_images')
    op.drop_table('product_ai_reviews')
    op.drop_table('product_hall_types')
    op.drop_table('product_hall_styles')
    op.drop_table('product_hall_food_types')
    # ### end Alembic commands ###

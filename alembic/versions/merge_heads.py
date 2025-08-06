"""Merge heads

Revision ID: merge_heads
Revises: add_user_settings_fields, a7be12f9b5d4, add_social_account_id_to_posts
Create Date: 2024-01-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'merge_heads'
down_revision = ('add_user_settings_fields', 'a7be12f9b5d4', 'add_social_account_id_to_posts')
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Объединяем все head ревизии"""
    pass


def downgrade() -> None:
    """Откатываем слияние"""
    pass 
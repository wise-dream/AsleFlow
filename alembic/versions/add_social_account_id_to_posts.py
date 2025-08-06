"""Add social_account_id to posts table

Revision ID: add_social_account_id_to_posts
Revises: fix_referral_system
Create Date: 2024-01-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_social_account_id_to_posts'
down_revision = 'fix_referral_system'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Добавляем поле social_account_id в таблицу posts"""
    
    # Добавляем колонку social_account_id
    op.add_column('posts', sa.Column('social_account_id', sa.Integer(), nullable=True))
    op.create_index(op.f('ix_posts_social_account_id'), 'posts', ['social_account_id'], unique=False)
    
    # Создаем Foreign Key constraint
    op.create_foreign_key(
        'fk_posts_social_account_id_social_accounts',
        'posts', 'social_accounts',
        ['social_account_id'], ['id'],
        ondelete='CASCADE'
    )


def downgrade() -> None:
    """Откатываем изменения"""
    
    # Удаляем Foreign Key constraint
    op.drop_constraint('fk_posts_social_account_id_social_accounts', 'posts', type_='foreignkey')
    
    # Удаляем индекс
    op.drop_index(op.f('ix_posts_social_account_id'), table_name='posts')
    
    # Удаляем колонку
    op.drop_column('posts', 'social_account_id') 
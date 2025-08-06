"""Add content_length field and rename fields for clarity

Revision ID: a1b2c3d4e5f6
Revises: 01ae38a3a3d9
Create Date: 2024-01-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = 'a1b2c3d4e5f6'
down_revision = '01ae38a3a3d9'
branch_labels = None
depends_on = None


def upgrade():
    # Добавляем новое поле content_length
    op.add_column('workflow_settings', sa.Column('content_length', sa.String(20), nullable=False, server_default='medium'))
    
    # Переименовываем поля для ясности
    op.alter_column('workflow_settings', 'content_format', new_column_name='writing_style')
    op.alter_column('workflow_settings', 'content_source', new_column_name='generation_method')
    
    # Можем удалить бесполезное поле channel_type, так как оно всегда "public"
    op.drop_column('workflow_settings', 'channel_type')


def downgrade():
    # Возвращаем изменения обратно
    op.add_column('workflow_settings', sa.Column('channel_type', sa.String(50), nullable=False, server_default='public'))
    op.alter_column('workflow_settings', 'generation_method', new_column_name='content_source')
    op.alter_column('workflow_settings', 'writing_style', new_column_name='content_format')
    op.drop_column('workflow_settings', 'content_length') 
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '01ae38a3a3d9'
down_revision: Union[str, Sequence[str], None] = '89bb6b866c52'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # 1. Создаём ENUM-тип media_type до использования
    media_type_enum = sa.Enum('text', 'image', 'video', name='media_type')
    media_type_enum.create(op.get_bind(), checkfirst=True)

    # 2. Удаляем внешние ключи и столбцы, связанные с clients
    op.drop_constraint(op.f('payments_client_id_fkey'), 'payments', type_='foreignkey')
    op.drop_column('payments', 'client_id')
    op.drop_constraint(op.f('social_accounts_client_id_fkey'), 'social_accounts', type_='foreignkey')
    op.drop_column('social_accounts', 'client_id')
    op.drop_constraint(op.f('subscriptions_client_id_fkey'), 'subscriptions', type_='foreignkey')
    op.drop_column('subscriptions', 'client_id')
    op.drop_constraint(op.f('user_workflows_client_id_fkey'), 'user_workflows', type_='foreignkey')
    op.drop_column('user_workflows', 'client_id')

    # 3. Теперь можно удалить таблицу clients (индексы удалятся автоматически)
    op.drop_table('clients')

    # 4. Остальные изменения (пример для posts/media_type)
    op.add_column('posts', sa.Column('media_type', media_type_enum, nullable=True))
    op.execute("UPDATE posts SET media_type = 'image' WHERE media_type IS NULL")
    op.alter_column('posts', 'media_type', nullable=False)

    # Аналогично для workflow_settings/post_language
    op.add_column('workflow_settings', sa.Column('post_language', sa.String(length=5), nullable=True))
    op.execute("UPDATE workflow_settings SET post_language = 'ru' WHERE post_language IS NULL")
    op.alter_column('workflow_settings', 'post_language', nullable=False)

    # Остальные ваши команды (создание новых таблиц, индексов, удаление старых и т.д.)
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('telegram_id', sa.BigInteger(), nullable=True),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('password', sa.String(length=255), nullable=True),
        sa.Column('username', sa.String(length=100), nullable=True),
        sa.Column('language', sa.String(length=2), nullable=False),
        sa.Column('timezone', sa.String(length=50), nullable=False),
        sa.Column('role', sa.Enum('admin', 'client', name='user_role'), nullable=False),
        sa.Column('cash', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('referral_code', sa.String(length=20), nullable=True),
        sa.Column('referred_by', sa.String(length=20), nullable=True),
        sa.Column('free_posts_used', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('referral_code')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_telegram_id'), 'users', ['telegram_id'], unique=True)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=False)
    op.create_table('post_stats',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('post_id', sa.Integer(), nullable=True),
        sa.Column('views', sa.Integer(), nullable=True),
        sa.Column('likes', sa.Integer(), nullable=True),
        sa.Column('reposts', sa.Integer(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['post_id'], ['posts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_post_stats_id'), 'post_stats', ['id'], unique=False)
    op.create_index(op.f('ix_post_stats_post_id'), 'post_stats', ['post_id'], unique=True)
    op.add_column('payments', sa.Column('user_id', sa.Integer(), nullable=True))
    op.create_index(op.f('ix_payments_user_id'), 'payments', ['user_id'], unique=False)
    op.create_foreign_key(None, 'payments', 'users', ['user_id'], ['id'], ondelete='CASCADE')
    op.add_column('posts', sa.Column('media_url', sa.Text(), nullable=True))
    op.add_column('posts', sa.Column('is_editable', sa.Boolean(), nullable=True))
    op.add_column('posts', sa.Column('moderated', sa.Boolean(), nullable=True))
    op.add_column('posts', sa.Column('origin_topic', sa.Text(), nullable=True))
    op.drop_index(op.f('idx_posts_scheduled_time'), table_name='posts')
    op.drop_index(op.f('idx_posts_workflow_status'), table_name='posts')
    op.create_index(op.f('ix_posts_media_type'), 'posts', ['media_type'], unique=False)
    op.create_index(op.f('ix_posts_status'), 'posts', ['status'], unique=False)
    op.add_column('social_accounts', sa.Column('user_id', sa.Integer(), nullable=True))
    
    # Check if constraint exists before dropping
    inspector = inspect(op.get_bind())
    constraints = inspector.get_unique_constraints('social_accounts')
    if any(c['name'] == 'uq_client_platform_channel' for c in constraints):
        op.drop_constraint('uq_client_platform_channel', 'social_accounts', type_='unique')
    
    op.create_index(op.f('ix_social_accounts_user_id'), 'social_accounts', ['user_id'], unique=False)
    op.create_unique_constraint('uq_user_platform_channel', 'social_accounts', ['user_id', 'platform', 'channel_id'])
    op.create_foreign_key(None, 'social_accounts', 'users', ['user_id'], ['id'], ondelete='CASCADE')
    op.add_column('subscriptions', sa.Column('user_id', sa.Integer(), nullable=True))
    op.create_index(op.f('ix_subscriptions_user_id'), 'subscriptions', ['user_id'], unique=False)
    op.create_foreign_key(None, 'subscriptions', 'users', ['user_id'], ['id'], ondelete='CASCADE')
    op.add_column('user_workflows', sa.Column('user_id', sa.Integer(), nullable=True))
    op.create_index(op.f('ix_user_workflows_user_id'), 'user_workflows', ['user_id'], unique=False)
    op.create_foreign_key(None, 'user_workflows', 'users', ['user_id'], ['id'], ondelete='CASCADE')
    op.add_column('workflow_settings', sa.Column('post_media_type', media_type_enum, nullable=True))
    op.add_column('workflow_settings', sa.Column('notifications_enabled', sa.Boolean(), nullable=True))
    # ### end Alembic commands ###

def downgrade() -> None:
    # 1. Откатываем все действия в обратном порядке
    op.drop_column('workflow_settings', 'notifications_enabled')
    op.drop_column('workflow_settings', 'post_media_type')
    op.drop_column('workflow_settings', 'post_language')
    op.drop_column('user_workflows', 'user_id')
    op.drop_index(op.f('ix_user_workflows_user_id'), table_name='user_workflows')
    op.drop_constraint(None, 'user_workflows', type_='foreignkey')
    op.add_column('user_workflows', sa.Column('client_id', sa.INTEGER(), autoincrement=False, nullable=True))
    op.create_foreign_key(op.f('user_workflows_client_id_fkey'), 'user_workflows', 'clients', ['client_id'], ['id'], ondelete='CASCADE')
    op.drop_column('subscriptions', 'user_id')
    op.drop_index(op.f('ix_subscriptions_user_id'), table_name='subscriptions')
    op.drop_constraint(None, 'subscriptions', type_='foreignkey')
    op.add_column('subscriptions', sa.Column('client_id', sa.INTEGER(), autoincrement=False, nullable=True))
    op.create_foreign_key(op.f('subscriptions_client_id_fkey'), 'subscriptions', 'clients', ['client_id'], ['id'], ondelete='CASCADE')
    op.drop_column('social_accounts', 'user_id')
    op.drop_index(op.f('ix_social_accounts_user_id'), table_name='social_accounts')
    op.drop_constraint(None, 'social_accounts', type_='foreignkey')
    op.add_column('social_accounts', sa.Column('client_id', sa.INTEGER(), autoincrement=False, nullable=True))
    op.create_foreign_key(op.f('social_accounts_client_id_fkey'), 'social_accounts', 'clients', ['client_id'], ['id'], ondelete='CASCADE')
    op.drop_constraint('uq_user_platform_channel', 'social_accounts', type_='unique')
    op.create_unique_constraint(op.f('uq_client_platform_channel'), 'social_accounts', ['client_id', 'platform', 'channel_id'], postgresql_nulls_not_distinct=False)
    op.drop_column('payments', 'user_id')
    op.drop_index(op.f('ix_payments_user_id'), table_name='payments')
    op.drop_constraint(None, 'payments', type_='foreignkey')
    op.add_column('payments', sa.Column('client_id', sa.INTEGER(), autoincrement=False, nullable=True))
    op.create_foreign_key(op.f('payments_client_id_fkey'), 'payments', 'clients', ['client_id'], ['id'], ondelete='CASCADE')
    op.drop_column('posts', 'origin_topic')
    op.drop_column('posts', 'moderated')
    op.drop_column('posts', 'is_editable')
    op.drop_column('posts', 'media_url')
    op.drop_column('posts', 'media_type')
    op.drop_index(op.f('ix_posts_status'), table_name='posts')
    op.drop_index(op.f('ix_posts_media_type'), table_name='posts')
    op.create_index(op.f('idx_posts_workflow_status'), 'posts', ['user_workflow_id', 'status'], unique=False)
    op.create_index(op.f('idx_posts_scheduled_time'), 'posts', ['scheduled_time'], unique=False)
    op.drop_table('post_stats')
    op.drop_index(op.f('ix_post_stats_post_id'), table_name='post_stats')
    op.drop_index(op.f('ix_post_stats_id'), table_name='post_stats')
    op.drop_table('users')
    # 2. Восстанавливаем таблицу clients
    op.create_table('clients',
        sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
        sa.Column('telegram_id', sa.BIGINT(), autoincrement=False, nullable=True),
        sa.Column('name', sa.VARCHAR(length=100), autoincrement=False, nullable=False),
        sa.Column('email', sa.VARCHAR(length=255), autoincrement=False, nullable=True),
        sa.Column('password', sa.VARCHAR(length=255), autoincrement=False, nullable=True),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True),
        sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True),
        sa.Column('username', sa.VARCHAR(length=100), autoincrement=False, nullable=True),
        sa.Column('language', sa.VARCHAR(length=2), server_default=sa.text("'ru'::character varying"), autoincrement=False, nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('clients_pkey'))
    )
    op.create_index(op.f('ix_clients_username'), 'clients', ['username'], unique=False)
    op.create_index(op.f('ix_clients_telegram_id'), 'clients', ['telegram_id'], unique=True)
    op.create_index(op.f('ix_clients_id'), 'clients', ['id'], unique=False)
    op.create_index(op.f('ix_clients_email'), 'clients', ['email'], unique=True)
    # ### end Alembic commands ###
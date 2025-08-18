from sqlalchemy import (
    Column, Integer, String, DateTime, ForeignKey, Text, Enum,
    Index, UniqueConstraint, BigInteger, Boolean, Numeric
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime, timezone

Base = declarative_base()

# --------------------
# Enums
# --------------------
PaymentStatus = Enum('pending', 'completed', 'failed', name='payment_status')
WorkflowStatus = Enum('active', 'inactive', name='workflow_status')
PostStatus = Enum('pending', 'scheduled', 'publishing', 'published', 'failed', name='post_status')
TopicStatus = Enum('pending', 'used', name='topic_status')
MediaType = Enum('text', 'image', 'video', name='media_type')
UserRole = Enum('admin', 'client', name='user_role')
WorkflowMode = Enum('auto', 'manual', 'mixed', name='workflow_mode')


# --------------------
# Пользователь
# --------------------
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(BigInteger, unique=True, nullable=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=True, index=True)
    password = Column(String(255), nullable=True)
    username = Column(String(100), nullable=True, index=True)
    role = Column(UserRole, nullable=False, default='client')
    cash = Column(Numeric(10, 2), default=0)
    referral_code = Column(String(20), unique=True, nullable=True)
    referred_by_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True)

    # Бесплатные посты (для проб/тестов)
    free_posts_used = Column(Integer, default=0)
    free_posts_limit = Column(Integer, default=5)

    # Безопасность / интерфейс
    two_factor_enabled = Column(Boolean, default=False)
    last_login = Column(DateTime(timezone=True), nullable=True)
    login_count = Column(Integer, default=0)
    theme = Column(String(20), default='light')
    compact_mode = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    subscriptions = relationship('Subscription', back_populates='user')
    social_accounts = relationship('SocialAccount', back_populates='user')
    user_workflows = relationship('UserWorkflow', back_populates='user')

    # Реферальная система
    referred_by = relationship('User', remote_side=[id], backref='referrals')


# --------------------
# Тарифные планы
# --------------------
class Plan(Base):
    __tablename__ = 'plans'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    channels_limit = Column(Integer, nullable=False)
    posts_limit = Column(Integer, nullable=False)
    manual_posts_limit = Column(Integer, nullable=False)
    ai_priority = Column(Boolean, default=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)

    subscriptions = relationship('Subscription', back_populates='plan')


# --------------------
# Подписки
# --------------------
class Subscription(Base):
    __tablename__ = 'subscriptions'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), index=True)
    plan_id = Column(Integer, ForeignKey('plans.id', ondelete='CASCADE'), nullable=False)
    start_date = Column(DateTime(timezone=True), nullable=False, index=True)
    end_date = Column(DateTime(timezone=True), nullable=False, index=True)
    status = Column(String(50), default='active')
    auto_renew = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    user = relationship('User', back_populates='subscriptions')
    plan = relationship('Plan', back_populates='subscriptions')
    payments = relationship('Payment', back_populates='subscription')
    usage = relationship('UsageStats', back_populates='subscription', uselist=False)

    __table_args__ = (
        Index('idx_subscription_active_window', 'status', 'start_date', 'end_date'),
    )


# --------------------
# Учёт использования
# --------------------
class UsageStats(Base):
    __tablename__ = 'usage_stats'
    id = Column(Integer, primary_key=True, index=True)
    subscription_id = Column(Integer, ForeignKey('subscriptions.id', ondelete='CASCADE'), index=True, unique=True)
    posts_used = Column(Integer, default=0)
    manual_posts_used = Column(Integer, default=0)
    channels_connected = Column(Integer, default=0)

    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    subscription = relationship('Subscription', back_populates='usage')


# --------------------
# Оплаты
# --------------------
class Payment(Base):
    __tablename__ = 'payments'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), index=True)
    subscription_id = Column(Integer, ForeignKey('subscriptions.id', ondelete='CASCADE'), index=True)
    amount = Column(Numeric(10, 2), nullable=False)
    status = Column(PaymentStatus, default='pending')
    payment_date = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)

    # Опциональные поля провайдера (расширяемость)
    provider = Column(String(50), nullable=True)
    currency = Column(String(10), nullable=True, default='RUB')
    external_id = Column(String(100), nullable=True, index=True)  # invoice/intent id
    payload = Column(JSONB, nullable=True)  # сырые данные вебхука/квитанции

    subscription = relationship('Subscription', back_populates='payments')


# --------------------
# Соцсети (аккаунт/канал)
# --------------------
class SocialAccount(Base):
    __tablename__ = 'social_accounts'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), index=True)
    platform = Column(String(50), nullable=False, index=True)
    channel_name = Column(String(100), nullable=False, index=True)
    channel_id = Column(String(100), nullable=False, index=True)
    channel_type = Column(String(20), nullable=False, default='public')

    # Авторизация/валидность
    access_token = Column(String(255), nullable=True)
    refresh_token = Column(String(255), nullable=True)
    token_expires_at = Column(DateTime(timezone=True), nullable=True, index=True)
    scopes = Column(JSONB, nullable=True)
    is_valid = Column(Boolean, default=True, index=True)

    # Перс. контекст канала/настройки форматирования
    channel_context = Column(JSONB, nullable=True)  # любые специфичные данные канала (ограничения/тон/метки)

    telegram_chat_id = Column(String(100), nullable=True, index=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    user = relationship('User', back_populates='social_accounts')

    __table_args__ = (
        UniqueConstraint('user_id', 'platform', 'channel_id', name='uq_user_platform_channel'),
        Index('idx_platform_chat', 'platform', 'telegram_chat_id'),
        Index('idx_social_validity', 'platform', 'is_valid'),
    )


# --------------------
# Задачи (воркфлоу)
# --------------------
class UserWorkflow(Base):
    __tablename__ = 'user_workflows'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), index=True)
    workflow_id = Column(String(50), nullable=False, index=True)  # тип/ид шаблона процесса
    name = Column(String(100), nullable=False)
    status = Column(WorkflowStatus, default='inactive')

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user = relationship('User', back_populates='user_workflows')
    settings = relationship('WorkflowSettings', back_populates='user_workflow', uselist=False)
    posts = relationship('Post', back_populates='workflow')

    __table_args__ = (
        Index('idx_user_workflows_user_status', 'user_id', 'status'),
    )


class WorkflowSettings(Base):
    __tablename__ = 'workflow_settings'
    id = Column(Integer, primary_key=True, index=True)
    user_workflow_id = Column(Integer, ForeignKey('user_workflows.id', ondelete='CASCADE'), unique=True, index=True)
    social_account_id = Column(Integer, ForeignKey('social_accounts.id', ondelete='CASCADE'), index=True)

    # Расписание
    interval_hours = Column(Integer, nullable=False, default=6, index=True)
    first_post_time = Column(String(5), nullable=False)  # 'HH:MM' — храним просто как текст без TZ

    # Базовый «профиль» генерации
    theme = Column(String(100), nullable=False)
    context = Column(Text, nullable=True)
    writing_style = Column(String(50), nullable=False)
    generation_method = Column(String(50), nullable=False)
    content_length = Column(String(20), nullable=False, default='medium')
    post_language = Column(String(5), nullable=False, default='en')
    post_media_type = Column(MediaType, nullable=True)

    # Модерация (булево вместо строкового флага)
    moderation = Column(Boolean, nullable=False, default=False)

    # Режим работы
    mode = Column(WorkflowMode, default='auto')

    # Память/профиль/правила для устранения «вразнобой»
    content_profile = Column(JSONB, nullable=True)     # стабильное ДНК задачи (аудитория/тон/хештеги/ограничения)
    content_memory = Column(JSONB, nullable=True)      # изменяемое состояние (серии, счётчики, недавние темы)
    publishing_rules = Column(JSONB, nullable=True)    # слоты/рубрики по дням недели и т.п.

    # Шаблон промпта по умолчанию
    prompt_template_id = Column(Integer, ForeignKey('prompt_templates.id', ondelete='SET NULL'), nullable=True, index=True)

    # Служебное
    notifications_enabled = Column(Boolean, default=True)
    last_execution = Column(DateTime(timezone=True), nullable=True, index=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    user_workflow = relationship('UserWorkflow', back_populates='settings')
    social_account = relationship('SocialAccount')
    prompt_template = relationship('PromptTemplate')

    __table_args__ = (
        Index('idx_workflow_settings_social', 'social_account_id'),
        Index('idx_workflow_settings_last_exec', 'last_execution'),
    )

# --------------------
# Шаблоны промптов
# --------------------
class PromptTemplate(Base):
    __tablename__ = 'prompt_templates'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)
    template_text = Column(Text, nullable=False)  # Шаблон промпта с плейсхолдерами
    is_system = Column(Boolean, default=False)    # Системный шаблон (нельзя удалить)
    is_active = Column(Boolean, default=True)

    # Настройки генерации
    default_temperature = Column(Numeric(3, 2), nullable=True, default=0.7)
    max_tokens = Column(Integer, nullable=True)
    variables = Column(JSONB, nullable=True)      # Список/схема переменных для валидации

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))



# --------------------
# Темы (очередь тем)
# --------------------
class Topic(Base):
    __tablename__ = 'topics'
    id = Column(Integer, primary_key=True, index=True)
    user_workflow_id = Column(Integer, ForeignKey('user_workflows.id', ondelete='CASCADE'), index=True)
    title = Column(Text, nullable=False)
    status = Column(TopicStatus, nullable=False, default='pending', index=True)
    source = Column(String(20), nullable=False, default='ai')  # 'ai' | 'user'
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    used_at = Column(DateTime(timezone=True), nullable=True)

    user_workflow = relationship('UserWorkflow')

    __table_args__ = (
        Index('idx_topics_workflow_status', 'user_workflow_id', 'status'),
    )


# --------------------
# Посты
# --------------------
class Post(Base):
    __tablename__ = 'posts'
    id = Column(Integer, primary_key=True, index=True)
    user_workflow_id = Column(Integer, ForeignKey('user_workflows.id', ondelete='CASCADE'), index=True)
    social_account_id = Column(Integer, ForeignKey('social_accounts.id', ondelete='CASCADE'), index=True)

    topic = Column(Text, nullable=False)
    content = Column(Text, nullable=False)
    media_type = Column(MediaType, nullable=False, index=True, default='image')
    media_url = Column(Text, nullable=True)

    # Публикация/статусы
    status = Column(PostStatus, default='pending', index=True)
    scheduled_time = Column(DateTime(timezone=True), nullable=False, index=True)
    published_time = Column(DateTime(timezone=True), nullable=True, index=True)

    # Внешние идентификаторы/ссылки
    external_id = Column(String(100), nullable=True)
    permalink = Column(Text, nullable=True)

    # Ретраи/ошибки
    retry_count = Column(Integer, default=0)
    last_error = Column(Text, nullable=True)

    # Редактирование/модерация
    is_editable = Column(Boolean, default=True)
    moderated = Column(Boolean, default=False)

    # Ручные посты/промпт
    user_prompt = Column(Text, nullable=True)
    user_notes = Column(Text, nullable=True)
    is_manual = Column(Boolean, default=False, index=True)
    prompt_template_id = Column(Integer, ForeignKey('prompt_templates.id', ondelete='SET NULL'), nullable=True, index=True)
    generation_temperature = Column(Numeric(3, 2), nullable=True)
    manual_topic = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    workflow = relationship('UserWorkflow', back_populates='posts')
    social_account = relationship('SocialAccount')
    prompt_template = relationship('PromptTemplate')

    __table_args__ = (
        Index('idx_posts_status_due', 'status', 'scheduled_time'),
        Index('idx_posts_account_published', 'social_account_id', 'published_time'),
        UniqueConstraint('social_account_id', 'external_id', name='uq_post_external_per_account'),
    )


# --------------------
# Статистика постов
# --------------------
class PostStats(Base):
    __tablename__ = 'post_stats'
    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey('posts.id', ondelete='CASCADE'), unique=True, index=True)
    views = Column(Integer, default=0)
    likes = Column(Integer, default=0)
    reposts = Column(Integer, default=0)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    post = relationship('Post')


# --------------------
# Логи публикаций (идемпотентность/диагностика)
# --------------------
class PublicationLog(Base):
    __tablename__ = 'publication_logs'
    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey('posts.id', ondelete='CASCADE'), index=True)
    attempt = Column(Integer, nullable=False, default=1)
    started_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    finished_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(20), nullable=False, default='started')  # started|success|failed
    error_code = Column(String(50), nullable=True)
    error_message = Column(Text, nullable=True)
    request_hash = Column(String(64), nullable=True, index=True)
    response_snippet = Column(Text, nullable=True)

    post = relationship('Post')

    __table_args__ = (
        Index('idx_publogs_post_attempt', 'post_id', 'attempt'),
    )

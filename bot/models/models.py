from sqlalchemy import (
    Column, Integer, String, DateTime, ForeignKey, Text, Enum,
    Index, UniqueConstraint, BigInteger, Boolean, Numeric
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

Base = declarative_base()

# Enums
PaymentStatus = Enum('pending', 'completed', 'failed', name='payment_status')
WorkflowStatus = Enum('active', 'inactive', name='workflow_status')
PostStatus = Enum('pending', 'scheduled', 'published', 'failed', name='post_status')
TopicStatus = Enum('pending', 'used', name='topic_status')
MediaType = Enum('text', 'image', 'video', name='media_type')
UserRole = Enum('admin', 'client', name='user_role')


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
    language = Column(String(2), nullable=False, default='ru')
    timezone = Column(String(50), nullable=False, default='UTC')
    role = Column(UserRole, nullable=False, default='client')
    cash = Column(Numeric(10, 2), default=0)
    referral_code = Column(String(20), unique=True, nullable=True)
    referred_by_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True)
    free_posts_used = Column(Integer, default=0)
    free_posts_limit = Column(Integer, default=5)  # Индивидуальный лимит бесплатных постов

    # Настройки уведомлений
    notify_new_posts = Column(Boolean, default=True)
    notify_scheduled = Column(Boolean, default=True)
    notify_errors = Column(Boolean, default=True)
    notify_payments = Column(Boolean, default=True)

    # Настройки контента
    default_language = Column(String(2), default='ru')
    default_style = Column(String(20), default='friendly')
    default_length = Column(String(20), default='medium')
    default_moderation = Column(Boolean, default=False)

    # Безопасность
    two_factor_enabled = Column(Boolean, default=False)
    last_login = Column(DateTime(timezone=True), nullable=True)
    login_count = Column(Integer, default=0)

    # Интерфейс
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

    subscription = relationship('Subscription', back_populates='payments')


# --------------------
# Соцсети
# --------------------
class SocialAccount(Base):
    __tablename__ = 'social_accounts'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), index=True)
    platform = Column(String(50), nullable=False, index=True)
    channel_name = Column(String(100), nullable=False, index=True)
    channel_id = Column(String(100), nullable=False, index=True)
    channel_type = Column(String(20), nullable=False, default='public')
    access_token = Column(String(255), nullable=True)
    telegram_chat_id = Column(String(100), nullable=True, index=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    user = relationship('User', back_populates='social_accounts')

    __table_args__ = (
        UniqueConstraint('user_id', 'platform', 'channel_id', name='uq_user_platform_channel'),
        Index('idx_platform_chat', 'platform', 'telegram_chat_id'),
    )


# --------------------
# Задачи (воркфлоу)
# --------------------
class UserWorkflow(Base):
    __tablename__ = 'user_workflows'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), index=True)
    workflow_id = Column(String(50), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    status = Column(WorkflowStatus, default='inactive')
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user = relationship('User', back_populates='user_workflows')
    settings = relationship('WorkflowSettings', back_populates='user_workflow', uselist=False)
    posts = relationship('Post', back_populates='workflow')


class WorkflowSettings(Base):
    __tablename__ = 'workflow_settings'
    id = Column(Integer, primary_key=True, index=True)
    user_workflow_id = Column(Integer, ForeignKey('user_workflows.id', ondelete='CASCADE'), unique=True, index=True)
    social_account_id = Column(Integer, ForeignKey('social_accounts.id', ondelete='CASCADE'), index=True)

    interval_hours = Column(Integer, nullable=False, default=6, index=True)
    theme = Column(String(100), nullable=False)
    context = Column(Text, nullable=True)
    writing_style = Column(String(50), nullable=False)
    generation_method = Column(String(50), nullable=False)
    content_length = Column(String(20), nullable=False, default='medium')
    moderation = Column(String(50), nullable=False, default='disabled')
    first_post_time = Column(String(5), nullable=False)
    post_language = Column(String(5), nullable=False, default='ru')
    post_media_type = Column(MediaType, nullable=True)
    notifications_enabled = Column(Boolean, default=True)
    last_execution = Column(DateTime(timezone=True), nullable=True, index=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    user_workflow = relationship('UserWorkflow', back_populates='settings')
    social_account = relationship('SocialAccount')


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
    status = Column(PostStatus, default='pending', index=True)
    scheduled_time = Column(DateTime(timezone=True), nullable=False, index=True)
    published_time = Column(DateTime(timezone=True), nullable=True, index=True)
    is_editable = Column(Boolean, default=True)
    moderated = Column(Boolean, default=False)
    origin_topic = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    workflow = relationship('UserWorkflow', back_populates='posts')
    social_account = relationship('SocialAccount')


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

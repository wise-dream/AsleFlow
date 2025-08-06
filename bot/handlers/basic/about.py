from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram import F
from aiogram import Router
from sqlalchemy import select, func
from datetime import datetime, timezone

from bot.models.models import Post, UserWorkflow, SocialAccount, Subscription
from bot.keyboards.inline.settings import get_settings_keyboard, get_simple_settings_keyboard

router = Router()


async def about_handler(message: Message, session, i18n, user, **_):
    """Отображает упрощенную информацию о профиле пользователя"""
    
    # Получаем статистику пользователя
    # Подсчет постов
    posts_result = await session.execute(
        select(func.count(Post.id)).where(Post.workflow.has(user_id=user.id))
    )
    total_posts = posts_result.scalar() or 0
    
    # Подсчет опубликованных постов
    published_posts_result = await session.execute(
        select(func.count(Post.id)).where(
            Post.workflow.has(user_id=user.id),
            Post.status == 'published'
        )
    )
    published_posts = published_posts_result.scalar() or 0
    
    # Подсчет workflow'ов
    workflows_result = await session.execute(
        select(func.count(UserWorkflow.id)).where(UserWorkflow.user_id == user.id)
    )
    total_workflows = workflows_result.scalar() or 0
    
    # Подсчет активных workflow'ов
    active_workflows_result = await session.execute(
        select(func.count(UserWorkflow.id)).where(
            UserWorkflow.user_id == user.id,
            UserWorkflow.status == 'active'
        )
    )
    active_workflows = active_workflows_result.scalar() or 0
    
    # Подсчет аккаунтов
    accounts_result = await session.execute(
        select(func.count(SocialAccount.id)).where(SocialAccount.user_id == user.id)
    )
    total_accounts = accounts_result.scalar() or 0
    
    # Получаем активную подписку
    subscription_result = await session.execute(
        select(Subscription).where(
            Subscription.user_id == user.id,
            Subscription.status == 'active',
            Subscription.end_date > datetime.now(timezone.utc)
        ).order_by(Subscription.end_date.desc())
    )
    active_subscription = subscription_result.scalar_one_or_none()
    
    # Формируем упрощенный текст профиля
    user_name = user.name or i18n.get("about.unknown")
    
    profile_text = i18n.get("about.profile_title").format(name=user_name) + "\n\n"
    
    # Подписка
    if active_subscription:
        subscription_end = active_subscription.end_date.strftime("%d.%m.%Y")
        plan_name = active_subscription.plan.name if active_subscription.plan else "Unknown"
        subscription_info = f"{plan_name} (до {subscription_end})"
    else:
        subscription_info = "Free"
    
    profile_text += i18n.get("about.subscription").format(subscription=subscription_info) + "\n"
    
    # Баланс
    cash = user.cash or 0
    balance = f"{cash}₽"
    profile_text += i18n.get("about.balance").format(balance=balance) + "\n"
    
    # Реферальный код - ВСЕГДА должен быть!
    if user.referral_code:
        profile_text += i18n.get("about.referral_code").format(code=f"<code>{user.referral_code}</code>") + "\n"
    else:
        # КРИТИЧЕСКАЯ ОШИБКА - у пользователя нет реферального кода!
        profile_text += i18n.get("about.referral_code_error") + "\n"
        print(f"КРИТИЧЕСКАЯ ОШИБКА: У пользователя {user.id} (Telegram ID: {user.telegram_id}) нет реферального кода!")
    
    # Информация о реферере
    if user.referred_by:
        referrer_name = user.referred_by.name
    else:
        referrer_name = i18n.get("about.no_referrer")
    
    profile_text += i18n.get("about.invited_by").format(referrer=referrer_name) + "\n"
    
    # Статистика
    free_posts_used = user.free_posts_used or 0
    free_posts_limit = user.free_posts_limit or 5
    free_posts_remaining = free_posts_limit - free_posts_used
    
    profile_text += "\n" + i18n.get("about.statistics").format(
        total_posts=total_posts,
        published_posts=published_posts,
        total_workflows=total_workflows,
        active_workflows=active_workflows,
        total_accounts=total_accounts,
        free_posts_remaining=free_posts_remaining
    ) + "\n"
    
    await message.answer(
        profile_text,
        reply_markup=get_simple_settings_keyboard(i18n),
        parse_mode="HTML"
    )


async def about_back_handler(callback: CallbackQuery, session, i18n, user, **_):
    """Обработчик кнопки "Назад" в профиле"""
    await callback.answer()
    await about_handler(callback.message, session, i18n, user)


def register_about_handler(router: Router):
    router.message.register(about_handler, Command("about"))
    router.message.register(about_handler, F.text.lower().contains("profile"))
    router.message.register(about_handler, F.text.lower().contains("профиль"))
    router.callback_query.register(about_back_handler, lambda c: c.data == "about:back")


__all__ = ["register_about_handler"]

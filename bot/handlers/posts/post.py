from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram import F, Router
from sqlalchemy.future import select

from bot.keyboards.inline.posts import get_posts_keyboard, get_post_actions_keyboard, get_post_filter_keyboard
from bot.services.crud.post import (
    get_post_by_id, 
    get_posts_by_status, 
    delete_post as crud_delete_post,
    update_post as crud_update_post
)
from bot.services.publishing import PublishingService
from bot.models.models import Post, UserWorkflow

router = Router()


async def get_posts_by_user_id(session, user_id: int, status_filter: str = None) -> list[Post]:
    """Получение постов пользователя с опциональной фильтрацией по статусу"""
    query = select(Post).join(UserWorkflow).where(UserWorkflow.user_id == user_id)
    
    if status_filter and status_filter != "all":
        query = query.where(Post.status == status_filter)
    
    query = query.order_by(Post.created_at.desc())
    result = await session.execute(query)
    return result.scalars().all()


def format_posts_stats_text(stats, i18n):
    text = []
    if stats.get('pending'):
        text.append(i18n.get("post.stats.pending", "⏳ Ожидание: {count}").format(count=stats['pending']))
    if stats.get('scheduled'):
        text.append(i18n.get("post.stats.scheduled", "📅 Запланированы: {count}").format(count=stats['scheduled']))
    if stats.get('published'):
        text.append(i18n.get("post.stats.published", "✅ Опубликованы: {count}").format(count=stats['published']))
    if stats.get('failed'):
        text.append(i18n.get("post.stats.failed", "❌ Неудачные: {count}").format(count=stats['failed']))
    return "\n".join(text)


async def posts_handler(message: Message, session, i18n, user, **_):
    """Главный обработчик постов"""
    posts = await get_posts_by_user_id(session, user.id)

    if not posts:
        await message.answer(
            i18n.get("posts.none", "📝 У вас пока нет постов."),
            reply_markup=get_posts_keyboard(i18n, [])
        )
        return

    text = format_posts_stats_text(posts, i18n)

    await message.answer(
        text,
        reply_markup=get_posts_keyboard(i18n, posts[:10]),  # Показываем первые 10
        parse_mode="HTML"
    )


async def posts_back_handler(callback: CallbackQuery, session, i18n, user, **_):
    """Возврат к списку постов"""
    await callback.answer()
    posts = await get_posts_by_user_id(session, user.id)

    if not posts:
        await callback.message.edit_text(
            i18n.get("posts.none", "📝 У вас пока нет постов."),
            reply_markup=get_posts_keyboard(i18n, [])
        )
        return

    text = format_posts_stats_text(posts, i18n)

    await callback.message.edit_text(
        text,
        reply_markup=get_posts_keyboard(i18n, posts[:10]),
        parse_mode="HTML"
    )


async def view_post_handler(callback: CallbackQuery, session, user, i18n, **_):
    """Просмотр отдельного поста"""
    await callback.answer()
    post_id = int(callback.data.split(":")[-1])
    
    post = await get_post_by_id(session, post_id)
    if not post:
        await callback.message.answer(i18n.get("post.not_found", "❌ Пост не найден."))
        return

    # Проверяем принадлежность поста пользователю
    workflow_result = await session.execute(
        select(UserWorkflow).where(UserWorkflow.id == post.user_workflow_id)
    )
    workflow = workflow_result.scalar_one_or_none()
    
    if not workflow or workflow.user_id != user.id:
        await callback.message.answer(i18n.get("post.access_denied", "❌ Доступ запрещен."))
        return

    # Форматируем статус
    status_text = i18n.get(f"post.status.{post.status}", post.status)
    status_text = status_text.upper()

    # Форматируем время
    from datetime import datetime
    scheduled_time = post.scheduled_time.strftime("%d.%m.%Y %H:%M") if post.scheduled_time else i18n.get("post.time.not_set", "Не указано")
    published_time = post.published_time.strftime("%d.%m.%Y %H:%M") if post.published_time else i18n.get("post.time.not_published", "—")

    # Форматируем модерацию
    moderation_text = i18n.get("post.moderation.yes", "✅ Да") if post.moderated else i18n.get("post.moderation.no", "❌ Нет")

    # Язык
    lang_code = (user.language or 'ru').upper()
    flag = {
        "RU": "🇷🇺",
        "EN": "🇬🇧",
        "UA": "🇺🇦",
        "ES": "🇪🇸",
        "DE": "🇩🇪",
        "FR": "🇫🇷"
    }.get(lang_code, "🏳️")
    lang_text = f"{flag} {lang_code}"

    text = (
        f"📝 <b>{post.topic}</b>\n\n"
        f"<b>{i18n.get('post.field.status', '📊 Статус')}:</b> {status_text}\n"
        f"<b>{i18n.get('post.field.scheduled_time', '📅 Запланировано')}:</b> {scheduled_time}\n"
        f"<b>{i18n.get('post.field.published_time', '✅ Опубликовано')}:</b> {published_time}\n"
        f"<b>{i18n.get('post.field.moderation', '🔧 Модерация')}:</b> {moderation_text}\n\n"
        f"<b>{i18n.get('post.field.content', '📄 Контент')}:</b>\n{post.content[:500]}"
        f"<b>{i18n.get('workflow.field.language', '🌐 Язык')}:</b> {lang_text}\n"
    )
    
    if len(post.content) > 500:
        text += "..."

    await callback.message.edit_text(
        text,
        reply_markup=get_post_actions_keyboard(post.id, i18n, post.status),
        parse_mode="HTML"
    )


async def delete_post_handler(callback: CallbackQuery, session, i18n, user, **_):
    """Удаление поста"""
    await callback.answer()
    post_id = int(callback.data.split(":")[-1])
    
    post = await get_post_by_id(session, post_id)
    if not post:
        await callback.message.answer(i18n.get("post.not_found", "❌ Пост не найден."))
        return

    # Проверяем принадлежность поста пользователю
    workflow_result = await session.execute(
        select(UserWorkflow).where(UserWorkflow.id == post.user_workflow_id)
    )
    workflow = workflow_result.scalar_one_or_none()
    
    if not workflow or workflow.user_id != user.id:
        await callback.message.answer(i18n.get("post.access_denied", "❌ Доступ запрещен."))
        return

    # Удаляем пост
    success = await crud_delete_post(session, post_id)
    if success:
        await callback.message.edit_text(i18n.get("post.deleted", "✅ Пост удален."))
    else:
        await callback.message.answer(i18n.get("post.delete_error", "❌ Ошибка удаления поста."))


async def publish_post_handler(callback: CallbackQuery, session, i18n, user, **_):
    """Публикация поста"""
    await callback.answer()
    post_id = int(callback.data.split(":")[-1])
    
    post = await get_post_by_id(session, post_id)
    if not post:
        await callback.message.answer(i18n.get("post.not_found", "❌ Пост не найден."))
        return

    # Проверяем принадлежность поста пользователю
    workflow_result = await session.execute(
        select(UserWorkflow).where(UserWorkflow.id == post.user_workflow_id)
    )
    workflow = workflow_result.scalar_one_or_none()
    
    if not workflow or workflow.user_id != user.id:
        await callback.message.answer(i18n.get("post.access_denied", "❌ Доступ запрещен."))
        return

    # Используем сервис публикации
    publishing_service = PublishingService(callback.bot)
    
    # Планируем пост к публикации
    scheduled = await publishing_service.schedule_post_for_publishing(session, post_id)
    
    if scheduled:
        # Сразу пытаемся опубликовать
        published = await publishing_service.publish_post(session, post_id)
        
        if published:
            await callback.message.edit_text(
                i18n.get("post.published_successfully", "✅ Пост успешно опубликован!"),
                reply_markup=get_post_actions_keyboard(post_id, i18n, "published")
            )
        else:
            await callback.message.edit_text(
                i18n.get("post.scheduled", "✅ Пост запланирован к публикации."),
                reply_markup=get_post_actions_keyboard(post_id, i18n, "scheduled")
            )
    else:
        await callback.message.answer(i18n.get("post.publish_error", "❌ Ошибка планирования поста."))


async def edit_post_handler(callback: CallbackQuery, session, i18n, user, **_):
    """Редактирование поста (только невыложенных)"""
    await callback.answer()
    post_id = int(callback.data.split(":")[-1])
    
    post = await get_post_by_id(session, post_id)
    if not post:
        await callback.message.answer(i18n.get("post.not_found", "❌ Пост не найден."))
        return

    # Проверяем принадлежность поста пользователю
    workflow_result = await session.execute(
        select(UserWorkflow).where(UserWorkflow.id == post.user_workflow_id)
    )
    workflow = workflow_result.scalar_one_or_none()
    
    if not workflow or workflow.user_id != user.id:
        await callback.message.answer(i18n.get("post.access_denied", "❌ Доступ запрещен."))
        return

    # Проверяем что пост можно редактировать
    if post.status == "published":
        await callback.message.answer(i18n.get("post.edit.published_error", "❌ Опубликованные посты нельзя редактировать."))
        return

    # Переходим к редактированию
    from aiogram.fsm.context import FSMContext
    from .edit import EditPostStates
    
    await callback.message.delete()
    
    text = (
        f"✏️ <b>{i18n.get('post.edit.title', 'Редактирование поста')}</b>\n\n"
        f"🎯 <b>{i18n.get('post.add.topic_label', 'Тема')}:</b> {post.topic}\n"
        f"📄 <b>{i18n.get('post.add.content_label', 'Контент')}:</b> {post.content[:100]}...\n\n"
        f"{i18n.get('post.edit.choose_field', 'Выберите что хотите изменить:')}"
    )
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=i18n.get("post.edit.topic", "✏️ Тему"),
                callback_data=f"post:edit:topic:{post_id}"
            ),
            InlineKeyboardButton(
                text=i18n.get("post.edit.content", "📝 Контент"),
                callback_data=f"post:edit:content:{post_id}"
            )
        ],
        [
            InlineKeyboardButton(
                text=i18n.get("post.edit.schedule", "⏰ Время публикации"),
                callback_data=f"post:edit:schedule:{post_id}"
            )
        ],
        [
            InlineKeyboardButton(
                text=i18n.get("common.back", "⬅️ Назад"),
                callback_data=f"post:view:{post_id}"
            )
        ]
    ])
    
    await callback.message.answer(text, reply_markup=keyboard, parse_mode="HTML")


def register_posts_handler(router: Router):
    """Регистрация всех обработчиков постов"""
    router.message.register(posts_handler, Command("posts"))
    router.message.register(posts_handler, F.text.lower().contains("posts"))
    router.message.register(posts_handler, F.text.lower().contains("пост"))
    
    router.callback_query.register(posts_back_handler, F.data == "posts:back")
    router.callback_query.register(view_post_handler, F.data.startswith("post:view:"))
    router.callback_query.register(delete_post_handler, F.data.startswith("post:delete:"))
    router.callback_query.register(publish_post_handler, F.data.startswith("post:publish:"))
    router.callback_query.register(edit_post_handler, F.data.startswith("post:edit:")) 
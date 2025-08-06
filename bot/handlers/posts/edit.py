from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from datetime import datetime, timezone
from sqlalchemy.future import select

from bot.services.crud.post import update_post, get_post_by_id
from bot.models.models import UserWorkflow
from bot.keyboards.inline.workflows import get_time_selection_keyboard

router = Router()

class EditPostStates(StatesGroup):
    editing_topic = State()
    editing_content = State()
    editing_schedule = State()


async def edit_topic_handler(callback: CallbackQuery, session, i18n, user, state: FSMContext, **_):
    """Начало редактирования темы поста"""
    await callback.answer()
    post_id = int(callback.data.split(":")[-1])
    
    post = await get_post_by_id(session, post_id)
    if not post or post.status == "published":
        await callback.message.answer(i18n.get("post.not_found", "❌ Пост не найден."))
        return

    # Проверяем принадлежность
    workflow_result = await session.execute(
        select(UserWorkflow).where(UserWorkflow.id == post.user_workflow_id)
    )
    workflow = workflow_result.scalar_one_or_none()
    
    if not workflow or workflow.user_id != user.id:
        await callback.message.answer(i18n.get("post.access_denied", "❌ Доступ запрещен."))
        return

    await callback.message.delete()
    
    text = (
        f"✏️ <b>{i18n.get('post.edit.topic', 'Редактирование темы')}</b>\n\n"
        f"📝 <b>{i18n.get('post.edit.current_topic', 'Текущая тема')}:</b> {post.topic}\n\n"
        f"{i18n.get('post.edit.enter_new_topic', 'Введите новую тему поста:')}"
    )
    
    msg = await callback.message.answer(text, parse_mode="HTML")
    await state.set_state(EditPostStates.editing_topic)
    await state.update_data(post_id=post_id, prev_msg_id=msg.message_id)


async def edit_content_handler(callback: CallbackQuery, session, i18n, user, state: FSMContext, **_):
    """Начало редактирования контента поста"""
    await callback.answer()
    post_id = int(callback.data.split(":")[-1])
    
    post = await get_post_by_id(session, post_id)
    if not post or post.status == "published":
        await callback.message.answer(i18n.get("post.not_found", "❌ Пост не найден."))
        return

    # Проверяем принадлежность
    workflow_result = await session.execute(
        select(UserWorkflow).where(UserWorkflow.id == post.user_workflow_id)
    )
    workflow = workflow_result.scalar_one_or_none()
    
    if not workflow or workflow.user_id != user.id:
        await callback.message.answer(i18n.get("post.access_denied", "❌ Доступ запрещен."))
        return

    await callback.message.delete()
    
    text = (
        f"📝 <b>{i18n.get('post.edit.content', 'Редактирование контента')}</b>\n\n"
        f"📄 <b>{i18n.get('post.edit.current_content', 'Текущий контент')}:</b>\n{post.content[:200]}...\n\n"
        f"{i18n.get('post.edit.enter_new_content', 'Введите новый контент поста:')}"
    )
    
    msg = await callback.message.answer(text, parse_mode="HTML")
    await state.set_state(EditPostStates.editing_content)
    await state.update_data(post_id=post_id, prev_msg_id=msg.message_id)


async def edit_schedule_handler(callback: CallbackQuery, session, i18n, user, state: FSMContext, **_):
    """Начало редактирования времени публикации"""
    await callback.answer()
    post_id = int(callback.data.split(":")[-1])
    
    post = await get_post_by_id(session, post_id)
    if not post or post.status == "published":
        await callback.message.answer(i18n.get("post.not_found", "❌ Пост не найден."))
        return

    # Проверяем принадлежность
    workflow_result = await session.execute(
        select(UserWorkflow).where(UserWorkflow.id == post.user_workflow_id)
    )
    workflow = workflow_result.scalar_one_or_none()
    
    if not workflow or workflow.user_id != user.id:
        await callback.message.answer(i18n.get("post.access_denied", "❌ Доступ запрещен."))
        return

    await callback.message.delete()
    
    current_time = post.scheduled_time.strftime("%d.%m.%Y %H:%M") if post.scheduled_time else "Не указано"
    
    text = (
        f"⏰ <b>{i18n.get('post.edit.schedule', 'Редактирование времени публикации')}</b>\n\n"
        f"📅 <b>{i18n.get('post.edit.current_time', 'Текущее время')}:</b> {current_time}\n\n"
        f"{i18n.get('post.edit.choose_new_time', 'Выберите новое время публикации:')}"
    )
    
    msg = await callback.message.answer(text, reply_markup=get_time_selection_keyboard(), parse_mode="HTML")
    await state.set_state(EditPostStates.editing_schedule)
    await state.update_data(post_id=post_id, prev_msg_id=msg.message_id)


async def process_topic_edit(message: Message, state: FSMContext, session, i18n, **_):
    """Обработка нового значения темы"""
    topic = message.text.strip()
    
    if len(topic) < 5:
        await message.answer(i18n.get("post.add.topic_too_short", "⚠️ Тема слишком короткая. Минимум 5 символов."))
        return
    
    if len(topic) > 200:
        await message.answer(i18n.get("post.add.topic_too_long", "⚠️ Тема слишком длинная. Максимум 200 символов."))
        return
    
    data = await state.get_data()
    post_id = data.get("post_id")
    
    try:
        await message.delete()
        if msg_id := data.get("prev_msg_id"):
            await message.bot.delete_message(message.chat.id, msg_id)
    except: 
        pass
    
    # Обновляем тему
    success = await update_post(session, post_id, topic=topic)
    
    if success:
        text = f"✅ {i18n.get('post.edit.topic_updated', 'Тема поста обновлена!')}"
    else:
        text = f"❌ {i18n.get('post.edit.topic_error', 'Ошибка обновления темы.')}"
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=i18n.get("post.view_all", "📋 К посту"),
                callback_data=f"post:view:{post_id}"
            )
        ]
    ])
    
    await message.answer(text, reply_markup=keyboard)
    await state.clear()


async def process_content_edit(message: Message, state: FSMContext, session, i18n, **_):
    """Обработка нового значения контента"""
    content = message.text.strip()
    
    if len(content) < 10:
        await message.answer(i18n.get("post.add.content_too_short", "⚠️ Контент слишком короткий."))
        return
    
    if len(content) > 4000:
        await message.answer(i18n.get("post.add.content_too_long", "⚠️ Контент слишком длинный. Максимум 4000 символов."))
        return
    
    data = await state.get_data()
    post_id = data.get("post_id")
    
    try:
        await message.delete()
        if msg_id := data.get("prev_msg_id"):
            await message.bot.delete_message(message.chat.id, msg_id)
    except: 
        pass
    
    # Обновляем контент
    success = await update_post(session, post_id, content=content)
    
    if success:
        text = f"✅ {i18n.get('post.edit.content_updated', 'Контент поста обновлен!')}"
    else:
        text = f"❌ {i18n.get('post.edit.content_error', 'Ошибка обновления контента.')}"
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=i18n.get("post.view_all", "📋 К посту"),
                callback_data=f"post:view:{post_id}"
            )
        ]
    ])
    
    await message.answer(text, reply_markup=keyboard)
    await state.clear()


async def process_schedule_edit(callback: CallbackQuery, state: FSMContext, session, i18n, **_):
    """Обработка нового времени публикации"""
    await callback.answer()
    time_data = callback.data.split(":", 1)[-1]
    
    data = await state.get_data()
    post_id = data.get("post_id")
    
    try:
        if msg_id := data.get("prev_msg_id"):
            await callback.bot.delete_message(callback.message.chat.id, msg_id)
    except:
        pass
    
    # Парсим время
    if time_data == "now":
        scheduled_time = datetime.now(timezone.utc)
    else:
        today = datetime.now(timezone.utc)
        hour, minute = map(int, time_data.split(":"))
        scheduled_time = today.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if scheduled_time < today:
            scheduled_time = scheduled_time.replace(day=today.day + 1)
    
    # Обновляем время
    success = await update_post(session, post_id, scheduled_time=scheduled_time)
    
    if success:
        time_str = scheduled_time.strftime("%d.%m.%Y %H:%M")
        text = f"✅ {i18n.get('post.edit.schedule_updated', 'Время публикации обновлено!')} {time_str}"
    else:
        text = f"❌ {i18n.get('post.edit.schedule_error', 'Ошибка обновления времени.')}"
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=i18n.get("post.view_all", "📋 К посту"),
                callback_data=f"post:view:{post_id}"
            )
        ]
    ])
    
    await callback.message.answer(text, reply_markup=keyboard)
    await state.clear()


def register_edit_post_handlers(router: Router):
    """Регистрация обработчиков редактирования постов"""
    router.callback_query.register(edit_topic_handler, F.data.startswith("post:edit:topic:"))
    router.callback_query.register(edit_content_handler, F.data.startswith("post:edit:content:"))
    router.callback_query.register(edit_schedule_handler, F.data.startswith("post:edit:schedule:"))
    router.callback_query.register(process_schedule_edit, F.data.startswith("time:"))
    router.message.register(process_topic_edit, EditPostStates.editing_topic)
    router.message.register(process_content_edit, EditPostStates.editing_content) 
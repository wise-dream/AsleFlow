from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from bot.keyboards.inline.workflows import (
    get_account_selection_keyboard,
    get_moderation_keyboard,
    get_theme_selection_keyboard,
    get_media_type_keyboard,
    get_language_selection_keyboard,
    get_style_selection_keyboard,
    get_time_selection_keyboard,
    get_interval_keyboard,
    get_content_length_keyboard
)
from bot.services.crud.socials import get_social_accounts_by_user_id
from bot.services.crud.workflow import create_user_workflow
from bot.services.crud.workflow_settings import create_workflow_settings
import uuid

router = Router()

class AddWorkflowState(StatesGroup):
    choosing_account = State()
    entering_name = State()
    choosing_theme = State()
    choosing_media = State()
    entering_time = State()
    choosing_interval = State()
    entering_custom_interval = State()
    choosing_content_length = State()
    choosing_language = State()
    choosing_style = State()
    choosing_moderation = State()

async def add_workflow_start(callback: CallbackQuery, session, user, i18n, state: FSMContext, **_):
    await callback.answer()
    accounts = await get_social_accounts_by_user_id(session, user.id)

    if not accounts:
        await callback.message.answer(i18n.get("accounts.none"))
        await state.clear()
        return

    await callback.message.delete()
    msg = await callback.message.answer(
        i18n.get("workflow.add.choose_account"),
        reply_markup=get_account_selection_keyboard(accounts)
    )
    await state.set_state(AddWorkflowState.choosing_account)
    await state.update_data(prev_msg_id=msg.message_id)

async def process_account_selection(callback: CallbackQuery, state: FSMContext, i18n, **_):
    await callback.answer()
    account_id = int(callback.data.split(":")[-1])
    data = await state.get_data()
    try:
        if msg_id := data.get("prev_msg_id"):
            await callback.bot.delete_message(callback.message.chat.id, msg_id)
    except: pass

    msg = await callback.message.answer(i18n.get("workflow.add.enter_name"))
    await state.update_data(account_id=account_id, prev_msg_id=msg.message_id)
    await state.set_state(AddWorkflowState.entering_name)

async def process_name(message: Message, state: FSMContext, i18n, **_):
    data = await state.get_data()
    try:
        if msg_id := data.get("prev_msg_id"):
            await message.bot.delete_message(message.chat.id, msg_id)
            await message.delete()
    except: pass

    await state.update_data(name=message.text.strip())
    msg = await message.answer(
        i18n.get("workflow.add.enter_theme"),
        reply_markup=get_theme_selection_keyboard(i18n)
    )
    await state.set_state(AddWorkflowState.choosing_theme)
    await state.update_data(prev_msg_id=msg.message_id)

async def process_theme_selection(callback: CallbackQuery, state: FSMContext, i18n, **_):
    await callback.answer()
    theme = callback.data.split(":")[-1]
    data = await state.get_data()
    try:
        if msg_id := data.get("prev_msg_id"):
            await callback.bot.delete_message(callback.message.chat.id, msg_id)
    except: pass

    await state.update_data(theme=theme)
    msg = await callback.message.answer(
        i18n.get("workflow.add.choose_media"),
        reply_markup=get_media_type_keyboard(i18n)
    )
    await state.set_state(AddWorkflowState.choosing_media)
    await state.update_data(prev_msg_id=msg.message_id)

async def process_media_type(callback: CallbackQuery, state: FSMContext, i18n, **_):
    await callback.answer()
    media = callback.data.split(":")[-1]
    data = await state.get_data()
    try:
        if msg_id := data.get("prev_msg_id"):
            await callback.bot.delete_message(callback.message.chat.id, msg_id)
    except: pass

    if media not in {"text", "image", "video"}:
        await callback.message.answer(i18n.get("workflow.add.invalid_media"))
        return

    await state.update_data(media_type=media)

    combined_text = (
        f"{i18n.get('workflow.add.time_note')}\n\n"
        f"{i18n.get('workflow.add.enter_time')}"
    )
    msg = await callback.message.answer(
        combined_text,
        reply_markup=get_time_selection_keyboard()
    )

    await state.set_state(AddWorkflowState.entering_time)
    await state.update_data(prev_msg_id=msg.message_id)

async def process_time(callback: CallbackQuery, state: FSMContext, i18n, **_):
    await callback.answer()
    time = callback.data.split(":", maxsplit=1)[-1]
    data = await state.get_data()
    try:
        if msg_id := data.get("prev_msg_id"):
            await callback.bot.delete_message(callback.message.chat.id, msg_id)
    except: pass

    await state.update_data(first_post_time=time)
    msg = await callback.message.answer(
        i18n.get("workflow.add.choose_interval", "⏱️ Выберите интервал между постами:"),
        reply_markup=get_interval_keyboard(i18n)
    )
    await state.set_state(AddWorkflowState.choosing_interval)
    await state.update_data(prev_msg_id=msg.message_id)

async def process_interval(callback: CallbackQuery, state: FSMContext, i18n, **_):
    await callback.answer()
    interval_data = callback.data.split(":")[-1]
    data = await state.get_data()
    try:
        if msg_id := data.get("prev_msg_id"):
            await callback.bot.delete_message(callback.message.chat.id, msg_id)
    except: pass

    if interval_data == "custom":
        # Пользователь хочет ввести свой интервал
        msg = await callback.message.answer(
            i18n.get("workflow.add.enter_interval", "⏱️ Введите интервал в часах (от 14 до 168):")
        )
        await state.set_state(AddWorkflowState.entering_custom_interval)
        await state.update_data(prev_msg_id=msg.message_id)
    else:
        # Пользователь выбрал предустановленный интервал
        interval_hours = int(interval_data)
        # Проверяем диапазон
        if not (4 <= interval_hours <= 168):
            await callback.message.answer(i18n.get("workflow.add.invalid_interval", "⚠️ Интервал должен быть от 4 до 168 часов."))
            return
        
        await state.update_data(interval_hours=interval_hours)
        msg = await callback.message.answer(
            i18n.get("workflow.add.choose_content_length", "📏 Выберите желаемую длину контента:"),
            reply_markup=get_content_length_keyboard(i18n)
        )
        await state.set_state(AddWorkflowState.choosing_content_length)
        await state.update_data(prev_msg_id=msg.message_id)


async def process_custom_interval(message: Message, state: FSMContext, i18n, **_):
    """Обработка пользовательского интервала"""
    data = await state.get_data()
    interval_text = message.text.strip()

    # Проверяем что это число
    try:
        interval_hours = int(interval_text)
    except ValueError:
        await message.answer(i18n.get("workflow.add.invalid_interval", "⚠️ Интервал должен быть от 4 до 168 часов."))
        return

    # Проверяем диапазон
    if not (4 <= interval_hours <= 168):
        await message.answer(i18n.get("workflow.add.invalid_interval", "⚠️ Интервал должен быть от 4 до 168 часов."))
        return

    try:
        await message.delete()
        instruction_msg_id = data.get("prev_msg_id")
        if instruction_msg_id:
            await message.bot.delete_message(message.chat.id, instruction_msg_id)
    except Exception:
        pass

    await state.update_data(interval_hours=interval_hours)
    msg = await message.answer(
        i18n.get("workflow.add.choose_content_length", "📏 Выберите желаемую длину контента:"),
        reply_markup=get_content_length_keyboard(i18n)
    )
    await state.set_state(AddWorkflowState.choosing_content_length)
    await state.update_data(prev_msg_id=msg.message_id)


async def process_content_length(callback: CallbackQuery, state: FSMContext, i18n, **_):
    """Обработка выбора длины контента"""
    await callback.answer()
    length = callback.data.split(":")[-1]
    
    if length not in {"short", "medium", "long"}:
        await callback.message.answer(i18n.get("workflow.add.invalid_length", "❌ Неверный выбор длины контента."))
        return
    
    data = await state.get_data()
    try:
        if msg_id := data.get("prev_msg_id"):
            await callback.bot.delete_message(callback.message.chat.id, msg_id)
    except: 
        pass

    await state.update_data(content_length=length)
    msg = await callback.message.answer(
        i18n.get("workflow.add.choose_language"),
        reply_markup=get_language_selection_keyboard(i18n)
    )
    await state.set_state(AddWorkflowState.choosing_language)
    await state.update_data(prev_msg_id=msg.message_id)


async def process_language(callback: CallbackQuery, state: FSMContext, i18n, **_):
    await callback.answer()
    lang = callback.data.split(":")[-1]
    data = await state.get_data()
    try:
        if msg_id := data.get("prev_msg_id"):
            await callback.bot.delete_message(callback.message.chat.id, msg_id)
    except: pass

    await state.update_data(post_language=lang)
    msg = await callback.message.answer(
        i18n.get("workflow.add.choose_style"),
        reply_markup=get_style_selection_keyboard(i18n)
    )
    await state.set_state(AddWorkflowState.choosing_style)
    await state.update_data(prev_msg_id=msg.message_id)

async def process_style(callback: CallbackQuery, state: FSMContext, i18n, **_):
    await callback.answer()
    style = callback.data.split(":")[-1]
    if style not in {"formal", "informal", "friendly"}:
        await callback.message.answer(i18n.get("workflow.add.invalid_style", "❌ Неверный стиль."))
        return

    data = await state.get_data()
    try:
        if msg_id := data.get("prev_msg_id"):
            await callback.bot.delete_message(callback.message.chat.id, msg_id)
    except: pass

    await state.update_data(style=style)
    msg = await callback.message.answer(
        i18n.get("workflow.add.choose_moderation"),
        reply_markup=get_moderation_keyboard(i18n)
    )
    await state.set_state(AddWorkflowState.choosing_moderation)
    await state.update_data(prev_msg_id=msg.message_id)


async def process_moderation(callback: CallbackQuery, state: FSMContext, session, user, i18n, **_):
    await callback.answer()
    mode = callback.data.split(":")[-1]
    if mode not in {"on", "off"}:
        await callback.message.answer(i18n.get("workflow.add.invalid_moderation", "❌ Неверный выбор модерации."))
        return

    moderation = "enabled" if mode == "on" else "disabled"

    data = await state.get_data()
    try:
        if msg_id := data.get("prev_msg_id"):
            await callback.bot.delete_message(callback.message.chat.id, msg_id)
    except: pass



    workflow = await create_user_workflow(
        session,
        user_id=user.id,
        name=data["name"],
        workflow_id=str(uuid.uuid4())
    )
    await create_workflow_settings(
        session,
        user_workflow_id=workflow.id,
        social_account_id=data["account_id"],
        theme=data["theme"],
        first_post_time=data["first_post_time"],
        interval_hours=data.get("interval_hours", 24),  # По умолчанию 24 часа если не указан
        writing_style=data["style"],  # formal, friendly, humorous
        generation_method="ai",  # всегда ai при создании через бота
        content_length=data.get("content_length", "medium"),  # short, medium, long
        moderation=moderation,
        post_language=data["post_language"],
        post_media_type=data["media_type"]
    )

    await callback.message.answer(i18n.get("workflow.add.success"))
    await state.clear()


def register_add_workflow_handlers(router: Router):
    router.callback_query.register(add_workflow_start, F.data == "workflow:add")
    router.callback_query.register(process_moderation, F.data.startswith("moderation:"))
    router.callback_query.register(process_account_selection, F.data.startswith("workflow:account:"))
    router.callback_query.register(process_theme_selection, F.data.startswith("theme:"))
    router.callback_query.register(process_media_type, F.data.startswith("media:"))
    router.callback_query.register(process_time, F.data.startswith("time:"))
    router.callback_query.register(process_interval, F.data.startswith("interval:"))
    router.callback_query.register(process_content_length, F.data.startswith("length:"))
    router.callback_query.register(process_language, F.data.startswith("lang:"))
    router.callback_query.register(process_style, F.data.startswith("style:"))
    router.message.register(process_name, AddWorkflowState.entering_name)
    router.message.register(process_custom_interval, AddWorkflowState.entering_custom_interval)

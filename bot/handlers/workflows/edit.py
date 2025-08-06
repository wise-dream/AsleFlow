from aiogram import F, Router
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.utils.markdown import hbold

from bot.services.crud.workflow import (
    get_user_workflow_by_id,
    update_user_workflow,
    delete_user_workflow,
    toggle_workflow_status,
)
from bot.services.crud.workflow_settings import (
    toggle_moderation,
    update_workflow_settings,
    get_settings_by_workflow_id
)
from bot.keyboards.inline.workflows import get_edit_workflow_keyboard

router = Router()

class EditWorkflowStates(StatesGroup):
    editing_name = State()
    editing_theme = State()
    editing_time = State()
    editing_interval = State()


def get_workflow_info_text(workflow, settings, i18n):
    """Формирует текст с информацией о workflow"""
    # Переводим статус
    status_key = f"workflow.status.{workflow.status}"
    status_text = i18n.get(status_key, workflow.status)
    status_text = status_text.upper()  # всегда капсом
    
    # Получаем переводы полей
    status_label = i18n.get("workflow.field.status", "📊 Статус")
    
    text = (
        f"🛠 <b>{hbold(workflow.name)}</b>\n\n"
        f"<b>{status_label}:</b> {status_text}\n"
    )
    
    if settings:
        # Переводим модерацию
        moderation_key = f"workflow.moderation.{settings.moderation}"
        moderation_text = i18n.get(moderation_key, settings.moderation)
        
        # Получаем переводы полей
        theme_label = i18n.get("workflow.field.theme", "🎯 Тема")
        time_label = i18n.get("workflow.field.time", "⏰ Время")
        interval_label = i18n.get("workflow.field.interval", "⏱️ Интервал")
        language_label = i18n.get("workflow.field.language", "🌐 Язык")
        style_label = i18n.get("workflow.field.style", "Стиль")
        moderation_label = i18n.get("workflow.field.moderation", "🔧 Модерация")
        
        # Форматируем интервал
        interval_hours = settings.interval_hours or 6
        interval_text = f"{interval_hours}ч" if i18n.get("language") == "ru" else f"{interval_hours}h"
        
        # Стиль письма
        style_value = i18n.get(f"workflow.style.{getattr(settings, 'writing_style', 'friendly')}", getattr(settings, 'writing_style', 'friendly'))
        
        # Язык: флаг + капсом
        lang_code = (settings.post_language or "ru").upper()
        flag = {
            "RU": "🇷🇺",
            "EN": "🇬🇧",
            "UA": "🇺🇦",
            "ES": "🇪🇸",
            "DE": "🇩🇪",
            "FR": "🇫🇷"
        }.get(lang_code, "🏳️")
        lang_text = f"{flag} {lang_code}"
        
        text += (
            f"<b>{theme_label}:</b> {settings.theme}\n"
            f"<b>{time_label}:</b> {settings.first_post_time}\n"
            f"<b>{interval_label}:</b> {interval_text}\n"
            f"<b>{language_label}:</b> {lang_text}\n"
            f"✍️ <b>{style_label}:</b> {style_value}\n"
            f"<b>{moderation_label}:</b> {moderation_text}\n"
        )
    
    return text


async def edit_workflow_handler(callback: CallbackQuery, session, user, i18n, **_):
    """Главное меню редактирования workflow"""
    await callback.answer()
    workflow_id = int(callback.data.split(":")[-1])
    
    # Получаем workflow и проверяем что он принадлежит пользователю
    workflow = await get_user_workflow_by_id(session, workflow_id)
    if not workflow or workflow.user_id != user.id:
        await callback.message.answer(i18n.get("workflow.not_found", "❌ Задача не найдена."))
        return

    # Получаем настройки workflow
    settings = await get_settings_by_workflow_id(session, workflow_id) if workflow else None
    
    text = get_workflow_info_text(workflow, settings, i18n)

    try:
        await callback.message.edit_text(
            text=text,
            reply_markup=get_edit_workflow_keyboard(
                workflow_id=workflow.id,
                i18n=i18n,
                moderation_enabled=(settings.moderation == "enabled" if settings else False),
                is_active=(workflow.status == "active")
            ),
            parse_mode="HTML"
        )
    except Exception:
        await callback.message.answer(
            text=text,
            reply_markup=get_edit_workflow_keyboard(
                workflow_id=workflow.id,
                i18n=i18n,
                moderation_enabled=(settings.moderation == "enabled" if settings else False),
                is_active=(workflow.status == "active")
            ),
            parse_mode="HTML"
        )


async def toggle_moderation_handler(callback: CallbackQuery, session, user, i18n, **_):
    """Переключение модерации"""
    await callback.answer()
    workflow_id = int(callback.data.split(":")[-1])
    
    workflow = await toggle_moderation(session, user.id, workflow_id)
    if not workflow:
        await callback.message.answer(i18n.get("workflow.not_found"))
        return

    settings = await get_settings_by_workflow_id(session, workflow_id)
    text = get_workflow_info_text(workflow, settings, i18n)
    
    await callback.message.edit_text(
        text=text,
        reply_markup=get_edit_workflow_keyboard(
            workflow_id=workflow.id,
            i18n=i18n,
            moderation_enabled=(settings.moderation == "enabled" if settings else False),
            is_active=(workflow.status == "active")
        ),
        parse_mode="HTML"
    )


async def toggle_status_handler(callback: CallbackQuery, session, user, i18n, **_):
    """Переключение статуса активности"""
    await callback.answer()
    
    result = await toggle_workflow_status(session, user.id, int(callback.data.split(":")[-1]))
    workflow, error = result
    
    if not workflow:
        if error == "no_subscription":
            await callback.answer(i18n.get("workflow.activation.no_subscription", "❌ Нет активной подписки"), show_alert=True)
        elif error == "limit_exceeded":
            # Получаем информацию о лимитах для показа пользователю
            from bot.services.crud.subscription import get_user_active_subscription
            active_subscription = await get_user_active_subscription(session, user.id)
            if active_subscription:
                channels_limit = active_subscription.plan.channels_limit
                await callback.answer(
                    i18n.get("workflow.activation.limit_exceeded", 
                            "❌ Достигнут лимит активных задач: {limit}").format(limit=channels_limit), 
                    show_alert=True
                )
            else:
                await callback.answer(i18n.get("workflow.activation.limit_exceeded", "❌ Достигнут лимит активных задач"), show_alert=True)
        else:
            await callback.answer(i18n.get("workflow.not_found", "❌ Задача не найдена"), show_alert=True)
        return

    settings = await get_settings_by_workflow_id(session, workflow.id)
    text = get_workflow_info_text(workflow, settings, i18n)
    
    await callback.message.edit_text(
        text=text,
        reply_markup=get_edit_workflow_keyboard(
            workflow_id=workflow.id,
            i18n=i18n,
            moderation_enabled=(settings.moderation == "enabled" if settings else False),
            is_active=(workflow.status == "active")
        ),
        parse_mode="HTML"
    )


async def edit_workflow_name_handler(callback: CallbackQuery, state: FSMContext, i18n):
    """Начало редактирования имени"""
    await callback.answer()
    workflow_id = int(callback.data.split(":")[-1])

    try:
        await callback.message.delete()
    except:
        pass

    instruction_msg = await callback.message.answer(
        i18n.get("workflow.edit_name_prompt", "✏️ Введите новое название задачи:")
    )

    await state.set_state(EditWorkflowStates.editing_name)
    await state.update_data(
        workflow_id=workflow_id,
        instruction_msg_id=instruction_msg.message_id,
    )


async def edit_workflow_theme_handler(callback: CallbackQuery, state: FSMContext, i18n):
    """Начало редактирования темы"""
    await callback.answer()
    workflow_id = int(callback.data.split(":")[-1])

    try:
        await callback.message.delete()
    except:
        pass

    instruction_msg = await callback.message.answer(
        i18n.get("workflow.edit_theme_prompt", "🎯 Введите новую тематику постов:")
    )

    await state.set_state(EditWorkflowStates.editing_theme)
    await state.update_data(
        workflow_id=workflow_id,
        instruction_msg_id=instruction_msg.message_id,
    )


async def edit_workflow_time_handler(callback: CallbackQuery, state: FSMContext, i18n):
    """Начало редактирования времени"""
    await callback.answer()
    workflow_id = int(callback.data.split(":")[-1])

    try:
        await callback.message.delete()
    except:
        pass

    instruction_msg = await callback.message.answer(
        i18n.get("workflow.edit_time_prompt", "⏰ Введите новое время первого поста (HH:MM):")
    )

    await state.set_state(EditWorkflowStates.editing_time)
    await state.update_data(
        workflow_id=workflow_id,
        instruction_msg_id=instruction_msg.message_id,
    )


async def edit_workflow_interval_handler(callback: CallbackQuery, state: FSMContext, i18n):
    """Начало редактирования интервала"""
    await callback.answer()
    workflow_id = int(callback.data.split(":")[-1])

    try:
        await callback.message.delete()
    except:
        pass

    instruction_msg = await callback.message.answer(
        i18n.get("workflow.edit_interval_prompt", "⏱️ Введите новый интервал в часах (от 14 до 168):")
    )

    await state.set_state(EditWorkflowStates.editing_interval)
    await state.update_data(
        workflow_id=workflow_id,
        instruction_msg_id=instruction_msg.message_id,
    )


async def process_new_workflow_name(message: Message, state: FSMContext, session, user, i18n, **_):
    """Обработка нового имени workflow"""
    data = await state.get_data()
    workflow_id = data.get("workflow_id")
    new_name = message.text.strip()

    if len(new_name) < 2:
        await message.answer(i18n.get("workflow.name_too_short", "⚠️ Название слишком короткое."))
        return

    # Проверяем что workflow принадлежит пользователю
    workflow = await get_user_workflow_by_id(session, workflow_id)
    if not workflow or workflow.user_id != user.id:
        await message.answer(i18n.get("workflow.not_found"))
        await state.clear()
        return

    await update_user_workflow(session, workflow_id, name=new_name)

    try:
        await message.delete()
        instruction_msg_id = data.get("instruction_msg_id")
        if instruction_msg_id:
            await message.bot.delete_message(message.chat.id, instruction_msg_id)
    except Exception:
        pass

    await message.answer(i18n.get("workflow.name_updated", "✅ Название задачи обновлено."))
    await state.clear()


async def process_new_workflow_theme(message: Message, state: FSMContext, session, user, i18n, **_):
    """Обработка новой темы workflow"""
    data = await state.get_data()
    workflow_id = data.get("workflow_id")
    new_theme = message.text.strip()

    if len(new_theme) < 2:
        await message.answer(i18n.get("workflow.theme_too_short", "⚠️ Тема слишком короткая."))
        return

    # Проверяем что workflow принадлежит пользователю
    workflow = await get_user_workflow_by_id(session, workflow_id)
    if not workflow or workflow.user_id != user.id:
        await message.answer(i18n.get("workflow.not_found"))
        await state.clear()
        return

    # Обновляем настройки workflow
    settings = await get_settings_by_workflow_id(session, workflow_id)
    if settings:
        await update_workflow_settings(session, settings.id, theme=new_theme)

    try:
        await message.delete()
        instruction_msg_id = data.get("instruction_msg_id")
        if instruction_msg_id:
            await message.bot.delete_message(message.chat.id, instruction_msg_id)
    except Exception:
        pass

    await message.answer(i18n.get("workflow.theme_updated", "✅ Тема обновлена."))
    await state.clear()


async def process_new_workflow_time(message: Message, state: FSMContext, session, user, i18n, **_):
    """Обработка нового времени workflow"""
    data = await state.get_data()
    workflow_id = data.get("workflow_id")
    new_time = message.text.strip()

    # Проверяем формат времени
    import re
    if not re.match(r'^([0-1]\d|2[0-3]):([0-5]\d)$', new_time):
        await message.answer(i18n.get("workflow.invalid_time", "⚠️ Неверный формат времени. Используйте HH:MM"))
        return

    # Проверяем что workflow принадлежит пользователю
    workflow = await get_user_workflow_by_id(session, workflow_id)
    if not workflow or workflow.user_id != user.id:
        await message.answer(i18n.get("workflow.not_found"))
        await state.clear()
        return

    # Обновляем настройки workflow
    settings = await get_settings_by_workflow_id(session, workflow_id)
    if settings:
        await update_workflow_settings(session, settings.id, first_post_time=new_time)

    try:
        await message.delete()
        instruction_msg_id = data.get("instruction_msg_id")
        if instruction_msg_id:
            await message.bot.delete_message(message.chat.id, instruction_msg_id)
    except Exception:
        pass

    await message.answer(i18n.get("workflow.time_updated", "✅ Время обновлено."))
    await state.clear()


async def process_new_workflow_interval(message: Message, state: FSMContext, session, user, i18n, **_):
    """Обработка нового интервала workflow"""
    data = await state.get_data()
    workflow_id = data.get("workflow_id")
    new_interval_text = message.text.strip()

    # Проверяем что это число
    try:
        new_interval = int(new_interval_text)
    except ValueError:
        await message.answer(i18n.get("workflow.add.invalid_interval", "⚠️ Интервал должен быть от 4 до 168 часов."))
        return

    # Проверяем диапазон
    if not (4 <= new_interval <= 168):
        await message.answer(i18n.get("workflow.add.invalid_interval", "⚠️ Интервал должен быть от 4 до 168 часов."))
        return

    # Проверяем что workflow принадлежит пользователю
    workflow = await get_user_workflow_by_id(session, workflow_id)
    if not workflow or workflow.user_id != user.id:
        await message.answer(i18n.get("workflow.not_found"))
        await state.clear()
        return

    # Обновляем настройки workflow
    settings = await get_settings_by_workflow_id(session, workflow_id)
    if settings:
        await update_workflow_settings(session, settings.id, interval_hours=new_interval)

    try:
        await message.delete()
        instruction_msg_id = data.get("instruction_msg_id")
        if instruction_msg_id:
            await message.bot.delete_message(message.chat.id, instruction_msg_id)
    except Exception:
        pass

    await message.answer(i18n.get("workflow.interval_updated", "✅ Интервал обновлён."))
    await state.clear()


async def delete_workflow_handler(callback: CallbackQuery, session, user, i18n):
    """Удаление workflow"""
    await callback.answer()
    workflow_id = int(callback.data.split(":")[-1])
    
    # Проверяем что workflow принадлежит пользователю
    workflow = await get_user_workflow_by_id(session, workflow_id)
    if not workflow or workflow.user_id != user.id:
        await callback.message.answer(i18n.get("workflow.not_found"))
        return
    
    await delete_user_workflow(session, workflow_id)
    await callback.message.edit_text(i18n.get("workflow.deleted", "✅ Задача удалена."))


def register_edit_workflow_handlers(router: Router):
    """Регистрация всех обработчиков редактирования workflow"""
    router.callback_query.register(edit_workflow_handler, F.data.startswith("workflow:view:"))
    router.callback_query.register(toggle_moderation_handler, F.data.startswith("workflow:edit:moderation:"))
    router.callback_query.register(toggle_status_handler, F.data.startswith("workflow:edit:toggle:"))
    router.callback_query.register(edit_workflow_name_handler, F.data.startswith("workflow:edit:name:"))
    router.callback_query.register(edit_workflow_theme_handler, F.data.startswith("workflow:edit:theme:"))
    router.callback_query.register(edit_workflow_time_handler, F.data.startswith("workflow:edit:time:"))
    router.callback_query.register(edit_workflow_interval_handler, F.data.startswith("workflow:edit:interval:"))
    router.callback_query.register(delete_workflow_handler, F.data.startswith("workflow:delete:"))
    
    # FSM состояния
    router.message.register(process_new_workflow_name, EditWorkflowStates.editing_name)
    router.message.register(process_new_workflow_theme, EditWorkflowStates.editing_theme)
    router.message.register(process_new_workflow_time, EditWorkflowStates.editing_time)
    router.message.register(process_new_workflow_interval, EditWorkflowStates.editing_interval)

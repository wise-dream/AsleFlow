from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.models import User
from bot.keyboards.inline.settings import get_settings_keyboard

from bot.services.crud.user import update_user_with_cache_clear, get_user_by_telegram_id
from bot.middlewares.i18n import I18nMiddleware

router = Router()


class SettingsStates(StatesGroup):
    waiting_for_email = State()
    waiting_for_referrer_code = State()  # Состояние для ввода реферального кода


async def settings_handler(message: Message, session, i18n, user, **_):
    """Показывает меню настроек"""
    await message.answer(
        i18n.get("settings.title", "⚙️ Настройки"),
        reply_markup=get_settings_keyboard(i18n)
    )


async def settings_callback_handler(callback: CallbackQuery, session, i18n, user, **_):
    """Обработчик кнопок настроек"""
    data = callback.data
    
    if data == "settings:language":
        # Вызываем обработчик выбора языка
        await language_selection_handler(callback, session, i18n, user)
        
    elif data == "settings:edit_name":
        await callback.answer(i18n.get("settings.edit_name_info", "Функция в разработке"))
        
    elif data == "settings:email":
        await handle_email_settings(callback, session, i18n, user)
        
    elif data == "settings:referral":
        await handle_referral_settings(callback, session, i18n, user)
        
    elif data == "settings:back":
        await back_to_settings_handler(callback, session, i18n, user)
        
    else:
        await callback.answer("❌ Неизвестная команда")


async def handle_email_settings(callback: CallbackQuery, session, i18n, user, **_):
    """Обработчик настроек email"""
    current_email = user.email or i18n.get("settings.no_email", "Не указан")
    
    if user.email:
        # Если email уже есть, предлагаем изменить
        text = (
            f"📧 <b>Текущий email:</b> {user.email}\n\n"
            f"{i18n.get('settings.email_change_prompt', 'Отправьте новый email или нажмите Отмена')}"
        )
    else:
        # Если email нет, предлагаем добавить
        text = (
            f"📧 <b>Email:</b> {i18n.get('settings.no_email', 'Не указан')}\n\n"
            f"{i18n.get('settings.email_add_prompt', 'Отправьте ваш email')}"
        )
    
    from bot.keyboards.inline.settings import get_email_keyboard
    await callback.message.edit_text(
        text,
        reply_markup=get_email_keyboard(i18n),
        parse_mode="HTML"
    )


async def email_enter_handler(callback: CallbackQuery, state: FSMContext, i18n, **_):
    """Обработчик кнопки ввода email"""
    await callback.answer()
    await callback.message.edit_text(
        i18n.get("settings.email_add_prompt", "Отправьте ваш email:"),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="🔙 " + i18n.get("back", "Назад"), 
                callback_data="settings:back"
            )]
        ])
    )
    await state.set_state(SettingsStates.waiting_for_email)


async def handle_referral_settings(callback: CallbackQuery, session, i18n, user, **_):
    """Обработчик настроек реферального кода"""
    current_code = user.referral_code or i18n.get("settings.no_referral_code", "Не сгенерирован")
    
    if user.referral_code:
        # Если код есть, показываем его
        text = (
            f"🎫 <b>Ваш реферальный код:</b> <code>{user.referral_code}</code>\n\n"
            f"{i18n.get('settings.referral_info', 'Используйте этот код для приглашения друзей')}"
        )
    else:
        # Если кода нет, показываем ошибку
        text = (
            f"🎫 <b>Реферальный код:</b> {i18n.get('settings.no_referral_code', 'Не сгенерирован')}\n\n"
            f"{i18n.get('settings.referral_error_info', 'Ошибка: реферальный код не был создан при регистрации')}"
        )
    
    from bot.keyboards.inline.settings import get_referral_keyboard
    await callback.message.edit_text(
        text,
        reply_markup=get_referral_keyboard(i18n, user.referral_code),
        parse_mode="HTML"
    )





async def referral_code_input_handler(message: Message, state: FSMContext, session, i18n, user, **_):
    """Обработчик ввода реферального кода в настройках"""
    
    code = message.text.strip().upper()
    
    # Проверяем формат кода
    from bot.utils.referral import validate_referral_code, get_user_by_referral_code
    if not validate_referral_code(code):
        await message.answer(
            i18n.get('referral.invalid_format',
                     '❌ <b>Неверный формат кода!</b>\n\n'
                     'Код должен быть 8 символов и содержать только заглавные буквы и цифры.\n'
                     'Пример: <code>ABC12345</code>\n\n'
                     'Попробуйте еще раз или нажмите "Отмена"'),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text=i18n.get("common.cancel", "Отмена"), 
                    callback_data="cancel_referral_input"
                )]
            ])
        )
        return
    
    # Проверяем, не пытается ли пользователь использовать свой код
    if code == user.referral_code:
        await message.answer(
            i18n.get('referral.self_referral',
                     '❌ <b>Нельзя использовать свой код!</b>\n\n'
                     'Введите код другого пользователя или нажмите "Отмена"'),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text=i18n.get("common.cancel", "Отмена"), 
                    callback_data="cancel_referral_input"
                )]
            ])
        )
        return
    
    # Ищем пользователя с таким кодом
    referrer = await get_user_by_referral_code(session, code)
    if not referrer:
        await message.answer(
            i18n.get('referral.code_not_found',
                     '❌ <b>Код не найден!</b>\n\n'
                     'Пользователь с таким реферальным кодом не существует.\n'
                     'Проверьте код и попробуйте еще раз или нажмите "Отмена"'),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text=i18n.get("common.cancel", "Отмена"), 
                    callback_data="cancel_referral_input"
                )]
            ])
        )
        return
    
    # Проверяем, не пытается ли пользователь пригласить сам себя
    if referrer.id == user.id:
        await message.answer(
            i18n.get('referral.self_referral',
                     '❌ <b>Нельзя использовать свой код!</b>\n\n'
                     'Введите код другого пользователя или нажмите "Отмена"'),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text=i18n.get("common.cancel", "Отмена"), 
                    callback_data="cancel_referral_input"
                )]
            ])
        )
        return
    
    # Проверяем, не пытается ли пользователь пригласить того, кто его уже пригласил
    if hasattr(referrer, 'referred_by_id') and referrer.referred_by_id == user.id:
        await message.answer(
            i18n.get('referral.circular_referral',
                     '❌ <b>Циклическая реферальная связь!</b>\n\n'
                     'Нельзя пригласить пользователя, который вас пригласил.\n'
                     'Введите другой код или нажмите "Отмена"'),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text=i18n.get("common.cancel", "Отмена"), 
                    callback_data="cancel_referral_input"
                )]
            ])
        )
        return
    
    # Устанавливаем реферальную связь
    try:
        from bot.services.crud.user import update_user_with_cache_clear
        updated_user = await update_user_with_cache_clear(
            session, user.id, referred_by_id=referrer.id
        )
        
        if updated_user:
            # Очищаем состояние
            await state.clear()
            
            # Отправляем подтверждение
            await message.answer(
                i18n.get('referral.success',
                         f'✅ <b>Реферальная связь установлена!</b>\n\n'
                         f'Вы были приглашены пользователем: <b>{referrer.name}</b>\n'
                         f'Его реферальный код: <code>{referrer.referral_code}</code>\n\n'
                         f'Теперь вы можете получать бонусы за приглашения!'),
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(
                        text=i18n.get("common.back_to_settings", "Назад к настройкам"), 
                        callback_data="settings:back"
                    )]
                ])
            )
            
        else:
            await message.answer(
                i18n.get('referral.update_error',
                         '❌ <b>Ошибка при обновлении!</b>\n\n'
                         'Не удалось установить реферальную связь.\n'
                         'Попробуйте еще раз позже.'),
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(
                        text=i18n.get("common.cancel", "Отмена"), 
                        callback_data="cancel_referral_input"
                    )]
                ])
            )
    
    except Exception as e:
        print(f"Ошибка при установке реферальной связи: {e}")
        await message.answer(
            i18n.get('referral.system_error',
                     '❌ <b>Системная ошибка!</b>\n\n'
                     'Произошла ошибка при установке реферальной связи.\n'
                     'Попробуйте еще раз позже.'),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text=i18n.get("common.cancel", "Отмена"), 
                    callback_data="cancel_referral_input"
                )]
            ])
        )


async def email_input_handler(message: Message, state: FSMContext, session, i18n, user, redis=None, **_):
    """Обработчик ввода email"""
    email = message.text.strip()
    
    # Простая валидация email
    if '@' not in email or '.' not in email:
        await message.answer(i18n.get("settings.email_invalid", "❌ Неверный формат email"))
        return
    
    try:
        # Обновляем пользователя и очищаем кэш
        updated_user = await update_user_with_cache_clear(session, user.id, email=email)
        
        if updated_user:
            await message.answer(
                f"✅ {i18n.get('settings.email_updated', 'Email обновлен')}: {email}",
                reply_markup=get_settings_keyboard(i18n)
            )
        else:
            await message.answer(i18n.get("settings.email_update_error", "❌ Ошибка обновления email"))
            
    except Exception as e:
        print(f"Ошибка обновления email: {e}")
        await message.answer(i18n.get("settings.email_error", "❌ Произошла ошибка"))


async def referral_copy_handler(callback: CallbackQuery, i18n, **_):
    """Обработчик копирования реферального кода"""
    data = callback.data
    if data.startswith("referral:copy:"):
        code = data.split(":")[2]
        await callback.answer(f"📋 {i18n.get('referral.copy', 'Скопировано')}: {code}")
    else:
        await callback.answer("❌ Ошибка копирования")





async def language_selection_handler(callback: CallbackQuery, session, i18n, user, **_):
    """Обработчик выбора языка"""
    from bot.keyboards.inline.settings import get_language_keyboard
    await callback.message.edit_text(
        i18n.get("language.choose", "🌐 Выберите язык интерфейса:"),
        reply_markup=get_language_keyboard(i18n)
    )


async def language_set_handler(callback: CallbackQuery, session, i18n, user, redis=None, **_):
    """Обработчик установки языка"""
    data = callback.data
    if data.startswith("language:set:"):
        lang = data.split(":")[2]
        
        try:
            # Обновляем пользователя и очищаем кэш
            updated_user = await update_user_with_cache_clear(session, user.id, redis, language=lang)
            
            if updated_user:
                # Получаем новые переводы для выбранного языка
                from bot.middlewares.i18n import I18nMiddleware
                new_translations = I18nMiddleware().translations.get(lang, {})
                
                # Отправляем приветственное сообщение на новом языке
                welcome_text = new_translations.get("welcome", "Привет, {name}!").format(name=user.name or callback.from_user.full_name)
                alert_text = new_translations.get("language_set", "✅ Язык успешно обновлён!")
                
                # Удаляем текущее сообщение с настройками
                try:
                    await callback.message.delete()
                except Exception as e:
                    print(f"Не удалось удалить сообщение: {e}")
                
                # Отправляем новое приветственное сообщение с главным меню
                from bot.keyboards.reply.main_menu import get_main_menu
                reply_markup = get_main_menu(new_translations)
                await callback.message.answer(welcome_text, reply_markup=reply_markup)
                
                await callback.answer(alert_text, show_alert=True)
            else:
                await callback.answer("❌ Ошибка обновления языка")
                
        except Exception as e:
            print(f"Ошибка обновления языка: {e}")
            await callback.answer("❌ Ошибка обновления языка")


async def referral_input_handler(callback: CallbackQuery, state: FSMContext, session, i18n, user, **_):
    """Обработчик кнопки ввода реферального кода"""
    # Проверяем, есть ли уже реферал
    if user.referred_by_id:
        await callback.answer(i18n.get('referral.already_has_referrer', 'У вас уже есть реферал!'), show_alert=True)
        return
    
    # Проверяем, есть ли у пользователя реферальный код
    if not user.referral_code:
        await callback.answer(i18n.get('referral.no_code_error', 'Ошибка: у вас нет реферального кода!'), show_alert=True)
        return
    
    # Переходим в состояние ожидания кода реферера
    await callback.message.edit_text(
        i18n.get('referral.input_prompt', 
                 '🎫 <b>Введите реферальный код пригласившего</b>\n\n'
                 'Если вас пригласил друг, попросите у него реферальный код.\n'
                 'Код должен быть 8 символов и содержать только заглавные буквы и цифры.\n\n'
                 'Пример: <code>ABC12345</code>\n\n'
                 'Просто введите код в следующем сообщении:'),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text=i18n.get("common.cancel", "Отмена"), 
                callback_data="cancel_referral_input"
            )]
        ])
    )
    
    # Устанавливаем состояние ожидания ввода кода
    await state.set_state(SettingsStates.waiting_for_referrer_code)
    await callback.answer()


async def cancel_referral_input_handler(callback: CallbackQuery, state: FSMContext, session, i18n, user, **_):
    """Отменяет ввод реферального кода"""
    
    await state.clear()
    
    await callback.message.edit_text(
        i18n.get('referral.cancelled',
                 '❌ <b>Ввод реферального кода отменен</b>\n\n'
                 'Вы можете попробовать позже в настройках.'),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text=i18n.get("common.back_to_settings", "Назад к настройкам"), 
                callback_data="settings:back"
            )]
        ])
    )
    
    await callback.answer()


async def back_to_settings_handler(callback: CallbackQuery, session, i18n, user, **_):
    """Возврат к основному меню настроек"""
    from bot.keyboards.inline.settings import get_settings_keyboard
    await callback.message.edit_text(
        i18n.get("settings.title", "⚙️ Настройки"),
        reply_markup=get_settings_keyboard(i18n)
    )





def register_settings_handler(router: Router):
    """Регистрирует хендлеры настроек"""
    
    # Основные хендлеры
    router.message.register(settings_handler, Command("settings"))
    router.message.register(settings_handler, F.text.lower().contains("настройки"))
    router.message.register(settings_handler, F.text.lower().contains("settings"))
    router.callback_query.register(settings_callback_handler, lambda c: c.data.startswith("settings:"))
    router.callback_query.register(email_enter_handler, lambda c: c.data == "email:enter")
    
    # Новые обработчики
    router.callback_query.register(referral_copy_handler, lambda c: c.data.startswith("referral:copy:"))
    router.callback_query.register(language_selection_handler, lambda c: c.data == "settings:language")
    router.callback_query.register(language_set_handler, lambda c: c.data.startswith("language:set:"))
    router.callback_query.register(referral_input_handler, lambda c: c.data == "referral:input")
    router.callback_query.register(cancel_referral_input_handler, lambda c: c.data == "cancel_referral_input")
    router.callback_query.register(back_to_settings_handler, lambda c: c.data == "settings:back")
    

    
    # FSM хендлеры
    router.message.register(email_input_handler, SettingsStates.waiting_for_email)
    router.message.register(referral_code_input_handler, SettingsStates.waiting_for_referrer_code)


__all__ = ["register_settings_handler"]

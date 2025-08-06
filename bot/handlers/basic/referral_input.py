from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram import F, Router
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.keyboards.inline.settings import get_settings_keyboard
from bot.utils.referral import validate_referral_code, get_user_by_referral_code
from bot.services.crud.user import update_user_with_cache_clear

router = Router()


class ReferralInputStates(StatesGroup):
    """Состояния для ввода реферального кода"""
    waiting_for_code = State()
    waiting_for_referrer_code = State()  # Новое состояние для ввода чужого кода


async def start_referral_input(callback: CallbackQuery, session, i18n, user, **_):
    """Начинает процесс обновления реферального кода"""
    
    # Проверяем, есть ли у пользователя реферальный код
    if not user.referral_code:
        await callback.answer(i18n.get('referral.no_code_error', 'Ошибка: у вас нет реферального кода!'), show_alert=True)
        return
    
    # Переходим в состояние ожидания кода
    await callback.message.edit_text(
        i18n.get('referral.update_prompt', 
                 '🎫 <b>Обновите ваш реферальный код</b>\n\n'
                 'Введите новый 8-символьный код для приглашения друзей.\n'
                 'Код должен содержать только заглавные буквы и цифры.\n\n'
                 'Пример: <code>ABC12345</code>\n\n'
                 'Введите новый код или нажмите "Отмена"'),
        reply_markup=get_cancel_keyboard(i18n)
    )
    
    await callback.answer()


async def start_referrer_input(callback: CallbackQuery, session, i18n, user, **_):
    """Начинает процесс ввода реферального кода пригласившего пользователя"""
    
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
                 '🎫 <b>Введите реферальный код</b>\n\n'
                 'Введите 8-символьный код пригласившего вас пользователя.\n'
                 'Код должен содержать только заглавные буквы и цифры.\n\n'
                 'Пример: <code>ABC12345</code>\n\n'
                 'Введите код или нажмите "Отмена"'),
        reply_markup=get_cancel_keyboard(i18n)
    )
    
    await callback.answer()
    await callback.message.answer(
        i18n.get('referral.input_hint', 'Введите код или нажмите "Отмена"'),
        reply_markup=get_cancel_keyboard(i18n)
    )


async def handle_referral_code_input(message: Message, state: FSMContext, session, i18n, user, **_):
    """Обрабатывает обновление реферального кода"""
    
    code = message.text.strip().upper()
    
    # Проверяем формат кода
    if not validate_referral_code(code):
        await message.answer(
            i18n.get('referral.invalid_format',
                     '❌ <b>Неверный формат кода!</b>\n\n'
                     'Код должен быть 8 символов и содержать только заглавные буквы и цифры.\n'
                     'Пример: <code>ABC12345</code>\n\n'
                     'Попробуйте еще раз или нажмите "Отмена"'),
            reply_markup=get_cancel_keyboard(i18n)
        )
        return
    
    # Проверяем, не пытается ли пользователь использовать свой текущий код
    if code == user.referral_code:
        await message.answer(
            i18n.get('referral.same_code',
                     '❌ <b>Это ваш текущий код!</b>\n\n'
                     'Введите новый код или нажмите "Отмена"'),
            reply_markup=get_cancel_keyboard(i18n)
        )
        return
    
    # Проверяем, не занят ли код другим пользователем
    existing_user = await get_user_by_referral_code(session, code)
    if existing_user and existing_user.id != user.id:
        await message.answer(
            i18n.get('referral.code_taken',
                     '❌ <b>Код уже занят!</b>\n\n'
                     'Этот код уже используется другим пользователем.\n'
                     'Попробуйте другой код или нажмите "Отмена"'),
            reply_markup=get_cancel_keyboard(i18n)
        )
        return
    
    # Обновляем реферальный код
    try:
        updated_user = await update_user_with_cache_clear(
            session, user.id, referral_code=code
        )
        
        if updated_user:
            # Очищаем состояние
            await state.clear()
            
            # Отправляем подтверждение
            await message.answer(
                i18n.get('referral.code_updated',
                         f'✅ <b>Реферальный код обновлен!</b>\n\n'
                         f'Ваш новый код: <code>{code}</code>\n\n'
                         f'Используйте его для приглашения друзей!'),
                reply_markup=get_back_to_settings_keyboard(i18n)
            )
            
        else:
            await message.answer(
                i18n.get('referral.update_error',
                         '❌ <b>Ошибка при обновлении!</b>\n\n'
                         'Не удалось обновить реферальный код.\n'
                         'Попробуйте еще раз позже.'),
                reply_markup=get_cancel_keyboard(i18n)
            )
    
    except Exception as e:
        print(f"Ошибка при обновлении реферального кода: {e}")
        await message.answer(
            i18n.get('referral.system_error',
                     '❌ <b>Системная ошибка!</b>\n\n'
                     'Произошла ошибка при обновлении реферального кода.\n'
                     'Попробуйте еще раз позже.'),
            reply_markup=get_cancel_keyboard(i18n)
        )


async def handle_referrer_code_input(message: Message, state: FSMContext, session, i18n, user, **_):
    """Обрабатывает ввод реферального кода пригласившего пользователя"""
    
    code = message.text.strip().upper()
    
    # Проверяем формат кода
    if not validate_referral_code(code):
        await message.answer(
            i18n.get('referral.invalid_format',
                     '❌ <b>Неверный формат кода!</b>\n\n'
                     'Код должен быть 8 символов и содержать только заглавные буквы и цифры.\n'
                     'Пример: <code>ABC12345</code>\n\n'
                     'Попробуйте еще раз или нажмите "Отмена"'),
            reply_markup=get_cancel_keyboard(i18n)
        )
        return
    
    # Проверяем, не пытается ли пользователь использовать свой код
    if code == user.referral_code:
        await message.answer(
            i18n.get('referral.self_referral',
                     '❌ <b>Нельзя использовать свой код!</b>\n\n'
                     'Введите код другого пользователя или нажмите "Отмена"'),
            reply_markup=get_cancel_keyboard(i18n)
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
            reply_markup=get_cancel_keyboard(i18n)
        )
        return
    
    # Проверяем, не пытается ли пользователь пригласить сам себя
    if referrer.id == user.id:
        await message.answer(
            i18n.get('referral.self_referral',
                     '❌ <b>Нельзя использовать свой код!</b>\n\n'
                     'Введите код другого пользователя или нажмите "Отмена"'),
            reply_markup=get_cancel_keyboard(i18n)
        )
        return
    
    # Проверяем, не пытается ли пользователь пригласить того, кто его уже пригласил
    if hasattr(referrer, 'referred_by_id') and referrer.referred_by_id == user.id:
        await message.answer(
            i18n.get('referral.circular_referral',
                     '❌ <b>Циклическая реферальная связь!</b>\n\n'
                     'Нельзя пригласить пользователя, который вас пригласил.\n'
                     'Введите другой код или нажмите "Отмена"'),
            reply_markup=get_cancel_keyboard(i18n)
        )
        return
    
    # Устанавливаем реферальную связь
    try:
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
                reply_markup=get_back_to_settings_keyboard(i18n)
            )
            
            # Уведомляем реферера (если нужно)
            # TODO: Добавить уведомление реферера о новом реферале
            
        else:
            await message.answer(
                i18n.get('referral.update_error',
                         '❌ <b>Ошибка при обновлении!</b>\n\n'
                         'Не удалось установить реферальную связь.\n'
                         'Попробуйте еще раз позже.'),
                reply_markup=get_cancel_keyboard(i18n)
            )
    
    except Exception as e:
        print(f"Ошибка при установке реферальной связи: {e}")
        await message.answer(
            i18n.get('referral.system_error',
                     '❌ <b>Системная ошибка!</b>\n\n'
                     'Произошла ошибка при установке реферальной связи.\n'
                     'Попробуйте еще раз позже.'),
            reply_markup=get_cancel_keyboard(i18n)
        )


async def cancel_referral_input(callback: CallbackQuery, state: FSMContext, i18n, **_):
    """Отменяет ввод реферального кода"""
    
    await state.clear()
    
    await callback.message.edit_text(
        i18n.get('referral.cancelled',
                 '❌ <b>Ввод реферального кода отменен</b>\n\n'
                 'Вы можете попробовать позже в настройках.'),
        reply_markup=get_back_to_settings_keyboard(i18n)
    )
    
    await callback.answer()


async def back_to_settings(callback: CallbackQuery, i18n, **_):
    """Возвращает к настройкам"""
    
    await callback.message.edit_text(
        i18n.get('settings.title', '⚙️ <b>Настройки</b>'),
        reply_markup=get_settings_keyboard(i18n)
    )
    
    await callback.answer()


def get_cancel_keyboard(i18n):
    """Создает клавиатуру с кнопкой отмены"""
    builder = InlineKeyboardBuilder()
    builder.button(
        text=i18n.get('common.cancel', '❌ Отмена'),
        callback_data="cancel_referral_input"
    )
    return builder.as_markup()


def get_back_to_settings_keyboard(i18n):
    """Создает клавиатуру для возврата к настройкам"""
    builder = InlineKeyboardBuilder()
    builder.button(
        text=i18n.get('common.back_to_settings', '🔙 Назад к настройкам'),
        callback_data="back_to_settings"
    )
    return builder.as_markup()


def register_referral_input_handlers(router: Router):
    """Регистрирует обработчики для ввода реферального кода"""
    
    # Начало обновления реферального кода
    router.callback_query.register(
        start_referral_input,
        F.data == "update_referral_code"
    )
    
    # Начало ввода реферального кода пригласившего пользователя
    router.callback_query.register(
        start_referrer_input,
        F.data == "input_referrer_code"
    )
    
    # Обработка обновления кода
    router.message.register(
        handle_referral_code_input,
        StateFilter(ReferralInputStates.waiting_for_code)
    )
    
    # Обработка ввода кода реферера
    router.message.register(
        handle_referrer_code_input,
        StateFilter(ReferralInputStates.waiting_for_referrer_code)
    )
    
    # Отмена ввода
    router.callback_query.register(
        cancel_referral_input,
        F.data == "cancel_referral_input"
    )
    
    # Возврат к настройкам
    router.callback_query.register(
        back_to_settings,
        F.data == "back_to_settings"
    ) 
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from bot.services.crud.user import get_user_by_telegram_id, get_or_create_user, update_user
from bot.middlewares.i18n import I18nMiddleware
from bot.keyboards.inline.language import get_language_keyboard
from bot.keyboards.reply.main_menu import get_main_menu


async def start_handler(
    message: Message,
    state: FSMContext,
    session,
    i18n,
    locale
):
    telegram_id = message.from_user.id
    full_name = message.from_user.full_name
    username = message.from_user.username

    # Проверяем, есть ли реферальный код в команде
    ref_code = None
    if message.text and len(message.text.split()) > 1:
        ref_code = message.text.split()[1].upper()

    user = await get_user_by_telegram_id(session, telegram_id)

    if user is None:
        # Новый пользователь — создаём и показываем EN текст + выбор языка
        user = await get_or_create_user(
            session=session,
            telegram_id=telegram_id,
            full_name=full_name,
            username=username,
            ref_code=ref_code,
            default_lang='en',
        )

        en_texts = I18nMiddleware().translations.get("en", {})
        welcome_text = en_texts.get("welcome", "Welcome, {name}!").format(name=user.name or full_name)
        
        # Добавляем информацию о реферальном коде, если он был использован
        if ref_code and user.referred_by:
            welcome_text += f"\n\n🎫 {en_texts.get('start.referral_used', 'Referral code used')}: {ref_code}"
        elif ref_code and not user.referred_by:
            welcome_text += f"\n\n❌ {en_texts.get('start.referral_invalid', 'Invalid referral code')}: {ref_code}"

        msg = await message.answer(welcome_text, reply_markup=get_language_keyboard())

        # Сохраняем ID сообщения, чтобы потом удалить при смене языка
        await state.update_data(welcome_msg_id=msg.message_id)
    else:
        # Уже зарегистрирован — приветствие на его языке + reply-клава
        lang = user.language or "ru"
        translations = I18nMiddleware().translations.get(lang, {})
        welcome_text = translations.get("welcome", "Привет, {name}!").format(name=user.name or full_name)
        
        # Если пользователь уже зарегистрирован, но передан реферальный код
        if ref_code and not user.referred_by:
            # Пытаемся применить реферальный код
            old_user = user
            user = await get_or_create_user(
                session=session,
                telegram_id=telegram_id,
                full_name=full_name,
                username=username,
                ref_code=ref_code,
                default_lang=user.language or 'ru',
            )
            
            if user.referred_by == ref_code:
                welcome_text += f"\n\n🎫 {translations.get('start.referral_applied', 'Реферальный код применен')}: {ref_code}"
            else:
                welcome_text += f"\n\n❌ {translations.get('start.referral_invalid', 'Неверный реферальный код')}: {ref_code}"
        
        reply_markup = get_main_menu(translations)
        await message.answer(welcome_text, reply_markup=reply_markup)


async def language_callback_handler(
    callback: CallbackQuery,
    state: FSMContext,
    session,
    i18n,
    locale,
    user,
    redis=None
):
    data = callback.data
    if not data.startswith("set_lang:"):
        return

    lang = data.split(":")[1]
    
    # Обновляем пользователя и очищаем кэш
    from bot.services.crud.user import update_user_with_cache_clear
    updated_user = await update_user_with_cache_clear(session, user.id, redis, language=lang)

    translations = I18nMiddleware().translations.get(lang, {})
    welcome_text = translations.get("welcome", "Привет, {name}!").format(name=user.name or callback.from_user.full_name)
    alert_text = translations.get("language_set", "Language updated successfully!")

    # Удаляем старое сообщение с приветствием и языковой клавой
    state_data = await state.get_data()
    msg_id = state_data.get("welcome_msg_id")
    chat_id = callback.message.chat.id
    
    print(f"🔍 Попытка удаления сообщения:")
    print(f"   Chat ID: {chat_id}")
    print(f"   Message ID: {msg_id}")
    print(f"   Current message ID: {callback.message.message_id}")
    
    if msg_id:
        try:
            await callback.message.bot.delete_message(chat_id, msg_id)
            print(f"✅ Сообщение {msg_id} успешно удалено")
        except Exception as e:
            print(f"❌ Ошибка при удалении сообщения {msg_id}: {e}")
            # Попробуем удалить текущее сообщение с клавиатурой
            try:
                await callback.message.delete()
                print("✅ Текущее сообщение с клавиатурой удалено")
            except Exception as e2:
                print(f"❌ Не удалось удалить текущее сообщение: {e2}")
    else:
        print("⚠️ ID сообщения не найден в состоянии, удаляем текущее сообщение")
        try:
            await callback.message.delete()
            print("✅ Текущее сообщение с клавиатурой удалено")
        except Exception as e:
            print(f"❌ Не удалось удалить текущее сообщение: {e}")

    # Отправляем новое приветствие с reply-клавиатурой
    reply_markup = get_main_menu(translations)
    await callback.message.answer(welcome_text, reply_markup=reply_markup)
    await callback.answer(alert_text, show_alert=True)


def register_start_handler(router):
    router.message.register(start_handler, Command("start"))
    router.callback_query.register(language_callback_handler, lambda c: c.data.startswith("set_lang:"))

__all__ = ["register_start_handler"]

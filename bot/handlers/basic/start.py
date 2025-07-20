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

    user = await get_user_by_telegram_id(session, telegram_id)

    if user is None:
        # Новый пользователь — создаём и показываем EN текст + выбор языка
        user = await get_or_create_user(
            session=session,
            telegram_id=telegram_id,
            full_name=full_name,
            username=username,
            ref_code=None,
            default_lang='en',
        )

        en_texts = I18nMiddleware().translations["en"]
        welcome_text = en_texts.get("welcome", "Welcome, {name}!").format(name=user.name or full_name)

        msg = await message.answer(welcome_text, reply_markup=get_language_keyboard())

        # Сохраняем ID сообщения, чтобы потом удалить при смене языка
        await state.update_data(welcome_msg_id=msg.message_id)
    else:
        # Уже зарегистрирован — приветствие на его языке + reply-клава
        lang = user.language or "ru"
        translations = I18nMiddleware().translations.get(lang, {})
        welcome_text = translations.get("welcome", "Привет, {name}!").format(name=user.name or full_name)
        reply_markup = get_main_menu(translations)

        await message.answer(welcome_text, reply_markup=reply_markup)


async def language_callback_handler(
    callback: CallbackQuery,
    state: FSMContext,
    session,
    i18n,
    locale,
    user
):
    data = callback.data
    if not data.startswith("set_lang:"):
        return

    lang = data.split(":")[1]
    await update_user(session, user.id, language=lang)

    translations = I18nMiddleware().translations.get(lang, {})
    welcome_text = translations.get("welcome", "Привет, {name}!").format(name=user.name or callback.from_user.full_name)
    alert_text = translations.get("language_set", "Language updated successfully!")

    # Удаляем старое сообщение с приветствием и языковой клавой
    state_data = await state.get_data()
    msg_id = state_data.get("welcome_msg_id")
    if msg_id:
        try:
            await callback.message.bot.delete_message(callback.message.chat.id, msg_id)
        except Exception:
            pass  # сообщение могло быть удалено вручную

    # Отправляем новое приветствие с reply-клавиатурой
    reply_markup = get_main_menu(translations)
    await callback.message.answer(welcome_text, reply_markup=reply_markup)
    await callback.answer(alert_text, show_alert=True)


def register_start_handler(router):
    router.message.register(start_handler, Command("start"))
    router.callback_query.register(language_callback_handler, lambda c: c.data.startswith("set_lang:"))

__all__ = ["register_start_handler"]

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.markdown import hbold

from bot.keyboards.inline.socials import get_platforms_keyboard, get_confirm_admin_keyboard
from bot.services.crud.socials import create_social_account

TELEGRAM_PLATFORM = "telegram"

router = Router()

class AddTelegramChannelStates(StatesGroup):
    waiting_admin_confirmation = State()
    waiting_forward = State()

async def choose_platform_handler(callback: CallbackQuery, i18n):
    await callback.answer()
    await callback.message.delete()
    await callback.message.answer(
        i18n.get("accounts.choose_platform", "📲 Choose a platform:"),
        reply_markup=get_platforms_keyboard(i18n)
    )


async def add_social_callback_handler(callback: CallbackQuery, state: FSMContext, i18n, **_):
    await callback.answer()
    await callback.message.delete()
    await callback.message.answer(
        i18n.get("accounts.telegram.instruction"),
        reply_markup=get_confirm_admin_keyboard(i18n),
        parse_mode="HTML"
    )
    await state.set_state(AddTelegramChannelStates.waiting_admin_confirmation)


async def confirm_admin_handler(callback: CallbackQuery, state: FSMContext, i18n):
    await callback.answer()
    await callback.message.delete()
    msg = await callback.message.answer(
        i18n.get("accounts.telegram.forward_request", "📨 Now, please forward any message from your channel."),
        parse_mode="HTML"
    )
    await state.update_data(instruction_msg_id=msg.message_id)
    await state.set_state(AddTelegramChannelStates.waiting_forward)


async def process_forwarded_channel(message: Message, state: FSMContext, session, i18n, user, **_):
    if not message.forward_from_chat or message.forward_from_chat.type != "channel":
        await message.answer(i18n.get("accounts.telegram.not_channel"))
        return

    data = await state.get_data()
    instruction_msg_id = data.get("instruction_msg_id")

    # Удаляем инструкцию
    if instruction_msg_id:
        try:
            await message.bot.delete_message(chat_id=message.chat.id, message_id=instruction_msg_id)
        except Exception:
            pass

    # Удаляем пересланное сообщение
    try:
        await message.delete()
    except Exception:
        pass

    channel = message.forward_from_chat
    channel_id = str(channel.id)
    channel_name = channel.title or "Unnamed"

    try:
        await create_social_account(
            session=session,
            user_id=user.id,
            platform=TELEGRAM_PLATFORM,
            channel_name=channel_name,
            channel_id=channel_id,
            channel_type=channel.type,
            telegram_chat_id=channel_id,
        )
    except Exception:
        await message.answer(i18n.get("accounts.telegram.error_saving"))
        await state.clear()
        return

    await message.answer(
        i18n.get("accounts.telegram.success").format(name=hbold(channel_name)),
        parse_mode="HTML"
    )
    await state.clear()


def register_add_social_handlers(router: Router):
    router.callback_query.register(choose_platform_handler, F.data == "accounts:add")
    router.callback_query.register(add_social_callback_handler, F.data == "add:telegram")
    router.callback_query.register(confirm_admin_handler, F.data == "add:telegram:confirm")
    router.message.register(process_forwarded_channel, AddTelegramChannelStates.waiting_forward)

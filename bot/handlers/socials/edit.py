from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.utils.markdown import hbold

from bot.services.crud.socials import get_social_account_by_id, update_social_account, delete_social_account
from bot.keyboards.inline.socials import get_manage_account_keyboard

router = Router()

class ManageAccountStates(StatesGroup):
    editing_name = State()


async def view_account_handler(callback: CallbackQuery, i18n, session, **_):
    await callback.answer()
    account_id = int(callback.data.split(":")[-1])
    account = await get_social_account_by_id(session, account_id)

    if not account:
        await callback.message.edit_text(i18n.get("accounts.not_found"))
        return

    text = (
        f"🔗 <b>{hbold(account.channel_name)}</b>\n"
        f"🌐 <b>Platform:</b> {account.platform.upper()}\n"
        f"🆔 <b>Channel ID:</b> <code>{account.channel_id}</code>"
    )
    await callback.message.edit_text(
        text,
        reply_markup=get_manage_account_keyboard(i18n, account.id),
        parse_mode="HTML"
    )


async def edit_account_name_handler(callback: CallbackQuery, state: FSMContext, i18n):
    await callback.answer()
    account_id = int(callback.data.split(":")[-1])

    try:
        await callback.message.delete()
    except:
        pass

    instruction_msg = await callback.message.answer(
        i18n.get("accounts.edit_name", "✏️ Введите новое имя для аккаунта:")
    )

    await state.set_state(ManageAccountStates.editing_name)
    await state.update_data(
        account_id=account_id,
        instruction_msg_id=instruction_msg.message_id,
    )



async def process_new_account_name(message: Message, state: FSMContext, session, i18n, **_):
    data = await state.get_data()
    account_id = data.get("account_id")
    new_name = message.text.strip()

    if len(new_name) < 2:
        await message.answer(i18n.get("accounts.manage.rename_too_short", "⚠️ Name is too short."))
        return

    await update_social_account(session, account_id, channel_name=new_name)

    try:
        await message.delete()
        instruction_msg_id = data.get("instruction_msg_id")
        if instruction_msg_id:
            await message.bot.delete_message(message.chat.id, instruction_msg_id)
    except Exception:
        pass

    await message.answer(i18n.get("accounts.name_updated", "✅ Account name updated."))
    await state.clear()


async def delete_account_handler(callback: CallbackQuery, session, i18n):
    await callback.answer()
    account_id = int(callback.data.split(":")[-1])
    await delete_social_account(session, account_id)
    await callback.message.edit_text(i18n.get("accounts.deleted"))


def register_manage_account_handlers(router: Router):
    router.callback_query.register(view_account_handler, F.data.startswith("accounts:view:"))
    router.callback_query.register(edit_account_name_handler, F.data.startswith("accounts:edit:"))
    router.callback_query.register(delete_account_handler, F.data.startswith("accounts:delete:"))
    router.message.register(process_new_account_name, ManageAccountStates.editing_name)
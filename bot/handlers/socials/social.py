from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram import F, Router

from bot.keyboards.inline.socials import get_accounts_keyboard
from bot.services.crud.socials import get_social_accounts_by_user_id

router = Router()


async def social_accounts_handler(message: Message, session, i18n, user, **_):
    accounts = await get_social_accounts_by_user_id(session, user.id)

    if not accounts:
        await message.answer(
            i18n.get("accounts.none"),
            reply_markup=get_accounts_keyboard(i18n, [])
        )
        return

    lines = [
        f"🔗 <b>{acc.channel_name or '-'}</b> ({acc.platform.upper() if acc.platform else '-'})"
        for acc in accounts
    ]

    text = i18n.get("accounts.list") + "\n\n" + "\n".join(lines)

    await message.answer(
        text,
        reply_markup=get_accounts_keyboard(i18n, accounts),
        parse_mode="HTML"
    )


async def social_accounts_back_handler(callback: CallbackQuery, session, i18n, user, **_):
    await callback.answer()
    accounts = await get_social_accounts_by_user_id(session, user.id)

    if not accounts:
        await callback.message.edit_text(
            i18n.get("accounts.none"),
            reply_markup=get_accounts_keyboard(i18n, [])
        )
        return

    lines = [
        f"🔗 <b>{acc.channel_name or '-'}</b> ({acc.platform.upper() if acc.platform else '-'})"
        for acc in accounts
    ]
    text = i18n.get("accounts.list") + "\n\n" + "\n".join(lines)

    await callback.message.edit_text(
        text,
        reply_markup=get_accounts_keyboard(i18n, accounts),
        parse_mode="HTML"
    )


def register_social_accounts_handler(router: Router):
    router.message.register(social_accounts_handler, Command("accounts"))
    router.message.register(social_accounts_handler, F.text.lower().contains("accounts"))
    router.message.register(social_accounts_handler, F.text.lower().contains("аккаунт"))
    router.callback_query.register(social_accounts_back_handler, F.data == "accounts:back")

from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram import F, Router

from bot.keyboards.inline.workflows import get_workflows_keyboard
from bot.services.crud.workflow import get_user_workflows_by_user_id

router = Router()


async def workflows_handler(message: Message, session, i18n, user, **_):
    workflows = await get_user_workflows_by_user_id(session, user.id)

    if not workflows:
        await message.answer(
            i18n.get("workflow.none", "📋 У вас пока нет задач."),
            reply_markup=get_workflows_keyboard(i18n, [])
        )
        return

    lines = [
        f"📌 <b>{wf.name}</b> — {wf.status.upper()}"
        for wf in workflows
    ]

    text = i18n.get("workflow.list", "📋 Ваши задачи:") + "\n\n" + "\n".join(lines)

    await message.answer(
        text,
        reply_markup=get_workflows_keyboard(i18n, workflows),
        parse_mode="HTML"
    )


async def workflows_back_handler(callback: CallbackQuery, session, i18n, user, **_):
    await callback.answer()
    workflows = await get_user_workflows_by_user_id(session, user.id)

    if not workflows:
        await callback.message.edit_text(
            i18n.get("workflow.none", "📋 У вас пока нет задач."),
            reply_markup=get_workflows_keyboard(i18n, [])
        )
        return

    lines = [
        f"📌 <b>{wf.name}</b> — {wf.status.upper()}"
        for wf in workflows
    ]

    text = i18n.get("workflow.list", "📋 Ваши задачи:") + "\n\n" + "\n".join(lines)

    await callback.message.edit_text(
        text,
        reply_markup=get_workflows_keyboard(i18n, workflows),
        parse_mode="HTML"
    )


def register_workflows_handler(router: Router):
    router.message.register(workflows_handler, Command("workflows"))
    router.message.register(workflows_handler, F.text.lower().contains("workflow"))
    router.message.register(workflows_handler, F.text.lower().contains("задач"))
    router.callback_query.register(workflows_back_handler, F.data == "workflows:back")

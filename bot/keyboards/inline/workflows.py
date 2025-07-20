from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.models.models import UserWorkflow

def get_workflows_keyboard(workflows: list[UserWorkflow], i18n: dict) -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(text=wf.name, callback_data=f"workflow:{wf.id}")]
        for wf in workflows
    ]
    keyboard.append([
        InlineKeyboardButton(text=i18n["workflow.add"], callback_data="workflow:add")
    ])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_post_actions_keyboard(post_id: int, i18n: dict) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=i18n["post.edit"], callback_data=f"post:edit:{post_id}"),
            InlineKeyboardButton(text=i18n["post.delete"], callback_data=f"post:delete:{post_id}")
        ],
        [
            InlineKeyboardButton(text=i18n["post.publish"], callback_data=f"post:publish:{post_id}")
        ]
    ])

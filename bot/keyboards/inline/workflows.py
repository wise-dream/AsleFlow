from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from bot.models.models import UserWorkflow

def get_workflows_keyboard(i18n: dict, workflows: list[UserWorkflow]) -> InlineKeyboardMarkup:
    keyboard = []

    for wf in workflows:
        status = wf.status.upper()
        button = InlineKeyboardButton(
            text=f"{wf.name} ({status})",
            callback_data=f"workflow:view:{wf.id}"
        )
        keyboard.append([button])

    keyboard.append([
        InlineKeyboardButton(
            text=i18n.get("workflow.button.add", "➕ Добавить задачу"),
            callback_data="workflow:add"
        )
    ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_account_selection_keyboard(accounts) -> InlineKeyboardBuilder:
    kb = InlineKeyboardBuilder()
    for acc in accounts:
        text = f"{acc.channel_name or '-'} ({acc.platform.upper()})"
        kb.button(
            text=text,
            callback_data=f"workflow:account:{acc.id}"
        )
    kb.adjust(1)
    return kb.as_markup()


def get_theme_selection_keyboard(i18n) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    # Основные тематики
    kb.button(text=i18n.get("workflow.theme.finance"), callback_data="theme:финансы")
    kb.button(text=i18n.get("workflow.theme.marketing"), callback_data="theme:маркетинг")
    kb.button(text=i18n.get("workflow.theme.tech"), callback_data="theme:технологии")
    kb.button(text=i18n.get("workflow.theme.psychology"), callback_data="theme:психология")
    kb.button(text=i18n.get("workflow.theme.health"), callback_data="theme:здоровье")
    kb.button(text=i18n.get("workflow.theme.education"), callback_data="theme:образование")
    kb.button(text=i18n.get("workflow.theme.sports"), callback_data="theme:спорт")
    kb.button(text=i18n.get("workflow.theme.travel"), callback_data="theme:путешествия")
    kb.button(text=i18n.get("workflow.theme.food"), callback_data="theme:еда")
    kb.button(text=i18n.get("workflow.theme.fashion"), callback_data="theme:мода")
    kb.button(text=i18n.get("workflow.theme.entertainment"), callback_data="theme:развлечения")
    kb.button(text=i18n.get("workflow.theme.business"), callback_data="theme:бизнес")
    kb.button(text=i18n.get("workflow.theme.lifestyle"), callback_data="theme:образ_жизни")
    # Кнопка для ввода своей тематики
    kb.button(text=i18n.get("workflow.theme.custom"), callback_data="theme:custom")
    kb.adjust(3)
    return kb.as_markup()


def get_media_type_keyboard(i18n) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text=i18n.get("workflow.media.text"), callback_data="media:text")
    kb.button(text=i18n.get("workflow.media.image"), callback_data="media:image")
    kb.button(text=i18n.get("workflow.media.video"), callback_data="media:video")
    kb.adjust(3)
    return kb.as_markup()


def get_language_selection_keyboard(i18n) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="🇷🇺 Русский", callback_data="lang:ru")
    kb.button(text="🇬🇧 English", callback_data="lang:en")
    kb.adjust(2)
    return kb.as_markup()

def get_style_selection_keyboard(i18n) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text=i18n.get("workflow.style.formal"), callback_data="style:formal")
    kb.button(text=i18n.get("workflow.style.friendly"), callback_data="style:friendly")
    kb.button(text=i18n.get("workflow.style.humorous"), callback_data="style:humorous")
    kb.adjust(1)
    return kb.as_markup()

def get_time_selection_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    # Кнопка "Сейчас"
    kb.button(text="🚀 Сейчас", callback_data="time:now")
    for hour in range(0, 24):  # теперь до 23:30 включительно
        kb.button(text=f"{hour:02d}:00", callback_data=f"time:{hour:02d}:00")
        kb.button(text=f"{hour:02d}:30", callback_data=f"time:{hour:02d}:30")
    kb.adjust(2)
    return kb.as_markup()

def get_style_selection_keyboard(i18n) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text=i18n.get("workflow.style.formal"), callback_data="style:formal")
    kb.button(text=i18n.get("workflow.style.informal"), callback_data="style:informal")
    kb.button(text=i18n.get("workflow.style.friendly"), callback_data="style:friendly")
    kb.adjust(1)
    return kb.as_markup()

def get_edit_workflow_keyboard(
    workflow_id: int,
    i18n: dict,
    moderation_enabled: bool = True,
    is_active: bool = True
) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()


    moderation_text = (
        i18n.get("workflow.edit.moderation_on", "✅ Модерация включена")
        if moderation_enabled else
        i18n.get("workflow.edit.moderation_off", "🚫 Модерация выключена")
    )
    kb.button(
        text=moderation_text,
        callback_data=f"workflow:edit:moderation:{workflow_id}"
    )

    status_text = (
        i18n.get("workflow.edit.active", "🟢 Задача включена")
        if is_active else
        i18n.get("workflow.edit.inactive", "⚪️ Задача выключена")
    )
    status_text = status_text.upper()  # всегда капсом
    kb.button(
        text=status_text,
        callback_data=f"workflow:edit:toggle:{workflow_id}"
    )

    kb.button(
        text=i18n.get("workflow.edit.name", "✏️ Название"),
        callback_data=f"workflow:edit:name:{workflow_id}"
    )
    kb.button(
        text=i18n.get("workflow.edit.theme", "🎯 Тема"),
        callback_data=f"workflow:edit:theme:{workflow_id}"
    )
    kb.button(
        text=i18n.get("workflow.edit.time", "⏰ Время"),
        callback_data=f"workflow:edit:time:{workflow_id}"
    )
    kb.button(
        text=i18n.get("workflow.edit.interval", "⏱️ Интервал"),
        callback_data=f"workflow:edit:interval:{workflow_id}"
    )
    kb.button(
        text=i18n.get("workflow.edit.language", "🌍 Язык"),
        callback_data=f"workflow:edit:lang:{workflow_id}"
    )
    kb.button(
        text=i18n.get("workflow.edit.style", "📝 Стиль"),
        callback_data=f"workflow:edit:style:{workflow_id}"
    )

    kb.button(
        text=i18n.get("common.back", "⬅️ Назад"),
        callback_data="workflows:back"
    )

    # Кнопка удаления
    kb.button(
        text=i18n.get("workflow.edit.delete", "🗑 Удалить"),
        callback_data=f"workflow:delete:{workflow_id}"
    )


    kb.adjust(2)
    return kb.as_markup()

def get_moderation_keyboard(i18n: dict) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text=i18n.get("workflow.moderation.on", "✅ С модерацией"), callback_data="moderation:on")
    kb.button(text=i18n.get("workflow.moderation.off", "🚫 Без модерации"), callback_data="moderation:off")
    kb.adjust(1)
    return kb.as_markup()


def get_content_length_keyboard(i18n: dict) -> InlineKeyboardMarkup:
    """Клавиатура выбора длины контента"""
    kb = InlineKeyboardBuilder()
    
    # Короткий контент (до 50 слов)
    kb.button(
        text=i18n.get("workflow.length.short", "📝 Короткий (до 50 слов)"), 
        callback_data="length:short"
    )
    
    # Средний контент (до 100 слов)  
    kb.button(
        text=i18n.get("workflow.length.medium", "📄 Средний (до 100 слов)"),
        callback_data="length:medium"
    )
    
    # Большой контент (100+ слов)
    kb.button(
        text=i18n.get("workflow.length.long", "📖 Большой (100+ слов)"),
        callback_data="length:long"
    )
    
    kb.adjust(1)
    return kb.as_markup()

def get_interval_keyboard(i18n: dict) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    # Интервалы с учетом ограничения 4-168 часов
    intervals = [4, 8, 12, 16, 20, 24, 36, 48]
    
    for interval in intervals:
        # Показываем часы с подписью 
        hours_text = f"{interval}ч" if i18n.get("language") == "ru" else f"{interval}h"
        kb.button(text=hours_text, callback_data=f"interval:{interval}")
    
    # Кнопка для ввода своего интервала
    kb.button(text=i18n.get("workflow.add.interval_custom", "✍️ Ввести свой интервал"), callback_data="interval:custom")
    
    kb.adjust(4)  # 4 кнопки в ряд
    return kb.as_markup()
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from bot.models.models import Post
from aiogram.utils.keyboard import InlineKeyboardBuilder

def get_posts_keyboard(i18n: dict, posts: list[Post]) -> InlineKeyboardMarkup:
    """Клавиатура со списком постов"""
    keyboard = []

    for post in posts:
        # Иконка статуса
        status_icon = {
            'pending': '⏳',
            'scheduled': '📅', 
            'published': '✅',
            'failed': '❌'
        }.get(post.status, '❓')
        
        button = InlineKeyboardButton(
            text=f"{status_icon} {post.topic[:40]}{'...' if len(post.topic) > 40 else ''}",
            callback_data=f"post:view:{post.id}"
        )
        keyboard.append([button])

    # Кнопки управления
    keyboard.append([
        InlineKeyboardButton(
            text=i18n.get("post.button.add", "➕ Создать пост"),
            callback_data="post:add"
        )
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_post_actions_keyboard(post_id: int, i18n: dict, post_status: str = "pending") -> InlineKeyboardMarkup:
    """Клавиатура с действиями для поста"""
    kb = InlineKeyboardBuilder()
    
    # Редактировать (если пост не опубликован)
    if post_status != "published":
        kb.button(
            text=i18n.get("post.edit", "✏️ Редактировать"),
            callback_data=f"post:edit:{post_id}"
        )
    
    # Опубликовать (если пост pending или failed)
    if post_status in ["pending", "failed"]:
        kb.button(
            text=i18n.get("post.publish", "✅ Опубликовать"),
            callback_data=f"post:publish:{post_id}"
        )
    
    # Удалить
    kb.button(
        text=i18n.get("post.delete", "🗑 Удалить"),
        callback_data=f"post:delete:{post_id}"
    )
    
    # Назад к списку
    kb.button(
        text=i18n.get("common.back", "⬅️ Назад"),
        callback_data="posts:back"
    )
    
    kb.adjust(2)
    return kb.as_markup()


def get_post_filter_keyboard(i18n: dict) -> InlineKeyboardMarkup:
    """Клавиатура фильтров постов"""
    kb = InlineKeyboardBuilder()
    
    kb.button(text=i18n.get("post.filter.all", "📋 Все"), callback_data="posts:filter:all")
    kb.button(text=i18n.get("post.filter.pending", "⏳ Ожидание"), callback_data="posts:filter:pending")
    kb.button(text=i18n.get("post.filter.scheduled", "📅 Запланированы"), callback_data="posts:filter:scheduled") 
    kb.button(text=i18n.get("post.filter.published", "✅ Опубликованы"), callback_data="posts:filter:published")
    
    kb.adjust(2)
    return kb.as_markup()


def get_post_creation_method_keyboard(i18n: dict) -> InlineKeyboardMarkup:
    """Клавиатура выбора способа создания поста"""
    kb = InlineKeyboardBuilder()
    
    kb.button(
        text=i18n.get("post.add.with_workflow", "🧠 С помощью задачи"),
        callback_data="post:add:workflow"
    )
    kb.button(
        text=i18n.get("post.add.from_scratch", "🆕 С нуля"),
        callback_data="post:add:manual"
    )
    kb.button(
        text=i18n.get("common.back", "⬅️ Назад"),
        callback_data="posts:back"
    )
    
    kb.adjust(1)
    return kb.as_markup()


def get_user_workflows_selection_keyboard(i18n: dict, workflows: list) -> InlineKeyboardMarkup:
    """Клавиатура выбора задачи для создания поста"""
    kb = InlineKeyboardBuilder()
    if not workflows:
        kb.button(text=i18n.get("post.add.no_workflows", "❌ Нет задач"), callback_data="noop")
    else:
        for wf in workflows:
            name = getattr(wf, 'name', '—')
            kb.button(
                text=name,
                callback_data=f"post:add:use_workflow:{wf.id}"
            )
    kb.button(text=i18n.get("common.back", "⬅️ Назад"), callback_data="posts:back")
    kb.adjust(1)
    return kb.as_markup()


def get_prompt_templates_keyboard(i18n: dict, templates: list, include_default: bool = True) -> InlineKeyboardMarkup:
    """Клавиатура выбора шаблона промпта"""
    kb = InlineKeyboardBuilder()
    if include_default:
        kb.button(text=i18n.get("prompt.use_default", "🧩 По умолчанию"), callback_data="prompt:default")
    for t in templates[:20]:
        kb.button(
            text=f"{getattr(t, 'name', 'Template')}",
            callback_data=f"prompt:select:{t.id}"
        )
    kb.button(text=i18n.get("common.back", "⬅️ Назад"), callback_data="posts:back")
    kb.adjust(1)
    return kb.as_markup()

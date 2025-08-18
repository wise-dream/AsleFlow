from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from bot.models.models import PromptTemplate
import json

ALLOWED_FIELDS = {
    "name", "description", "template_text",
    "is_system", "is_active", "default_temperature", "max_tokens"
}


async def create_prompt_template(session: AsyncSession, **kwargs) -> PromptTemplate:
    """Создает новый шаблон промпта"""
    template = PromptTemplate(**kwargs)
    session.add(template)
    await session.commit()
    await session.refresh(template)
    return template


async def get_prompt_template_by_id(session: AsyncSession, template_id: int) -> PromptTemplate | None:
    """Получает шаблон промпта по ID"""
    result = await session.execute(select(PromptTemplate).where(PromptTemplate.id == template_id))
    return result.scalar_one_or_none()


async def get_all_prompt_templates(session: AsyncSession, active_only: bool = True) -> list[PromptTemplate]:
    """Получает все шаблоны промптов"""
    query = select(PromptTemplate)
    if active_only:
        query = query.where(PromptTemplate.is_active == True)
    result = await session.execute(query)
    return result.scalars().all()


# Удалено: фильтрация по prompt_type не используется


async def get_system_prompt_templates(session: AsyncSession) -> list[PromptTemplate]:
    """Получает системные шаблоны промптов"""
    result = await session.execute(
        select(PromptTemplate).where(
            PromptTemplate.is_system == True,
            PromptTemplate.is_active == True
        )
    )
    return result.scalars().all()


async def update_prompt_template(session: AsyncSession, template_id: int, **kwargs) -> PromptTemplate | None:
    """Обновляет шаблон промпта"""
    template = await get_prompt_template_by_id(session, template_id)
    if not template:
        return None
    
    for key, value in kwargs.items():
        if key in ALLOWED_FIELDS:
            setattr(template, key, value)
    
    await session.commit()
    await session.refresh(template)
    return template


async def delete_prompt_template(session: AsyncSession, template_id: int) -> bool:
    """Удаляет шаблон промпта (только пользовательские)"""
    template = await get_prompt_template_by_id(session, template_id)
    if not template or template.is_system:
        return False
    
    await session.delete(template)
    await session.commit()
    return True


async def render_prompt_template(template: PromptTemplate, variables: dict) -> str:
    """Рендерит шаблон промпта с переменными"""
    try:
        rendered = template.template_text
        for key, value in variables.items():
            placeholder = f"{{{key}}}"
            rendered = rendered.replace(placeholder, str(value))
        return rendered
    except Exception:
        return template.template_text


# Упразднено: переменные больше не хранятся в шаблоне, плейсхолдеры формируются динамически
async def get_template_variables(template: PromptTemplate) -> dict:
    return {}


async def create_default_templates(session: AsyncSession) -> list[PromptTemplate]:
    """Создает стандартные системные шаблоны промптов"""
    default_templates = [
        {
            "name": "Базовый шаблон",
            "description": "Шаблон, учитывающий тематику и описание ситуации пользователя.",
            "template_text": (
                "Сгенерируй качественный пост для соцсетей.\n"
                "Тема: '{topic}'.\n"
                "Контекст: '{context}'.\n"
                "Цель: дать полезную ценность, удержать внимание и подтолкнуть к взаимодействию.\n"
                "Ограничения: избегай воды, пиши конкретно, используй подзаголовки/списки при необходимости.\n"
                "Стиль: {style}. Длина: {length}. Язык: {language}.\n"
                "Верни итоговый текст без лишних пояснений."
            ),
            "is_system": True,
            "default_temperature": 0.7,
        }
    ]
    
    created_templates = []
    for template_data in default_templates:
        # Проверяем, существует ли уже такой шаблон
        existing = await session.execute(
            select(PromptTemplate).where(
                PromptTemplate.name == template_data["name"],
                PromptTemplate.is_system == True
            )
        )
        if not existing.scalar_one_or_none():
            template = await create_prompt_template(session, **template_data)
            created_templates.append(template)
    
    return created_templates

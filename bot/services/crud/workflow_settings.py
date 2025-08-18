from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from bot.models.models import WorkflowSettings

ALLOWED_FIELDS = {
    "social_account_id", "interval_hours", "theme", "context", "writing_style",
    "generation_method", "content_length", "moderation", "first_post_time",
    "post_language", "post_media_type", "notifications_enabled", "last_execution",
    "mode",  # Новое поле для режима работы
    "prompt_template_id"  # Связанный шаблон промпта по умолчанию
}

async def create_workflow_settings(session: AsyncSession, **kwargs) -> WorkflowSettings:
    settings = WorkflowSettings(**kwargs)
    session.add(settings)
    await session.commit()
    await session.refresh(settings)
    return settings

async def get_workflow_settings_by_id(session: AsyncSession, settings_id: int) -> WorkflowSettings | None:
    result = await session.execute(select(WorkflowSettings).where(WorkflowSettings.id == settings_id))
    return result.scalar_one_or_none()

async def get_all_workflow_settings(session: AsyncSession) -> list[WorkflowSettings]:
    result = await session.execute(select(WorkflowSettings))
    return result.scalars().all()

async def update_workflow_settings(session: AsyncSession, settings_id: int, **kwargs) -> WorkflowSettings | None:
    settings = await get_workflow_settings_by_id(session, settings_id)
    if not settings:
        return None
    for key, value in kwargs.items():
        if key in ALLOWED_FIELDS:
            setattr(settings, key, value)
    await session.commit()
    await session.refresh(settings)
    return settings

async def delete_workflow_settings(session: AsyncSession, settings_id: int) -> bool:
    settings = await get_workflow_settings_by_id(session, settings_id)
    if not settings:
        return False
    await session.delete(settings)
    await session.commit()
    return True

async def get_settings_by_workflow_id(session: AsyncSession, user_workflow_id: int) -> WorkflowSettings | None:
    result = await session.execute(
        select(WorkflowSettings).where(WorkflowSettings.user_workflow_id == user_workflow_id)
    )
    return result.scalar_one_or_none()

async def toggle_moderation(session, user_id: int, workflow_id: int) -> WorkflowSettings | None:
    result = await session.execute(
        select(WorkflowSettings)
        .join(WorkflowSettings.user_workflow)
        .where(
            WorkflowSettings.user_workflow_id == workflow_id,
            WorkflowSettings.user_workflow.has(user_id=user_id)
        )
    )
    settings = result.scalar_one_or_none()
    if not settings:
        return None

    settings.moderation = "disabled" if settings.moderation == "enabled" else "enabled"
    await session.commit()
    await session.refresh(settings)
    return settings  # Возвращаем только settings, без user_workflow

async def get_settings_by_social_account_id(session: AsyncSession, social_account_id: int) -> list[WorkflowSettings]:
    result = await session.execute(
        select(WorkflowSettings).where(WorkflowSettings.social_account_id == social_account_id)
    )
    return result.scalars().all()

async def get_settings_by_theme(session: AsyncSession, theme: str) -> list[WorkflowSettings]:
    result = await session.execute(
        select(WorkflowSettings).where(WorkflowSettings.theme == theme)
    )
    return result.scalars().all()

async def get_settings_by_generation_method(session: AsyncSession, generation_method: str) -> list[WorkflowSettings]:
    result = await session.execute(
        select(WorkflowSettings).where(WorkflowSettings.generation_method == generation_method)
    )
    return result.scalars().all()

async def get_settings_by_moderation_status(session: AsyncSession, moderation: str) -> list[WorkflowSettings]:
    result = await session.execute(
        select(WorkflowSettings).where(WorkflowSettings.moderation == moderation)
    )
    return result.scalars().all()

async def update_last_execution(session: AsyncSession, settings_id: int) -> WorkflowSettings | None:
    from datetime import datetime, timezone
    settings = await get_workflow_settings_by_id(session, settings_id)
    if not settings:
        return None
    
    settings.last_execution = datetime.now(timezone.utc)
    await session.commit()
    await session.refresh(settings)
    return settings


# Новые функции для работы с режимом задачи
async def get_workflows_by_mode(session: AsyncSession, mode: str) -> list[WorkflowSettings]:
    """Получает задачи по режиму работы"""
    result = await session.execute(
        select(WorkflowSettings).where(WorkflowSettings.mode == mode)
    )
    return result.scalars().all()


async def get_auto_workflows(session: AsyncSession) -> list[WorkflowSettings]:
    """Получает автоматические задачи"""
    return await get_workflows_by_mode(session, 'auto')


async def get_manual_workflows(session: AsyncSession) -> list[WorkflowSettings]:
    """Получает ручные задачи"""
    return await get_workflows_by_mode(session, 'manual')


async def get_mixed_workflows(session: AsyncSession) -> list[WorkflowSettings]:
    """Получает смешанные задачи"""
    return await get_workflows_by_mode(session, 'mixed')


async def update_workflow_mode(session: AsyncSession, settings_id: int, mode: str) -> WorkflowSettings | None:
    """Обновляет режим работы задачи"""
    settings = await get_workflow_settings_by_id(session, settings_id)
    if not settings:
        return None
    
    settings.mode = mode
    await session.commit()
    await session.refresh(settings)
    return settings


async def get_workflows_for_manual_posts(session: AsyncSession, user_id: int = None) -> list[WorkflowSettings]:
    """Получает задачи, которые можно использовать для ручных постов"""
    query = select(WorkflowSettings).where(
        WorkflowSettings.mode.in_(['manual', 'mixed'])
    )
    
    if user_id:
        query = query.join(WorkflowSettings.user_workflow).where(
            WorkflowSettings.user_workflow.has(user_id=user_id)
        )
    
    result = await session.execute(query)
    return result.scalars().all()
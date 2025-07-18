from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from bot.models.models import WorkflowSettings

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
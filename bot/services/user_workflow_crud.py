from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from bot.models.models import UserWorkflow

async def create_user_workflow(session: AsyncSession, **kwargs) -> UserWorkflow:
    workflow = UserWorkflow(**kwargs)
    session.add(workflow)
    await session.commit()
    await session.refresh(workflow)
    return workflow

async def get_user_workflow_by_id(session: AsyncSession, workflow_id: int) -> UserWorkflow | None:
    result = await session.execute(select(UserWorkflow).where(UserWorkflow.id == workflow_id))
    return result.scalar_one_or_none()

async def get_all_user_workflows(session: AsyncSession) -> list[UserWorkflow]:
    result = await session.execute(select(UserWorkflow))
    return result.scalars().all()

async def update_user_workflow(session: AsyncSession, workflow_id: int, **kwargs) -> UserWorkflow | None:
    workflow = await get_user_workflow_by_id(session, workflow_id)
    if not workflow:
        return None
    for key, value in kwargs.items():
        setattr(workflow, key, value)
    await session.commit()
    await session.refresh(workflow)
    return workflow

async def delete_user_workflow(session: AsyncSession, workflow_id: int) -> bool:
    workflow = await get_user_workflow_by_id(session, workflow_id)
    if not workflow:
        return False
    await session.delete(workflow)
    await session.commit()
    return True 
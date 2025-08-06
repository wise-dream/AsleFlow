from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from bot.models.models import UserWorkflow

ALLOWED_FIELDS = {"user_id", "workflow_id", "name", "status"}

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
        if key in ALLOWED_FIELDS:
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

async def get_user_workflows_by_user_id(session: AsyncSession, user_id: int) -> list[UserWorkflow]:
    result = await session.execute(
        select(UserWorkflow).where(UserWorkflow.user_id == user_id)
    )
    return result.scalars().all()

async def toggle_workflow_status(session, user_id: int, workflow_id: int) -> tuple[UserWorkflow | None, str | None]:
    """
    Переключает статус задачи с проверкой лимитов подписки
    
    Returns:
        tuple: (workflow, error_message) - workflow или None, сообщение об ошибке или None
    """
    result = await session.execute(
        select(UserWorkflow).where(
            UserWorkflow.id == workflow_id,
            UserWorkflow.user_id == user_id
        )
    )
    workflow = result.scalar_one_or_none()
    if not workflow:
        return None, "Workflow not found"

    # Если пытаемся активировать задачу
    if workflow.status == "inactive":
        # Проверяем активную подписку пользователя
        from bot.services.crud.subscription import get_user_active_subscription
        active_subscription = await get_user_active_subscription(session, user_id)
        
        if not active_subscription:
            return None, "no_subscription"
        
        # Получаем лимит каналов из подписки
        channels_limit = active_subscription.plan.channels_limit
        
        # Считаем уже активные задачи
        active_workflows = await get_active_workflows_by_user_id(session, user_id)
        active_count = len(active_workflows)
        
        # Проверяем лимит
        if active_count >= channels_limit:
            return None, "limit_exceeded"
    
    # Переключаем статус
    workflow.status = "inactive" if workflow.status == "active" else "active"
    await session.commit()
    await session.refresh(workflow)
    return workflow, None

async def get_active_workflows_by_user_id(session: AsyncSession, user_id: int) -> list[UserWorkflow]:
    result = await session.execute(
        select(UserWorkflow).where(
            UserWorkflow.user_id == user_id,
            UserWorkflow.status == "active"
        )
    )
    return result.scalars().all()

async def get_workflows_by_status(session: AsyncSession, status: str) -> list[UserWorkflow]:
    result = await session.execute(
        select(UserWorkflow).where(UserWorkflow.status == status)
    )
    return result.scalars().all()

async def get_workflow_by_workflow_id(session: AsyncSession, workflow_id: str) -> UserWorkflow | None:
    result = await session.execute(
        select(UserWorkflow).where(UserWorkflow.workflow_id == workflow_id)
    )
    return result.scalar_one_or_none()
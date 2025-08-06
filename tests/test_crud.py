# tests/test_crud.py
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import logging
import pytest
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from bot.services import crud
from bot.models.models import User, Subscription, Payment, SocialAccount, UserWorkflow, WorkflowSettings, Post, PostStats, Plan

logger = logging.getLogger(__name__)

@pytest.mark.asyncio
async def test_user_crud(session: AsyncSession):
    # CREATE
    user = await crud.user_crud.create_user(
        session,
        telegram_id=123456,
        name="Test User",
        language="en"
    )
    assert user.id

    # READ
    user_fetched = await crud.user_crud.get_user_by_id(session, user.id)
    assert user_fetched.name == "Test User"

    # UPDATE
    await crud.user_crud.update_user(session, user.id, name="Updated")
    updated = await crud.user_crud.get_user_by_id(session, user.id)
    assert updated.name == "Updated"

    # DELETE
    result = await crud.user_crud.delete_user(session, user.id)
    assert result is True

@pytest.mark.asyncio
async def test_subscription_crud(session: AsyncSession, user: User):
    now = datetime.now(timezone.utc)
    
    # Создаем план для теста
    plan = await crud.plan_crud.create_plan(
        session,
        name="Test Plan",
        price=100.00,
        channels_limit=5,
        posts_limit=100,
        manual_posts_limit=10
    )

    # CREATE
    sub = await crud.subscription_crud.create_subscription(
        session,
        user_id=user.id,
        plan_id=plan.id,  # Используем созданный plan
        start_date=now,
        end_date=now + timedelta(days=30)
    )
    assert sub.id

    # UPDATE
    await crud.subscription_crud.update_subscription(session, sub.id, status='inactive')
    updated = await crud.subscription_crud.get_subscription_by_id(session, sub.id)
    assert updated.status == 'inactive'

    # DELETE
    result = await crud.subscription_crud.delete_subscription(session, sub.id)
    assert result is True

@pytest.mark.asyncio
async def test_payment_crud(session: AsyncSession, user: User, subscription: Subscription):
    # CREATE
    pay = await crud.payment_crud.create_payment(
        session,
        user_id=user.id,
        subscription_id=subscription.id,
        amount=1000
    )
    assert pay.id

    # UPDATE
    await crud.payment_crud.update_payment(session, pay.id, status="completed")
    updated = await crud.payment_crud.get_payment_by_id(session, pay.id)
    assert updated.status == "completed"

    # DELETE
    result = await crud.payment_crud.delete_payment(session, pay.id)
    assert result is True

@pytest.mark.asyncio
async def test_social_account_crud(session: AsyncSession, user: User):
    # CREATE
    account = await crud.social_account_crud.create_social_account(
        session,
        user_id=user.id,
        platform="telegram",
        channel_name="Test",
        channel_id="1234",
        channel_type="public"
    )
    assert account.id

    # UPDATE
    await crud.social_account_crud.update_social_account(session, account.id, access_token="abc123")
    updated = await crud.social_account_crud.get_social_account_by_id(session, account.id)
    assert updated.access_token == "abc123"

    # DELETE
    result = await crud.social_account_crud.delete_social_account(session, account.id)
    assert result is True

@pytest.mark.asyncio
async def test_user_workflow_crud(session: AsyncSession, user: User):
    # CREATE
    wf = await crud.user_workflow_crud.create_user_workflow(
        session,
        user_id=user.id,
        workflow_id="w123",
        name="Workflow"
    )
    assert wf.id

    # UPDATE
    await crud.user_workflow_crud.update_user_workflow(session, wf.id, name="Updated")
    updated = await crud.user_workflow_crud.get_user_workflow_by_id(session, wf.id)
    assert updated.name == "Updated"

    # DELETE
    result = await crud.user_workflow_crud.delete_user_workflow(session, wf.id)
    assert result is True

@pytest.mark.asyncio
async def test_workflow_settings_crud(session: AsyncSession, workflow: UserWorkflow, account: SocialAccount):
    # CREATE
    settings = await crud.workflow_settings_crud.create_workflow_settings(
        session,
        user_workflow_id=workflow.id,
        social_account_id=account.id,
        interval_hours=1,
        theme="tech",
        context="ctx",
        writing_style="friendly",
        generation_method="ai",
        content_length="medium",
        moderation="auto",
        first_post_time="10:00",
        post_language="en"
    )
    assert settings.id

    # UPDATE
    await crud.workflow_settings_crud.update_workflow_settings(session, settings.id, theme="updated")
    updated = await crud.workflow_settings_crud.get_workflow_settings_by_id(session, settings.id)
    assert updated.theme == "updated"

    # DELETE
    result = await crud.workflow_settings_crud.delete_workflow_settings(session, settings.id)
    assert result is True

@pytest.mark.asyncio
async def test_post_crud(session: AsyncSession, workflow: UserWorkflow):
    now = datetime.now(timezone.utc)

    # CREATE
    post = await crud.post_crud.create_post(
        session,
        user_workflow_id=workflow.id,
        topic="AI",
        content="Content",
        media_type="text",
        scheduled_time=now + timedelta(minutes=30)
    )
    assert post.id

    # UPDATE
    await crud.post_crud.update_post(session, post.id, topic="Updated")
    updated = await crud.post_crud.get_post_by_id(session, post.id)
    assert updated.topic == "Updated"

    # DELETE
    result = await crud.post_crud.delete_post(session, post.id)
    assert result is True

@pytest.mark.asyncio
async def test_post_stats_crud(session: AsyncSession, post: Post):
    # CREATE
    stats = await crud.post_stats_crud.create_post_stats(
        session,
        post_id=post.id,
        views=100,
        likes=5
    )
    assert stats.id

    # UPDATE
    await crud.post_stats_crud.update_post_stats(session, stats.id, views=250)
    updated = await crud.post_stats_crud.get_post_stats_by_id(session, stats.id)
    assert updated.views == 250

    # DELETE
    result = await crud.post_stats_crud.delete_post_stats(session, stats.id)
    assert result is True

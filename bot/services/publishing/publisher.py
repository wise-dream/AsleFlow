import asyncio
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from aiogram import Bot

from bot.models.models import Post, UserWorkflow, WorkflowSettings, SocialAccount
from bot.services.crud.post import update_post


class PublishingService:
    """Сервис для публикации постов в социальные сети"""

    def __init__(self, bot: Bot):
        self.bot = bot

    async def publish_post(self, session: AsyncSession, post_id: int) -> bool:
        """
        Публикует пост в соответствующий канал

        Args:
            session: Сессия базы данных
            post_id: ID поста для публикации

        Returns:
            bool: True если публикация успешна, False иначе
        """
        try:
            # Получаем пост с всеми связанными данными
            post_data = await self._get_post_with_details(session, post_id)
            if not post_data:
                return False

            post, workflow, settings, social_account = post_data

            # Проверяем что пост готов к публикации
            if post.status not in ["pending", "scheduled"]:
                return False

            # Публикуем в зависимости от платформы
            success = False
            if social_account.platform == "telegram":
                success = await self._publish_to_telegram(post, social_account)
            else:
                # Здесь можно добавить поддержку других платформ
                print(f"Platform {social_account.platform} not supported yet")
                return False

            if success:
                # Обновляем статус поста
                await update_post(
                    session,
                    post_id,
                    status="published",
                    published_time=datetime.now(timezone.utc)
                )
                return True
            else:
                # Помечаем как неудачный
                await update_post(session, post_id, status="failed")
                return False
                
        except Exception as e:
            print(f"Error publishing post {post_id}: {e}")
            try:
                await update_post(session, post_id, status="failed")
            except:
                pass
            return False
    
    async def _get_post_with_details(self, session: AsyncSession, post_id: int):
        """Получает пост со всеми связанными данными.
        Поддерживает два варианта:
        1) Пост привязан к workflow (через WorkflowSettings → SocialAccount)
        2) Пост имеет прямую ссылку на SocialAccount (manual без workflow)
        """
        # Попытка №1: полный путь через workflow/settings
        try:
            query = (
                select(Post, UserWorkflow, WorkflowSettings, SocialAccount)
                .join(UserWorkflow, Post.user_workflow_id == UserWorkflow.id)
                .join(WorkflowSettings, WorkflowSettings.user_workflow_id == UserWorkflow.id)
                .join(SocialAccount, WorkflowSettings.social_account_id == SocialAccount.id)
                .where(Post.id == post_id)
            )
            result = await session.execute(query)
            row = result.first()
            if row:
                return row.Post, row.UserWorkflow, row.WorkflowSettings, row.SocialAccount
        except Exception:
            pass

        # Попытка №2: без workflow, напрямую через Post.social_account_id
        try:
            query2 = (
                select(Post, SocialAccount)
                .join(SocialAccount, Post.social_account_id == SocialAccount.id)
                .where(Post.id == post_id)
            )
            result2 = await session.execute(query2)
            row2 = result2.first()
            if row2:
                # Совместимость с основным форматом: вернем workflow/settings как None
                return row2.Post, None, None, row2.SocialAccount
        except Exception:
            pass

        return None
    
    async def _publish_to_telegram(self, post: Post, social_account: SocialAccount) -> bool:
        """Публикует пост в Telegram канал"""
        try:
            chat_id = social_account.telegram_chat_id
            if not chat_id:
                print(f"No telegram_chat_id for social account {social_account.id}")
                return False
            
            # Формируем текст поста
            message_text = f"📝 <b>{post.topic}</b>\n\n{post.content}"
            
            # Отправляем сообщение
            await self.bot.send_message(
                chat_id=chat_id,
                text=message_text,
                parse_mode="HTML"
            )
            
            print(f"Successfully published post {post.id} to Telegram channel {chat_id}")
            return True
            
        except Exception as e:
            print(f"Error publishing to Telegram: {e}")
            return False
    
    async def schedule_post_for_publishing(self, session: AsyncSession, post_id: int) -> bool:
        """
        Планирует пост к публикации (изменяет статус на scheduled)
        
        Args:
            session: Сессия базы данных  
            post_id: ID поста
            
        Returns:
            bool: True если успешно запланирован
        """
        try:
            updated_post = await update_post(
                session,
                post_id,
                status="scheduled",
                moderated=True
            )
            return updated_post is not None
        except Exception as e:
            print(f"Error scheduling post {post_id}: {e}")
            return False
    
    async def get_pending_posts(self, session: AsyncSession) -> list[Post]:
        """Получает все посты готовые к публикации"""
        query = (
            select(Post)
            .where(
                Post.status == "scheduled",
                Post.scheduled_time <= datetime.now(timezone.utc)
            )
            .order_by(Post.scheduled_time)
        )
        
        result = await session.execute(query)
        return list(result.scalars().all())
    
    async def run_publishing_cycle(self, session: AsyncSession):
        """
        Запускает цикл публикации - публикует все готовые посты
        Эта функция может вызываться периодически (например, каждые 5 минут)
        """
        pending_posts = await self.get_pending_posts(session)
        
        # Публикуем параллельно с ограничением степени параллелизма
        semaphore = asyncio.Semaphore(5)

        async def _worker(p):
            async with semaphore:
                success = await self.publish_post(session, p.id)
                if success:
                    print(f"Published post {p.id}: {p.topic}")
                else:
                    print(f"Failed to publish post {p.id}: {p.topic}")
                await asyncio.sleep(0.5)

        await asyncio.gather(*[ _worker(p) for p in pending_posts ])

    async def get_posts_for_n8n(self, session: AsyncSession, limit: int = 10) -> list[dict]:
        """
        Получает посты готовые к публикации для n8n
        
        Args:
            session: Сессия базы данных
            limit: Максимальное количество постов
            
        Returns:
            list[dict]: Список постов с полной информацией для публикации
        """
        try:
            # Получаем посты готовые к публикации
            posts = await self.get_pending_posts(session)
            
            result = []
            for post in posts[:limit]:
                # Получаем связанные данные
                post_data = await self._get_post_with_details(session, post.id)
                if not post_data:
                    continue
                    
                post_obj, workflow, settings, social_account = post_data
                
                # Формируем данные для n8n
                post_info = {
                    "post_id": post_obj.id,
                    "topic": post_obj.topic,
                    "content": post_obj.content,
                    "media_type": post_obj.media_type,
                    "media_url": post_obj.media_url,
                    "scheduled_time": post_obj.scheduled_time.isoformat() if post_obj.scheduled_time else None,
                    "platform": social_account.platform,
                    "channel_id": social_account.channel_id,
                    "channel_name": social_account.channel_name,
                    "telegram_chat_id": social_account.telegram_chat_id,
                    "access_token": social_account.access_token,
                    "user_id": workflow.user_id,
                    "workflow_id": workflow.id,
                    "workflow_name": workflow.name
                }
                
                result.append(post_info)
            
            return result
            
        except Exception as e:
            print(f"Error getting posts for n8n: {e}")
            return []
    
    async def mark_post_as_published(self, session: AsyncSession, post_id: int, external_id: str = None) -> bool:
        """
        Помечает пост как опубликованный (вызывается n8n после успешной публикации)
        
        Args:
            session: Сессия базы данных
            post_id: ID поста
            external_id: Внешний ID поста (например, ID в Telegram)
            
        Returns:
            bool: True если успешно обновлен
        """
        try:
            # Обновляем статус поста
            success = await update_post(
                session,
                post_id,
                status="published",
                published_time=datetime.now(timezone.utc)
            )
            
            if success and external_id:
                # Здесь можно сохранить external_id если нужно
                # await update_post(session, post_id, external_id=external_id)
                pass
            
            return success
            
        except Exception as e:
            print(f"Error marking post as published: {e}")
            return False
    
    async def mark_post_as_failed(self, session: AsyncSession, post_id: int, error_message: str = None) -> bool:
        """
        Помечает пост как неудачный (вызывается n8n при ошибке публикации)
        
        Args:
            session: Сессия базы данных
            post_id: ID поста
            error_message: Сообщение об ошибке
            
        Returns:
            bool: True если успешно обновлен
        """
        try:
            # Обновляем статус поста
            success = await update_post(
                session,
                post_id,
                status="failed"
            )
            
            # Здесь можно сохранить error_message в отдельную таблицу если нужно
            if error_message:
                print(f"Post {post_id} failed: {error_message}")
            
            return success
            
        except Exception as e:
            print(f"Error marking post as failed: {e}")
            return False
    
    async def get_posts_stats_for_n8n(self, session: AsyncSession, user_id: int = None) -> dict:
        """
        Получает статистику постов для n8n
        
        Args:
            session: Сессия базы данных
            user_id: ID пользователя (опционально)
            
        Returns:
            dict: Статистика постов
        """
        try:
            from sqlalchemy import func
            
            # Базовый запрос
            query = select(
                Post.status,
                func.count(Post.id).label('count')
            ).group_by(Post.status)
            
            # Фильтр по пользователю если указан
            if user_id:
                query = query.join(UserWorkflow).where(UserWorkflow.user_id == user_id)
            
            result = await session.execute(query)
            stats = result.all()
            
            # Формируем статистику
            stats_dict = {
                'pending': 0,
                'scheduled': 0,
                'published': 0,
                'failed': 0,
                'total': 0
            }
            
            for status, count in stats:
                stats_dict[status] = count
                stats_dict['total'] += count
            
            return stats_dict
            
        except Exception as e:
            print(f"Error getting posts stats: {e}")
            return {
                'pending': 0,
                'scheduled': 0,
                'published': 0,
                'failed': 0,
                'total': 0
            } 
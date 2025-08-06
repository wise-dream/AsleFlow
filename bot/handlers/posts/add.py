from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from datetime import datetime, timezone, timedelta
from sqlalchemy.future import select

from bot.services.crud.post import create_post
from bot.services.ai import OpenAIService
from bot.keyboards.inline.workflows import (
    get_theme_selection_keyboard,
    get_style_selection_keyboard, 
    get_content_length_keyboard,
    get_media_type_keyboard,
    get_language_selection_keyboard,
    get_time_selection_keyboard
)

router = Router()

class AddPostStates(StatesGroup):
    choosing_account = State()  # Новое состояние для выбора аккаунта
    choosing_creation_method = State()  # Новое состояние для выбора способа создания
    choosing_theme = State()
    entering_custom_theme = State()  # Новое состояние для ввода своей тематики
    choosing_style = State()
    choosing_content_length = State()
    choosing_media_type = State()
    choosing_language = State()
    entering_topic = State()
    choosing_content_method = State()
    entering_content = State()
    generating_ai_content = State()
    confirming_post = State()
    choosing_publish_time = State()  # Новый этап


async def add_post_start(callback: CallbackQuery, session, user, i18n, state: FSMContext, **_):
    """Начало создания поста"""
    await callback.answer()
    
    # Сначала проверяем наличие аккаунтов
    from bot.services.crud.socials import get_social_accounts_by_user_id
    accounts = await get_social_accounts_by_user_id(session, user.id)
    
    if not accounts:
        await callback.message.answer(
            i18n.get("post.add.no_accounts", "❌ У вас нет подключенных аккаунтов социальных сетей. Сначала добавьте аккаунт в разделе 'Соцсети'.")
        )
        return
    
    # Проверяем подписку и бесплатные посты
    from bot.services.crud.subscription import get_active_subscription
    from bot.services.crud.usage_stats import get_user_usage_stats
    from bot.services.crud.user import can_create_free_post, get_free_posts_remaining
    
    subscription = await get_active_subscription(session, user.id)
    
    if not subscription:
        # Проверяем возможность создания бесплатного поста
        from bot.services.crud.user import get_free_posts_info
        free_posts_info = await get_free_posts_info(session, user.id)
        
        if not free_posts_info['can_create']:
            await callback.message.answer(
                i18n.get("post.add.free_posts_exceeded", "❌ Вы использовали все {limit} бесплатных постов. Оформите подписку для создания новых постов.").format(limit=free_posts_info['limit'])
            )
            return
        
        # Сохраняем информацию о бесплатных постах
        await state.update_data(is_free_post=True)
    else:
        # Получаем статистику использования для подписанных пользователей
        usage_stats = await get_user_usage_stats(session, user.id)
        if usage_stats and usage_stats.posts_used >= subscription.plan.posts_limit:
            await callback.message.answer(
                i18n.get("post.add.limit_exceeded", "❌ Достигнут лимит постов по вашей подписке. Обновите план для создания новых постов.")
            )
            return
        
        await state.update_data(is_free_post=False)
    
    await callback.message.delete()
    
    # Начинаем с выбора аккаунта
    text = i18n.get("post.add.choose_account", "📱 Выберите аккаунт для публикации:")
    
    from bot.keyboards.inline.workflows import get_account_selection_keyboard
    msg = await callback.message.answer(text, reply_markup=get_account_selection_keyboard(accounts))
    await state.set_state(AddPostStates.choosing_account)
    await state.update_data(prev_msg_id=msg.message_id)


async def process_account_selection(callback: CallbackQuery, state: FSMContext, i18n, **_):
    """Обработка выбора аккаунта"""
    await callback.answer()
    account_id = int(callback.data.split(":")[-1])
    
    data = await state.get_data()
    try:
        if msg_id := data.get("prev_msg_id"):
            await callback.bot.delete_message(callback.message.chat.id, msg_id)
    except: 
        pass
    
    await state.update_data(social_account_id=account_id)
    
    # Показываем информацию о бесплатных постах для пользователей без подписки
    is_free_post = data.get("is_free_post", False)
    
    if is_free_post:
        from bot.services.crud.user import get_free_posts_info
        session = callback.bot.get("session")
        free_posts_info = await get_free_posts_info(session, callback.from_user.id)
        
        text = i18n.get("post.add.free_posts_available", "🎁 У вас есть {remaining} бесплатных постов!").format(remaining=free_posts_info['remaining'])
        text += "\n\n" + i18n.get("post.add.choose_creation_method", "🎯 Выберите способ создания поста:")
        
        from bot.keyboards.inline.posts import get_post_creation_method_keyboard
        msg = await callback.message.answer(text, reply_markup=get_post_creation_method_keyboard(i18n))
        await state.set_state(AddPostStates.choosing_creation_method)
        await state.update_data(prev_msg_id=msg.message_id)
    else:
        # Для подписанных пользователей сразу переходим к выбору способа создания
        text = i18n.get("post.add.choose_creation_method", "🎯 Выберите способ создания поста:")
        
        from bot.keyboards.inline.posts import get_post_creation_method_keyboard
        msg = await callback.message.answer(text, reply_markup=get_post_creation_method_keyboard(i18n))
        await state.set_state(AddPostStates.choosing_creation_method)
        await state.update_data(prev_msg_id=msg.message_id)


async def process_creation_method_selection(callback: CallbackQuery, state: FSMContext, i18n, **_):
    """Обработка выбора способа создания поста"""
    await callback.answer()
    method = callback.data.split(":")[-1]
    
    data = await state.get_data()
    try:
        if msg_id := data.get("prev_msg_id"):
            await callback.bot.delete_message(callback.message.chat.id, msg_id)
    except: 
        pass
    
    # Сохраняем выбранный способ создания
    await state.update_data(creation_method=method)
    
    if method == "workflow":
        # Переход к созданию поста через задачу (существующая логика)
        from bot.services.crud.workflow import get_user_workflows
        workflows = await get_user_workflows(callback.bot.get("session"), callback.from_user.id)
        
        if not workflows:
            await callback.message.answer(
                i18n.get("post.add.no_workflows", "❌ У вас нет активных задач. Сначала создайте задачу.")
            )
            return
        
        # Здесь должна быть логика выбора задачи
        # Пока что просто переходим к ручной настройке
        text = i18n.get("post.add.choose_theme", "📂 Выберите тематику поста:")
        from bot.keyboards.inline.workflows import get_theme_selection_keyboard
        msg = await callback.message.answer(text, reply_markup=get_theme_selection_keyboard(i18n))
        await state.set_state(AddPostStates.choosing_theme)
        await state.update_data(prev_msg_id=msg.message_id)
        
    elif method == "manual":
        # Переход к ручной настройке
        text = i18n.get("post.add.choose_theme", "📂 Выберите тематику поста:")
        from bot.keyboards.inline.workflows import get_theme_selection_keyboard
        msg = await callback.message.answer(text, reply_markup=get_theme_selection_keyboard(i18n))
        await state.set_state(AddPostStates.choosing_theme)
        await state.update_data(prev_msg_id=msg.message_id)
    
    else:
        await callback.message.answer("❌ Неверный выбор способа создания поста.")


async def process_theme_selection(callback: CallbackQuery, state: FSMContext, i18n, **_):
    """Обработка выбора темы"""
    await callback.answer()
    theme = callback.data.split(":")[-1]
    
    data = await state.get_data()
    try:
        if msg_id := data.get("prev_msg_id"):
            await callback.bot.delete_message(callback.message.chat.id, msg_id)
    except: 
        pass
    
    # Если выбрана своя тематика, переходим к вводу
    if theme == "custom":
        text = i18n.get("post.add.enter_custom_theme", "✏️ Введите свою тематику поста:")
        msg = await callback.message.answer(text)
        await state.set_state(AddPostStates.entering_custom_theme)
        await state.update_data(prev_msg_id=msg.message_id)
    else:
        await state.update_data(theme=theme)
        
        text = i18n.get("post.add.choose_style", "✨ Выберите стиль написания:")
        msg = await callback.message.answer(text, reply_markup=get_style_selection_keyboard(i18n))
        await state.set_state(AddPostStates.choosing_style)
        await state.update_data(prev_msg_id=msg.message_id)


async def process_custom_theme(message: Message, state: FSMContext, i18n, **_):
    """Обработка ввода своей тематики"""
    custom_theme = message.text.strip()
    
    if len(custom_theme) < 3:
        await message.answer(i18n.get("post.add.theme_too_short", "⚠️ Тематика слишком короткая. Минимум 3 символа."))
        return
    
    if len(custom_theme) > 50:
        await message.answer(i18n.get("post.add.theme_too_long", "⚠️ Тематика слишком длинная. Максимум 50 символов."))
        return
    
    data = await state.get_data()
    try:
        await message.delete()
        if msg_id := data.get("prev_msg_id"):
            await message.bot.delete_message(message.chat.id, msg_id)
    except: 
        pass
    
    await state.update_data(theme=custom_theme)
    
    text = i18n.get("post.add.choose_style", "✨ Выберите стиль написания:")
    msg = await message.answer(text, reply_markup=get_style_selection_keyboard(i18n))
    await state.set_state(AddPostStates.choosing_style)
    await state.update_data(prev_msg_id=msg.message_id)


async def process_style_selection(callback: CallbackQuery, state: FSMContext, i18n, **_):
    """Обработка выбора стиля"""
    await callback.answer()
    style = callback.data.split(":")[-1]
    
    if style not in {"formal", "friendly", "humorous"}:
        await callback.message.answer(i18n.get("post.add.invalid_style", "❌ Неверный выбор стиля."))
        return
    
    data = await state.get_data()
    try:
        if msg_id := data.get("prev_msg_id"):
            await callback.bot.delete_message(callback.message.chat.id, msg_id)
    except: 
        pass
    
    await state.update_data(writing_style=style)
    
    text = i18n.get("post.add.choose_content_length", "📏 Выберите длину контента:")
    msg = await callback.message.answer(text, reply_markup=get_content_length_keyboard(i18n))
    await state.set_state(AddPostStates.choosing_content_length)
    await state.update_data(prev_msg_id=msg.message_id)


async def process_content_length_selection(callback: CallbackQuery, state: FSMContext, i18n, **_):
    """Обработка выбора длины контента"""
    await callback.answer()
    length = callback.data.split(":")[-1]
    
    if length not in {"short", "medium", "long"}:
        await callback.message.answer(i18n.get("post.add.invalid_length", "❌ Неверный выбор длины контента."))
        return
    
    data = await state.get_data()
    try:
        if msg_id := data.get("prev_msg_id"):
            await callback.bot.delete_message(callback.message.chat.id, msg_id)
    except: 
        pass
    
    await state.update_data(content_length=length)
    
    text = i18n.get("post.add.choose_media_type", "🎨 Выберите тип контента:")
    msg = await callback.message.answer(text, reply_markup=get_media_type_keyboard(i18n))
    await state.set_state(AddPostStates.choosing_media_type)
    await state.update_data(prev_msg_id=msg.message_id)


async def process_media_type_selection(callback: CallbackQuery, state: FSMContext, i18n, **_):
    """Обработка выбора типа медиа"""
    await callback.answer()
    media_type = callback.data.split(":")[-1]
    
    if media_type not in {"text", "image", "video", "carousel"}:
        await callback.message.answer(i18n.get("post.add.invalid_media", "❌ Неверный выбор типа медиа."))
        return
    
    data = await state.get_data()
    try:
        if msg_id := data.get("prev_msg_id"):
            await callback.bot.delete_message(callback.message.chat.id, msg_id)
    except: 
        pass
    
    await state.update_data(post_media_type=media_type)
    
    text = i18n.get("post.add.choose_language", "🌐 Выберите язык:")
    msg = await callback.message.answer(text, reply_markup=get_language_selection_keyboard(i18n))
    await state.set_state(AddPostStates.choosing_language)
    await state.update_data(prev_msg_id=msg.message_id)


async def process_language_selection(callback: CallbackQuery, state: FSMContext, i18n, **_):
    """Обработка выбора языка"""
    await callback.answer()
    language = callback.data.split(":")[-1]
    
    data = await state.get_data()
    try:
        if msg_id := data.get("prev_msg_id"):
            await callback.bot.delete_message(callback.message.chat.id, msg_id)
    except: 
        pass
    
    await state.update_data(post_language=language)
    
    topic_prompt = i18n.get('post.add.topic_prompt', '💡 Введите тему поста (например: «Как инвестировать в ETF»):')
    text = (
        f"📝 <b>{i18n.get('post.add.enter_topic', 'Создание поста')}</b>\n\n"
        f"{topic_prompt}"
    )
    
    msg = await callback.message.answer(text, parse_mode="HTML")
    await state.update_data(prev_msg_id=msg.message_id)
    await state.set_state(AddPostStates.entering_topic)


async def process_topic(message: Message, state: FSMContext, i18n, **_):
    """Обработка ввода темы поста"""
    topic = message.text.strip()
    
    if len(topic) < 5:
        await message.answer(i18n.get("post.add.topic_too_short", "⚠️ Тема слишком короткая. Минимум 5 символов."))
        return
    
    if len(topic) > 200:
        await message.answer(i18n.get("post.add.topic_too_long", "⚠️ Тема слишком длинная. Максимум 200 символов."))
        return
    
    data = await state.get_data()
    try:
        await message.delete()
        if msg_id := data.get("prev_msg_id"):
            await message.bot.delete_message(message.chat.id, msg_id)
    except: 
        pass
    
    text = (
        f"📝 <b>{i18n.get('post.add.choose_method', 'Выберите способ создания контента')}</b>\n\n"
        f"🎯 <b>{i18n.get('post.add.topic_label', 'Тема')}:</b> {topic}\n\n"
        f"{i18n.get('post.add.method_prompt', 'Как хотите создать контент?')}"
    )
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=i18n.get("post.add.ai_generate", "🤖 Генерировать AI"),
                callback_data="post:add:ai:manual"
            )
        ],
        [
            InlineKeyboardButton(
                text=i18n.get("post.add.manual_input", "✍️ Написать самому"),
                callback_data="post:add:manual:manual"
            )
        ],
        [
            InlineKeyboardButton(
                text=i18n.get("common.back", "⬅️ Назад"),
                callback_data="posts:back"
            )
        ]
    ])
    
    msg = await message.answer(text, reply_markup=keyboard, parse_mode="HTML")
    await state.update_data(
        topic=topic,
        prev_msg_id=msg.message_id
    )
    await state.set_state(AddPostStates.choosing_content_method)


async def process_content_method_ai(callback: CallbackQuery, state: FSMContext, session, user, i18n, **_):
    """Обработка выбора AI генерации"""
    await callback.answer()
    
    data = await state.get_data()
    topic = data.get("topic")
    
    try:
        if msg_id := data.get("prev_msg_id"):
            await callback.bot.delete_message(callback.message.chat.id, msg_id)
    except: 
        pass
    
    # Показываем сообщение о генерации
    loading_msg = await callback.message.answer(
        f"🤖 {i18n.get('post.add.generating', 'Генерирую контент...')}\n\n"
        f"⏳ {i18n.get('post.add.please_wait', 'Пожалуйста, подождите несколько секунд.')}"
    )
    
    try:
        # Получаем параметры из выбранных пользователем настроек
        theme = data.get("theme", "общая тематика")
        style = data.get("writing_style", "friendly")
        language = data.get("post_language", "ru")
        content_length = data.get("content_length", "medium")
        
        # Проверяем тип подписки пользователя
        from bot.services.crud.subscription import get_active_subscription
        active_subscription = await get_active_subscription(session, user.id)
        
        # Определяем, является ли пользователь премиум (с активной подпиской)
        is_premium = active_subscription is not None
        
        # Генерируем контент через AI с учетом типа подписки
        ai_service = OpenAIService()
        generated_content = await ai_service.generate_post_content(
            topic=topic,
            theme=theme,
            style=style,
            language=language,
            content_length=content_length,
            max_length=3000,
            is_premium=is_premium
        )
        
        await loading_msg.delete()
        
        if generated_content:
            # Определяем модель для отображения
            model_name = i18n.get("post.add.ai_model_gpt4", "GPT-4") if is_premium else i18n.get("post.add.ai_model_gpt35", "GPT-3.5 Turbo")
            
            # Показываем сгенерированный контент
            preview_text = (
                f"🤖 <b>{i18n.get('post.add.ai_generated', 'AI сгенерировал контент')}</b>\n\n"
                f"🧠 <b>Модель:</b> {model_name}\n"
                f"📂 <b>{i18n.get('workflow.field.theme', 'Тематика')}:</b> {theme}\n"
                f"✨ <b>{i18n.get('workflow.field.style', 'Стиль')}:</b> {style}\n"
                f"📏 <b>{i18n.get('workflow.field.length', 'Длина')}:</b> {content_length}\n"
                f"🎯 <b>{i18n.get('post.add.topic_label', 'Тема')}:</b> {topic}\n\n"
                f"📄 <b>{i18n.get('post.add.generated_content', 'Сгенерированный контент')}:</b>\n\n{generated_content}"
            )
            
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=i18n.get("post.add.use_content", "✅ Использовать"),
                        callback_data="post:add:use_ai"
                    ),
                    InlineKeyboardButton(
                        text=i18n.get("post.add.regenerate", "🔄 Пересоздать"),
                        callback_data="post:add:ai:manual"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text=i18n.get("post.add.edit_content", "✏️ Редактировать"),
                        callback_data="post:add:manual:manual"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text=i18n.get("common.back", "⬅️ Назад"),
                        callback_data="posts:back"
                    )
                ]
            ])
            
            msg = await callback.message.answer(preview_text, reply_markup=keyboard, parse_mode="HTML")
            await state.update_data(
                generated_content=generated_content,
                prev_msg_id=msg.message_id
            )
            await state.set_state(AddPostStates.generating_ai_content)
        else:
            # Ошибка генерации - переходим к ручному вводу
            await callback.message.answer(
                i18n.get("post.add.ai_error", "❌ Ошибка генерации. Попробуйте написать контент самостоятельно.")
            )
            await process_content_method_manual(callback, state, session, user, i18n)
            
    except Exception as e:
        try:
            await loading_msg.delete()
        except:
            pass
        await callback.message.answer(
            i18n.get("post.add.ai_error", "❌ Ошибка генерации. Попробуйте написать контент самостоятельно.")
        )
        await process_content_method_manual(callback, state, session, user, i18n)


async def process_content_method_manual(callback: CallbackQuery, state: FSMContext, session, user, i18n, **_):
    """Обработка выбора ручного ввода"""
    await callback.answer()
    
    data = await state.get_data()
    topic = data.get("topic")
    
    try:
        if msg_id := data.get("prev_msg_id"):
            await callback.bot.delete_message(callback.message.chat.id, msg_id)
    except: 
        pass
    
    text = (
        f"📝 <b>{i18n.get('post.add.enter_content', 'Введите контент')}</b>\n\n"
        f"📂 <b>{i18n.get('workflow.field.theme', 'Тематика')}:</b> {data.get('theme', 'общая')}\n"
        f"🎯 <b>{i18n.get('post.add.topic_label', 'Тема')}:</b> {topic}\n\n"
        f"{i18n.get('post.add.content_prompt', '✍️ Введите текст поста:')}"
    )
    
    msg = await callback.message.answer(text, parse_mode="HTML")
    await state.update_data(prev_msg_id=msg.message_id)
    await state.set_state(AddPostStates.entering_content)


async def process_use_ai_content(callback: CallbackQuery, state: FSMContext, session, user, i18n, **_):
    """Обработка использования AI контента"""
    await callback.answer()
    
    data = await state.get_data()
    generated_content = data.get("generated_content")
    
    if generated_content:
        # После подтверждения контента спрашиваем время публикации
        await ask_publish_time(callback, state, i18n)
    else:
        await callback.message.answer(i18n.get("post.add.error", "❌ Ошибка создания поста. Попробуйте позже."))
        await state.clear()


async def create_post_from_content(content: str, callback_or_message, state: FSMContext, session, user, i18n, scheduled_time=None):
    """Создает пост из готового контента"""
    data = await state.get_data()
    topic = data.get("topic")
    
    if scheduled_time is None:
        from datetime import datetime, timezone, timedelta
        scheduled_time = datetime.now(timezone.utc) + timedelta(hours=1)
    
    try:
        if hasattr(callback_or_message, 'message'):
            # Это callback
            try:
                if msg_id := data.get("prev_msg_id"):
                    await callback_or_message.bot.delete_message(callback_or_message.message.chat.id, msg_id)
            except: 
                pass
            message_handler = callback_or_message.message
        else:
            # Это message
            try:
                await callback_or_message.delete()
                if msg_id := data.get("prev_msg_id"):
                    await callback_or_message.bot.delete_message(callback_or_message.chat.id, msg_id)
            except: 
                pass
            message_handler = callback_or_message
        
        # Время по умолчанию - через час
        # scheduled_time = datetime.now(timezone.utc) + timedelta(hours=1) # This line is now handled by the function call
        
        post = await create_post(
            session,
            user_workflow_id=None,  # Пост создается независимо от workflow
            social_account_id=data.get("social_account_id"),  # Используем выбранный аккаунт
            topic=topic,
            content=content,
            media_type=data.get("post_media_type", "text"),
            status="pending",
            scheduled_time=scheduled_time,
            moderated=False
        )
        
        # Обновляем статистику использования
        if post:
            data = await state.get_data()
            is_free_post = data.get("is_free_post", False)
            
            if is_free_post:
                # Увеличиваем счетчик бесплатных постов
                from bot.services.crud.user import increment_free_posts_used, get_free_posts_remaining
                await increment_free_posts_used(session, user.id)
                remaining = await get_free_posts_remaining(session, user.id)
                
                # Показываем сообщение о бесплатном посте
                preview_text = (
                    f"✅ <b>{i18n.get('post.add.free_post_created', 'Бесплатный пост создан! Осталось бесплатных постов: {remaining}').format(remaining=remaining)}</b>\n\n"
                    f"📂 <b>{i18n.get('workflow.field.theme', 'Тематика')}:</b> {data.get('theme', 'общая')}\n"
                    f"✨ <b>{i18n.get('workflow.field.style', 'Стиль')}:</b> {data.get('writing_style', 'дружелюбный')}\n"
                    f"🎯 <b>{i18n.get('post.add.topic_label', 'Тема')}:</b> {topic}\n"
                    f"📅 <b>{i18n.get('post.add.scheduled_label', 'Запланировано')}:</b> {scheduled_time.strftime('%d.%m.%Y %H:%M')}\n\n"
                    f"📄 <b>{i18n.get('post.add.content_label', 'Контент')}:</b>\n{content[:300]}"
                )
            else:
                # Обновляем статистику подписки
                from bot.services.crud.usage_stats import get_user_usage_stats, update_user_usage_stats
                usage_stats = await get_user_usage_stats(session, user.id)
                if usage_stats:
                    usage_stats.posts_used += 1
                    await session.commit()
                
                # Обычное сообщение о создании поста
                preview_text = (
                    f"✅ <b>{i18n.get('post.add.created', 'Пост создан!')}</b>\n\n"
                    f"📂 <b>{i18n.get('workflow.field.theme', 'Тематика')}:</b> {data.get('theme', 'общая')}\n"
                    f"✨ <b>{i18n.get('workflow.field.style', 'Стиль')}:</b> {data.get('writing_style', 'дружелюбный')}\n"
                    f"🎯 <b>{i18n.get('post.add.topic_label', 'Тема')}:</b> {topic}\n"
                    f"📅 <b>{i18n.get('post.add.scheduled_label', 'Запланировано')}:</b> {scheduled_time.strftime('%d.%m.%Y %H:%M')}\n\n"
                    f"📄 <b>{i18n.get('post.add.content_label', 'Контент')}:</b>\n{content[:300]}"
                )
        
        # Показываем превью созданного поста
        
        if len(content) > 300:
            preview_text += "..."
        
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=i18n.get("post.view_all", "📋 Все посты"),
                    callback_data="posts:back"
                ),
                InlineKeyboardButton(
                    text=i18n.get("post.add.create_another", "➕ Еще пост"),
                    callback_data="post:add"
                )
            ]
        ])
        
        await message_handler.answer(preview_text, reply_markup=keyboard, parse_mode="HTML")
        await state.clear()
        
    except Exception as e:
        await message_handler.answer(
            i18n.get("post.add.error", "❌ Ошибка создания поста. Попробуйте позже.")
        )
        await state.clear()


async def process_content(message: Message, state: FSMContext, session, user, i18n, **_):
    """Обработка ручного ввода контента"""
    content = message.text.strip()
    
    if len(content) < 10:
        await message.answer(i18n.get("post.add.content_too_short", "⚠️ Контент слишком короткий."))
        return
    
    if len(content) > 4000:
        await message.answer(i18n.get("post.add.content_too_long", "⚠️ Контент слишком длинный. Максимум 4000 символов."))
        return
    
    data = await state.get_data()
    try:
        await message.delete()
        if msg_id := data.get("prev_msg_id"):
            await message.bot.delete_message(message.chat.id, msg_id)
    except: 
        pass
    
    await state.update_data(generated_content=content)
    # После ручного ввода спрашиваем время публикации
    await ask_publish_time(message, state, i18n)

async def ask_publish_time(callback_or_message, state: FSMContext, i18n):
    """Показывает клавиатуру выбора времени публикации"""
    text = i18n.get("post.add.choose_publish_time", "⏰ Когда опубликовать пост?")
    if hasattr(callback_or_message, 'message'):
        msg = await callback_or_message.message.answer(text, reply_markup=get_time_selection_keyboard())
    else:
        msg = await callback_or_message.answer(text, reply_markup=get_time_selection_keyboard())
    await state.set_state(AddPostStates.choosing_publish_time)
    await state.update_data(prev_msg_id=msg.message_id)

async def process_publish_time(callback: CallbackQuery, state: FSMContext, session, user, i18n, **_):
    await callback.answer()
    time_data = callback.data.split(":", 1)[-1]
    data = await state.get_data()
    try:
        if msg_id := data.get("prev_msg_id"):
            await callback.bot.delete_message(callback.message.chat.id, msg_id)
    except:
        pass
    if time_data == "now":
        from datetime import datetime, timezone
        scheduled_time = datetime.now(timezone.utc)
    else:
        from datetime import datetime, timezone
        today = datetime.now(timezone.utc)
        hour, minute = map(int, time_data.split(":"))
        scheduled_time = today.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if scheduled_time < today:
            scheduled_time = scheduled_time.replace(day=today.day + 1)
    await create_post_from_content(
        data.get("generated_content"), callback, state, session, user, i18n, scheduled_time=scheduled_time
    )


def register_add_post_handlers(router: Router):
    """Регистрация обработчиков создания постов"""
    router.callback_query.register(add_post_start, F.data == "post:add")
    router.callback_query.register(process_account_selection, F.data.startswith("workflow:account:"))
    router.callback_query.register(process_creation_method_selection, F.data.startswith("post:add:"))
    router.callback_query.register(process_theme_selection, F.data.startswith("theme:"))
    router.callback_query.register(process_style_selection, F.data.startswith("style:"))
    router.callback_query.register(process_content_length_selection, F.data.startswith("length:"))
    router.callback_query.register(process_media_type_selection, F.data.startswith("media:"))
    router.callback_query.register(process_language_selection, F.data.startswith("lang:"))
    router.callback_query.register(process_content_method_ai, F.data.startswith("post:add:ai:"))
    router.callback_query.register(process_content_method_manual, F.data.startswith("post:add:manual:"))
    router.callback_query.register(process_use_ai_content, F.data == "post:add:use_ai")
    router.callback_query.register(process_publish_time, F.data.startswith("time:"))
    router.message.register(process_topic, AddPostStates.entering_topic)
    router.message.register(process_content, AddPostStates.entering_content)
    router.message.register(process_custom_theme, AddPostStates.entering_custom_theme) 
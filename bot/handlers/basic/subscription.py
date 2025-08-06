from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram import F, Router
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from bot.services.crud.plan import get_all_active_plans
from bot.services.crud.subscription import get_user_active_subscription, create_subscription
from bot.services.crud.user import add_balance_to_user, get_user_by_telegram_id
from bot.keyboards.inline.subscription import get_subscription_keyboard, get_balance_keyboard

router = Router()


class SubscriptionStates(StatesGroup):
    waiting_for_balance_amount = State()


async def subscription_handler(message: Message, session, i18n, user, **_):
    """Хендлер для показа информации о подписках и пополнении баланса"""
    
    # Получаем активные планы
    plans = await get_all_active_plans(session)
    
    # Получаем активную подписку пользователя
    active_subscription = await get_user_active_subscription(session, user.id)
    
    # Формируем текст с информацией о подписках
    text = i18n.get("subscription.title", "📦 Подписки и пополнение баланса")
    text += "\n\n"
    
    if active_subscription:
        text += i18n.get("subscription.active_info", 
                        "✅ <b>У вас активна подписка:</b>\n"
                        "📦 План: {plan_name}\n"
                        "💰 Стоимость: {price} руб.\n"
                        "📅 Действует до: {end_date}\n"
                        "🔄 Автопродление: {auto_renew}").format(
            plan_name=active_subscription.plan.name,
            price=active_subscription.plan.price,
            end_date=active_subscription.end_date.strftime("%d.%m.%Y"),
            auto_renew="Включено" if active_subscription.auto_renew else "Отключено"
        )
    else:
        text += i18n.get("subscription.no_active", "❌ <b>У вас нет активной подписки</b>")
    
    text += "\n\n"
    text += i18n.get("subscription.balance_info", 
                    "💰 <b>Ваш баланс:</b> {balance} руб.\n\n"
                    "Выберите действие:").format(balance=user.cash or 0)
    
    # Создаем клавиатуру с опциями
    keyboard = get_balance_keyboard(i18n, plans)
    
    await message.answer(text, reply_markup=keyboard)


async def balance_handler(callback: CallbackQuery, session, i18n, user, **_):
    """Хендлер для пополнения баланса"""
    
    text = i18n.get("balance.title", "💰 Пополнение баланса")
    text += "\n\n"
    text += i18n.get("balance.current", "Текущий баланс: {balance} руб.").format(balance=user.cash or 0)
    text += "\n\n"
    text += i18n.get("balance.enter_amount", 
                    "Введите сумму для пополнения (в рублях):\n"
                    "Минимум: 100 руб.\n"
                    "Максимум: 10000 руб.")
    
    # Создаем клавиатуру с быстрыми суммами
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="100 ₽", callback_data="balance:amount:100")],
        [InlineKeyboardButton(text="500 ₽", callback_data="balance:amount:500")],
        [InlineKeyboardButton(text="1000 ₽", callback_data="balance:amount:1000")],
        [InlineKeyboardButton(text="2000 ₽", callback_data="balance:amount:2000")],
        [InlineKeyboardButton(text="5000 ₽", callback_data="balance:amount:5000")],
        [InlineKeyboardButton(text="✏️ Ввести свою сумму", callback_data="balance:custom")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="subscription:back")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


async def balance_amount_handler(callback: CallbackQuery, session, i18n, user, redis, **_):
    """Хендлер для быстрого пополнения баланса"""
    
    # Извлекаем сумму из callback_data
    amount_str = callback.data.split(":")[-1]
    try:
        amount = float(amount_str)
    except ValueError:
        await callback.answer("❌ Неверная сумма", show_alert=True)
        return
    
    # Проверяем лимиты
    if amount < 100 or amount > 10000:
        await callback.answer("❌ Сумма должна быть от 100 до 10000 рублей", show_alert=True)
        return
    
    # Пополняем баланс
    success = await add_balance_to_user(session, user.id, amount, redis)
    
    if success:
        # Обновляем информацию о пользователе
        updated_user = await get_user_by_telegram_id(session, user.telegram_id)
        
        text = i18n.get("balance.success", 
                       "✅ <b>Баланс успешно пополнен!</b>\n\n"
                       "💰 Пополнено: {amount} руб.\n"
                       "💳 Новый баланс: {new_balance} руб.").format(
            amount=amount,
            new_balance=updated_user.cash
        )
        
        # Если у пользователя есть реферал, показываем информацию о бонусе
        if user.referred_by_id:
            bonus_amount = amount * 0.1
            text += f"\n\n🎁 <b>Реферальный бонус:</b> {bonus_amount} руб. добавлено пригласившему"
        
        await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 К подпискам", callback_data="subscription:back")]
        ]))
    else:
        await callback.answer("❌ Ошибка при пополнении баланса", show_alert=True)
    
    await callback.answer()


async def balance_custom_handler(callback: CallbackQuery, state: FSMContext, i18n, **_):
    """Хендлер для ввода произвольной суммы"""
    
    await state.set_state(SubscriptionStates.waiting_for_balance_amount)
    
    text = i18n.get("balance.custom_prompt", 
                   "✏️ <b>Введите сумму для пополнения</b>\n\n"
                   "Отправьте сообщение с суммой в рублях.\n"
                   "Например: <code>1500</code>\n\n"
                   "Минимум: 100 руб.\n"
                   "Максимум: 10000 руб.")
    
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Отмена", callback_data="balance:cancel")]
    ]))
    await callback.answer()


async def balance_custom_amount_handler(message: Message, state: FSMContext, session, i18n, user, redis, **_):
    """Хендлер для обработки введенной суммы"""
    
    try:
        amount = float(message.text)
    except ValueError:
        await message.answer("❌ Пожалуйста, введите корректную сумму (только цифры)")
        return
    
    # Проверяем лимиты
    if amount < 100:
        await message.answer("❌ Минимальная сумма пополнения: 100 рублей")
        return
    
    if amount > 10000:
        await message.answer("❌ Максимальная сумма пополнения: 10000 рублей")
        return
    
    # Пополняем баланс
    success = await add_balance_to_user(session, user.id, amount, redis)
    
    if success:
        # Обновляем информацию о пользователе
        updated_user = await get_user_by_telegram_id(session, user.telegram_id)
        
        text = i18n.get("balance.success", 
                       "✅ <b>Баланс успешно пополнен!</b>\n\n"
                       "💰 Пополнено: {amount} руб.\n"
                       "💳 Новый баланс: {new_balance} руб.").format(
            amount=amount,
            new_balance=updated_user.cash
        )
        
        # Если у пользователя есть реферал, показываем информацию о бонусе
        if user.referred_by_id:
            bonus_amount = amount * 0.1
            text += f"\n\n🎁 <b>Реферальный бонус:</b> {bonus_amount} руб. добавлено пригласившему"
        
        await message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 К подпискам", callback_data="subscription:back")]
        ]))
    else:
        await message.answer("❌ Ошибка при пополнении баланса")
    
    await state.clear()


async def balance_cancel_handler(callback: CallbackQuery, state: FSMContext, i18n, **_):
    """Хендлер для отмены пополнения баланса"""
    
    await state.clear()
    
    text = i18n.get("balance.cancelled", "❌ Пополнение баланса отменено")
    
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 К подпискам", callback_data="subscription:back")]
    ]))
    await callback.answer()


async def subscription_plans_handler(callback: CallbackQuery, session, i18n, user, **_):
    """Хендлер для показа доступных планов подписок"""
    
    # Получаем активные планы
    plans = await get_all_active_plans(session)
    
    if not plans:
        text = i18n.get("subscription.no_plans", "❌ <b>Нет доступных планов подписок</b>\n\nВ данный момент нет активных тарифных планов.")
        await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data="subscription:back")]
        ]))
        await callback.answer()
        return
    
    # Формируем текст с информацией о планах
    text = i18n.get("subscription.plans_title", "📦 <b>Доступные планы подписок</b>")
    text += "\n\n"
    
    for i, plan in enumerate(plans, 1):
        text += f"<b>{i}. {plan.name}</b>\n"
        text += f"💰 Стоимость: {plan.price} руб.\n"
        text += f"📱 Каналов: {plan.channels_limit}\n"
        text += f"📝 Постов: {plan.posts_limit}\n"
        text += f"✏️ Ручных постов: {plan.manual_posts_limit}\n"
        if plan.ai_priority:
            text += "🤖 Приоритет AI: ✅\n"
        if plan.description:
            text += f"📄 {plan.description}\n"
        text += "\n"
    
    text += i18n.get("subscription.plans_info", "Выберите план для оформления подписки:")
    
    # Создаем клавиатуру с планами
    from bot.keyboards.inline.subscription import get_plans_keyboard
    keyboard = get_plans_keyboard(plans, i18n)
    
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


async def plan_select_handler(callback: CallbackQuery, session, i18n, user, **_):
    """Хендлер для выбора плана подписки"""
    
    # Извлекаем ID плана из callback_data
    plan_id_str = callback.data.split(":")[-1]
    try:
        plan_id = int(plan_id_str)
    except ValueError:
        await callback.answer("❌ Неверный план", show_alert=True)
        return
    
    # Получаем план
    from bot.services.crud.plan import get_plan_by_id
    plan = await get_plan_by_id(session, plan_id)
    
    if not plan:
        await callback.answer("❌ План не найден", show_alert=True)
        return
    
    # Проверяем баланс пользователя
    from decimal import Decimal
    user_cash = Decimal(str(user.cash or 0))
    plan_price = Decimal(str(plan.price))
    
    if user_cash < plan_price:
        text = i18n.get("subscription.insufficient_balance", 
                       "❌ <b>Недостаточно средств</b>\n\n"
                       "💰 Ваш баланс: {balance} руб.\n"
                       "💳 Стоимость плана: {price} руб.\n\n"
                       "Пополните баланс для оформления подписки.").format(
            balance=user_cash,
            price=plan_price
        )
        
        await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💰 Пополнить баланс", callback_data="balance:topup")],
            [InlineKeyboardButton(text="🔙 К планам", callback_data="subscription:plans")]
        ]))
        await callback.answer()
        return
    
    # Формируем текст подтверждения
    remaining = user_cash - plan_price
    
    text = i18n.get("subscription.confirm_purchase", 
                   "✅ <b>Подтверждение покупки</b>\n\n"
                   "📦 План: {plan_name}\n"
                   "💰 Стоимость: {price} руб.\n"
                   "📱 Каналов: {channels}\n"
                   "📝 Постов: {posts}\n"
                   "✏️ Ручных постов: {manual_posts}\n"
                   "🤖 Приоритет AI: {ai_priority}\n\n"
                   "💳 Ваш баланс: {balance} руб.\n"
                   "💸 После покупки: {remaining} руб.\n\n"
                   "Подтвердите покупку:").format(
        plan_name=plan.name,
        price=plan_price,
        channels=plan.channels_limit,
        posts=plan.posts_limit,
        manual_posts=plan.manual_posts_limit,
        ai_priority="✅" if plan.ai_priority else "❌",
        balance=user_cash,
        remaining=remaining
    )
    
    # Создаем клавиатуру подтверждения
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"plan:confirm:{plan_id}")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="subscription:plans")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


async def plan_confirm_handler(callback: CallbackQuery, session, i18n, user, redis, **_):
    """Хендлер для подтверждения покупки плана"""
    
    # Извлекаем ID плана из callback_data
    plan_id_str = callback.data.split(":")[-1]
    try:
        plan_id = int(plan_id_str)
    except ValueError:
        await callback.answer("❌ Неверный план", show_alert=True)
        return
    
    # Получаем план
    from bot.services.crud.plan import get_plan_by_id
    plan = await get_plan_by_id(session, plan_id)
    
    if not plan:
        await callback.answer("❌ План не найден", show_alert=True)
        return
    
    # Проверяем баланс еще раз
    from decimal import Decimal
    user_cash = Decimal(str(user.cash or 0))
    plan_price = Decimal(str(plan.price))
    
    if user_cash < plan_price:
        await callback.answer("❌ Недостаточно средств", show_alert=True)
        return
    
    # Создаем подписку
    from datetime import datetime, timezone, timedelta
    start_date = datetime.now(timezone.utc)
    end_date = start_date + timedelta(days=30)  # 30 дней подписка
    
    subscription = await create_subscription(
        session,
        user_id=user.id,
        plan_id=plan.id,
        start_date=start_date,
        end_date=end_date,
        status='active',
        auto_renew=True
    )
    
    if subscription:
        # Списываем деньги с баланса
        user.cash = user_cash - plan_price
        await session.commit()
        
        # Очищаем кеш пользователя
        if redis and user.telegram_id:
            from bot.services.crud.user import clear_user_cache
            await clear_user_cache(redis, user.telegram_id)
        
        text = i18n.get("subscription.purchase_success", 
                       "🎉 <b>Подписка успешно оформлена!</b>\n\n"
                       "📦 План: {plan_name}\n"
                       "💰 Стоимость: {price} руб.\n"
                       "📅 Действует до: {end_date}\n"
                       "💳 Остаток баланса: {balance} руб.\n\n"
                       "Теперь вы можете использовать все возможности плана!").format(
            plan_name=plan.name,
            price=plan_price,
            end_date=end_date.strftime("%d.%m.%Y"),
            balance=user.cash
        )
        
        await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 К подпискам", callback_data="subscription:back")]
        ]))
    else:
        await callback.answer("❌ Ошибка при оформлении подписки", show_alert=True)
    
    await callback.answer()


async def subscription_back_handler(callback: CallbackQuery, session, i18n, user, **_):
    """Хендлер для возврата к подпискам"""
    
    # Получаем активные планы
    plans = await get_all_active_plans(session)
    
    # Получаем активную подписку пользователя
    active_subscription = await get_user_active_subscription(session, user.id)
    
    # Формируем текст с информацией о подписках
    text = i18n.get("subscription.title", "📦 Подписки и пополнение баланса")
    text += "\n\n"
    
    if active_subscription:
        text += i18n.get("subscription.active_info", 
                        "✅ <b>У вас активна подписка:</b>\n"
                        "📦 План: {plan_name}\n"
                        "💰 Стоимость: {price} руб.\n"
                        "📅 Действует до: {end_date}\n"
                        "🔄 Автопродление: {auto_renew}").format(
            plan_name=active_subscription.plan.name,
            price=active_subscription.plan.price,
            end_date=active_subscription.end_date.strftime("%d.%m.%Y"),
            auto_renew="Включено" if active_subscription.auto_renew else "Отключено"
        )
    else:
        text += i18n.get("subscription.no_active", "❌ <b>У вас нет активной подписки</b>")
    
    text += "\n\n"
    text += i18n.get("subscription.balance_info", 
                    "💰 <b>Ваш баланс:</b> {balance} руб.\n\n"
                    "Выберите действие:").format(balance=user.cash or 0)
    
    # Создаем клавиатуру с опциями
    keyboard = get_balance_keyboard(i18n, plans)
    
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


def register_subscription_handlers(router: Router):
    """Регистрирует хендлеры подписок"""
    
    # Основные хендлеры
    router.message.register(subscription_handler, Command("subscription"))
    router.message.register(subscription_handler, F.text.lower().contains("подписка"))
    router.message.register(subscription_handler, F.text.lower().contains("subscription"))
    
    # Callback хендлеры
    router.callback_query.register(balance_handler, F.data == "balance:topup")
    router.callback_query.register(balance_amount_handler, F.data.startswith("balance:amount:"))
    router.callback_query.register(balance_custom_handler, F.data == "balance:custom")
    router.callback_query.register(balance_cancel_handler, F.data == "balance:cancel")
    router.callback_query.register(subscription_back_handler, F.data == "subscription:back")
    router.callback_query.register(subscription_plans_handler, F.data == "subscription:plans")
    router.callback_query.register(plan_select_handler, F.data.startswith("plan:select:"))
    router.callback_query.register(plan_confirm_handler, F.data.startswith("plan:confirm:"))
    
    # FSM хендлеры
    router.message.register(balance_custom_amount_handler, SubscriptionStates.waiting_for_balance_amount)


__all__ = ["register_subscription_handlers"] 
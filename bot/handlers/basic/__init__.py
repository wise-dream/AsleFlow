from aiogram import Router

from .settings import register_settings_handler
from .start import register_start_handler
from .help import register_help_handler
from .about import register_about_handler
from .referral_input import register_referral_input_handlers
from .subscription import register_subscription_handlers

def register_basic_handlers(dp):
    router = Router()
    register_start_handler(router)
    register_help_handler(router)
    register_about_handler(router)
    register_settings_handler(router)
    register_referral_input_handlers(router)
    register_subscription_handlers(router)
    dp.include_router(router)

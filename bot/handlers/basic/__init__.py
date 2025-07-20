from aiogram import Router

from .settings import register_settings_handler
from .start import register_start_handler
from .help import register_help_handler
from .about import register_about_handler

def register_basic_handlers(dp):
    router = Router()
    register_start_handler(router)
    register_help_handler(router)
    register_about_handler(router)
    register_settings_handler(router)
    dp.include_router(router)

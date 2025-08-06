from aiogram import Router

from .add import register_add_social_handlers
from .social import register_social_accounts_handler
from .edit import register_manage_account_handlers

def register_socials_handlers(dp):
    router = Router()
    register_manage_account_handlers(router)
    register_social_accounts_handler(router)
    register_add_social_handlers(router)
    dp.include_router(router)

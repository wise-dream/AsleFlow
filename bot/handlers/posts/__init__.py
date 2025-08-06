from aiogram import Router

from .post import register_posts_handler
from .add import register_add_post_handlers
from .edit import register_edit_post_handlers

def register_posts_handlers(dp):
    router = Router()
    register_posts_handler(router)
    register_add_post_handlers(router)
    register_edit_post_handlers(router)
    dp.include_router(router) 
from aiogram import Router
from .workflow import register_workflows_handler
from .add import register_add_workflow_handlers
from .edit import register_edit_workflow_handlers

def register_workflow_handlers(dp):
    router = Router()
    register_workflows_handler(router)
    register_add_workflow_handlers(router)
    register_edit_workflow_handlers(router)
    dp.include_router(router)

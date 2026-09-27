from aiogram import Router

from handlers.task_actions import router as actions_router
from handlers.task_creation import router as creation_router
from handlers.task_views import router as views_router

router = Router()

router.include_router(creation_router)
router.include_router(actions_router)
router.include_router(views_router)
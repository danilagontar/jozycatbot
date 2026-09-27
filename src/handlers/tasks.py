from aiogram import Router

from handlers.mycreated import router as mycreated_router
from handlers.task_actions import router as actions_router
from handlers.task_creation import router as creation_router
from handlers.task_deadline import router as deadline_router
from handlers.task_views import router as views_router
from handlers.top import router as top_router


router = Router()

router.include_router(creation_router)
router.include_router(actions_router)
router.include_router(deadline_router)
router.include_router(views_router)
router.include_router(mycreated_router)
router.include_router(top_router)
from fastapi import APIRouter
from .users import router as users_router
from .roles import router as roles_router
from .audit import router as audit_router
from .models import router as models_router

router = APIRouter()

router.include_router(users_router)
router.include_router(roles_router)
router.include_router(audit_router)
router.include_router(models_router)
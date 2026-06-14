from fastapi import APIRouter
from .auth import router as auth_router
from .users import router as users_router
from .departments import router as departments_router
from .documents import router as documents_router
from .document_permissions import router as document_permissions_router
from .categories import router as categories_router
from .tags import router as tags_router
from .search import router as search_router
from .comments import router as comments_router
from .notifications import router as notifications_router
from .subscriptions import router as subscriptions_router
from .knowledge_graph import router as knowledge_graph_router
from .templates import router as templates_router
from .approvals import router as approvals_router
from .attachments import router as attachments_router
from .teams import router as teams_router
from .statistics import router as statistics_router
from .sso import router as sso_router
from .admin import router as admin_router
from .ai import router as ai_router

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(departments_router)
api_router.include_router(documents_router)
api_router.include_router(document_permissions_router)
api_router.include_router(categories_router)
api_router.include_router(tags_router)
api_router.include_router(search_router)
api_router.include_router(comments_router)
api_router.include_router(notifications_router)
api_router.include_router(subscriptions_router)
api_router.include_router(knowledge_graph_router)
api_router.include_router(templates_router)
api_router.include_router(approvals_router)
api_router.include_router(attachments_router)
api_router.include_router(teams_router)
api_router.include_router(statistics_router)
api_router.include_router(sso_router)
api_router.include_router(admin_router)
api_router.include_router(ai_router)
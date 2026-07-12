"""
Kiro API v1 Router

This module provides the main API router that combines all sub-routers.
"""
from fastapi import APIRouter

api_router = APIRouter()

# Platform routers
from kiro_platform.api.v1.auth import router as auth_router
from kiro_platform.api.v1.users import router as users_router
from kiro_platform.api.v1.teams import router as teams_router
from kiro_platform.api.v1.admin.users import router as admin_users_router
from kiro_platform.api.v1.admin.roles import router as admin_roles_router
from kiro_platform.api.v1.admin.audit import router as admin_audit_router
from kiro_platform.api.v1.admin.models import router as admin_models_router
from kiro_platform.api.v1.approvals import router as approvals_router
from kiro_platform.api.v1.comments import router as comments_router
from kiro_platform.api.v1.notifications import router as notifications_router
from kiro_platform.api.v1.sso import router as sso_router
from kiro_platform.api.v1.statistics import router as statistics_router
from kiro_platform.api.v1.subscriptions import router as subscriptions_router

# Knowledge base routers
from kiro_knbase.api.v1.documents import router as documents_router
from kiro_knbase.api.v1.ai import router as ai_router
from kiro_knbase.api.v1.search import router as search_router
from kiro_knbase.api.v1.categories import router as categories_router
from kiro_knbase.api.v1.tags import router as tags_router
from kiro_knbase.api.v1.attachments import router as attachments_router
from kiro_knbase.api.v1.document_permissions import router as document_permissions_router
from kiro_knbase.api.v1.knowledge_graph import router as knowledge_graph_router
from kiro_knbase.api.v1.templates import router as templates_router

# Include platform routers
api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(teams_router)
api_router.include_router(approvals_router)
api_router.include_router(comments_router)
api_router.include_router(notifications_router)
api_router.include_router(sso_router)
api_router.include_router(statistics_router)
api_router.include_router(subscriptions_router)

# Include admin routers
api_router.include_router(admin_users_router)
api_router.include_router(admin_roles_router)
api_router.include_router(admin_audit_router)
api_router.include_router(admin_models_router)

# Include knowledge base routers
api_router.include_router(documents_router)
api_router.include_router(ai_router)
api_router.include_router(search_router)
api_router.include_router(categories_router)
api_router.include_router(tags_router)
api_router.include_router(attachments_router)
api_router.include_router(document_permissions_router)
api_router.include_router(knowledge_graph_router)
api_router.include_router(templates_router)

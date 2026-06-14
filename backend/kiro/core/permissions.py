from enum import Enum
from typing import List


class UserRole(str, Enum):
    ADMIN = "admin"
    EDITOR = "editor"
    USER = "user"


class DocumentPermission(str, Enum):
    PUBLIC = "public"
    PRIVATE = "private"
    DEPARTMENT = "department"


class Permission:
    ROLE_PERMISSIONS = {
        UserRole.ADMIN: ["*"],
        UserRole.EDITOR: [
            "document:create",
            "document:edit",
            "document:delete",
            "category:manage",
            "tag:manage",
        ],
        UserRole.USER: [
            "document:read",
            "document:comment",
            "document:share",
        ]
    }

    @staticmethod
    def has_permission(role: UserRole, required_permission: str) -> bool:
        permissions = Permission.ROLE_PERMISSIONS.get(role, [])
        if "*" in permissions:
            return True
        return required_permission in permissions

    @staticmethod
    def get_role_permissions(role: UserRole) -> List[str]:
        return Permission.ROLE_PERMISSIONS.get(role, [])


def require_permission(permission: str):
    def decorator(func):
        func._required_permission = permission
        return func
    return decorator

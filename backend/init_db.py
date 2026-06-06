#!/usr/bin/env python
"""
数据库初始化脚本
用于创建所有数据库表
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from knpy.core.database import engine, Base
from knpy.models import *

print("Creating database tables...")
Base.metadata.create_all(bind=engine)
print("Database tables created successfully!")

from knpy.core.database import SessionLocal
from knpy.core.security import get_password_hash
from knpy.models import User, Role

db = SessionLocal()
try:
    existing_admin = db.query(User).filter(User.email == "admin@example.com").first()
    if not existing_admin:
        admin = User(
            email="admin@example.com",
            username="admin",
            hashed_password=get_password_hash("admin123"),
            full_name="Administrator",
            role="admin",
            is_active=True
        )
        db.add(admin)
        db.commit()
        print("Admin user created: admin@example.com / admin123")
    else:
        print("Admin user already exists")
    
    existing_roles = db.query(Role).all()
    if not existing_roles:
        roles = [
            Role(name="管理员", code="admin", description="系统管理员，拥有所有权限", permissions='["*"]'),
            Role(name="编辑者", code="editor", description="内容编辑者，可以创建和编辑文档", permissions='["document.create", "document.edit", "document.delete"]'),
            Role(name="普通用户", code="user", description="普通用户，可以查看文档", permissions='["document.view"]')
        ]
        db.add_all(roles)
        db.commit()
        print("Default roles created successfully!")
        for role in roles:
            print(f"  - {role.name} ({role.code})")
    else:
        print(f"Default roles already exist: {len(existing_roles)} roles")
finally:
    db.close()
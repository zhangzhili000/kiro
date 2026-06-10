#!/usr/bin/env python
"""
数据库迁移脚本
用于创建所有缺失的表和字段
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from kiro.core.database import engine, Base
from kiro.models import *

print("Recreating all database tables...")
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)
print("All database tables created successfully!")
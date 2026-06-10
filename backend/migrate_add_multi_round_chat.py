"""
数据库迁移脚本：添加多轮对话功能相关字段和索引
用法: python migrate_add_multi_round_chat.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# 数据库配置
DB_CONFIG = {
    'host': 'localhost',
    'port': '5432',
    'user': 'postgres',
    'password': '123456',
    'dbname': 'kiro'
}

MIGRATION_SQL = """
-- 1. 添加对话模式字段
ALTER TABLE ai_conversations ADD COLUMN IF NOT EXISTS conversation_mode VARCHAR(20) DEFAULT 'fast_qa';

-- 2. 添加历史对话摘要字段
ALTER TABLE ai_conversations ADD COLUMN IF NOT EXISTS history_summary TEXT;

-- 3. 添加user_id索引（如果不存在）
CREATE INDEX IF NOT EXISTS idx_ai_conversations_user_id ON ai_conversations(user_id);

-- 4. 添加created_at索引（如果不存在）
CREATE INDEX IF NOT EXISTS idx_ai_conversations_created_at ON ai_conversations(created_at DESC);

-- 5. 添加conversation_uuid索引（如果不存在）
CREATE INDEX IF NOT EXISTS idx_ai_conversations_conversation_uuid ON ai_conversations(conversation_uuid);

-- 6. 添加注释
COMMENT ON COLUMN ai_conversations.conversation_mode IS 'Conversation mode: fast_qa-quick Q&A, multi_round-multi-round chat';
COMMENT ON COLUMN ai_conversations.history_summary IS 'History conversation summary (for multi-round chat)';
"""

def run_migration():
    """Execute database migration"""
    try:
        print("Starting database migration...")
        print(f"Connecting to database: {DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['dbname']}")

        # Connect to database
        conn = psycopg2.connect(**DB_CONFIG)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()

        # Execute migration SQL
        cursor.execute(MIGRATION_SQL)

        print("\n[OK] Migration completed successfully!")
        print("\nAdded:")
        print("  - conversation_mode field (conversation mode)")
        print("  - history_summary field (history conversation summary)")
        print("  - user_id index")
        print("  - created_at index")
        print("  - conversation_uuid index")

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"\n[ERROR] Migration failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    run_migration()
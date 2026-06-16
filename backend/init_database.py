"""
数据库初始化脚本
用法: python init_database.py
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

# 建表SQL - 按依赖顺序排列
CREATE_TABLES_SQL = """
-- 1. 部门表 (无依赖)
CREATE TABLE IF NOT EXISTS departments (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    parent_id INTEGER REFERENCES departments(id),
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. 用户表 (依赖 departments)
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(100),
    avatar VARCHAR(500),
    phone VARCHAR(20),
    role VARCHAR(20) DEFAULT 'user',
    department_id INTEGER REFERENCES departments(id),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. 分类表 (无依赖)
CREATE TABLE IF NOT EXISTS categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    parent_id INTEGER REFERENCES categories(id),
    description TEXT,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. 标签表 (无依赖)
CREATE TABLE IF NOT EXISTS tags (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    color VARCHAR(7) DEFAULT '#409EFF',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. 文档表 (依赖 users, categories, departments)
CREATE TABLE IF NOT EXISTS documents (
    id SERIAL PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    content TEXT,
    html_content TEXT,
    summary TEXT,
    keywords JSONB,
    author_id INTEGER REFERENCES users(id),
    category_id INTEGER REFERENCES categories(id),
    permission VARCHAR(20) DEFAULT 'public',
    department_id INTEGER REFERENCES departments(id),
    status VARCHAR(20) DEFAULT 'draft',
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMP,
    deleted_by INTEGER REFERENCES users(id),
    view_count INTEGER DEFAULT 0,
    like_count INTEGER DEFAULT 0,
    comment_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 6. 文档版本表 (依赖 documents)
CREATE TABLE IF NOT EXISTS document_versions (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    version_number INTEGER NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(document_id, version_number)
);

-- 7. 文档标签关联表 (依赖 documents, tags)
CREATE TABLE IF NOT EXISTS document_tags (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    tag_id INTEGER REFERENCES tags(id) ON DELETE CASCADE,
    UNIQUE(document_id, tag_id)
);

-- 8. 评论表 (依赖 documents, users)
CREATE TABLE IF NOT EXISTS comments (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id),
    parent_id INTEGER REFERENCES comments(id),
    content TEXT NOT NULL,
    is_deleted BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 9. 用户收藏表 (依赖 users, documents)
CREATE TABLE IF NOT EXISTS user_favorites (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, document_id)
);

-- 10. 文档点赞表 (依赖 users, documents)
CREATE TABLE IF NOT EXISTS document_likes (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, document_id)
);

-- 11. 文档分享表 (依赖 documents)
CREATE TABLE IF NOT EXISTS document_shares (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    share_token VARCHAR(100) UNIQUE NOT NULL,
    created_by INTEGER REFERENCES users(id),
    expires_at TIMESTAMP,
    view_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 12. 通知表 (依赖 users, documents)
CREATE TABLE IF NOT EXISTS notifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(200) NOT NULL,
    content TEXT,
    notification_type VARCHAR(50),
    is_read BOOLEAN DEFAULT FALSE,
    related_document_id INTEGER REFERENCES documents(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 13. 审计日志表 (依赖 users)
CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    action VARCHAR(50) NOT NULL,
    resource_type VARCHAR(50),
    resource_id INTEGER,
    details TEXT,
    ip_address VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 14. 搜索历史表 (依赖 users)
CREATE TABLE IF NOT EXISTS search_history (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    keyword VARCHAR(200) NOT NULL,
    search_type VARCHAR(20) DEFAULT 'fulltext',
    result_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 15. 文档模板表 (依赖 users, categories)
CREATE TABLE IF NOT EXISTS document_templates (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    content TEXT,
    category_id INTEGER REFERENCES categories(id),
    created_by INTEGER REFERENCES users(id),
    is_public BOOLEAN DEFAULT TRUE,
    is_active BOOLEAN DEFAULT TRUE,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 16. 审批模板表 (无依赖)
CREATE TABLE IF NOT EXISTS approval_templates (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    flow_config JSONB,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 17. 审批记录表 (依赖 documents, approval_templates, users)
CREATE TABLE IF NOT EXISTS approval_records (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    template_id INTEGER REFERENCES approval_templates(id),
    current_step INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'pending',
    submitted_by INTEGER REFERENCES users(id),
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    approved_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 18. 审批历史表 (依赖 approval_records, users)
CREATE TABLE IF NOT EXISTS approval_history (
    id SERIAL PRIMARY KEY,
    approval_id INTEGER REFERENCES approval_records(id) ON DELETE CASCADE,
    step INTEGER NOT NULL,
    approver_id INTEGER REFERENCES users(id),
    action VARCHAR(20) NOT NULL,
    comment TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 19. 附件表 (依赖 documents, users)
CREATE TABLE IF NOT EXISTS attachments (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    original_filename VARCHAR(500) NOT NULL,
    stored_filename VARCHAR(500) NOT NULL,
    file_size BIGINT,
    content_type VARCHAR(100),
    uploaded_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 20. 团队表 (无依赖)
CREATE TABLE IF NOT EXISTS teams (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    icon VARCHAR(500),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 21. 团队成员表 (依赖 teams, users)
CREATE TABLE IF NOT EXISTS team_members (
    id SERIAL PRIMARY KEY,
    team_id INTEGER REFERENCES teams(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(20) DEFAULT 'member',
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(team_id, user_id)
);

-- 22. 团队文档表 (依赖 teams, documents)
CREATE TABLE IF NOT EXISTS team_documents (
    id SERIAL PRIMARY KEY,
    team_id INTEGER REFERENCES teams(id) ON DELETE CASCADE,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(team_id, document_id)
);

-- 23. 订阅表 (依赖 users)
CREATE TABLE IF NOT EXISTS subscriptions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    subscription_type VARCHAR(20) NOT NULL,
    target_id INTEGER NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 24. 角色表
CREATE TABLE IF NOT EXISTS roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    code VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    permissions TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 25. 文档权限表 (依赖 documents)
CREATE TABLE IF NOT EXISTS document_permissions (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    permission_type VARCHAR(20) NOT NULL,
    target_id INTEGER NOT NULL,
    action VARCHAR(20) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 26. 知识图谱节点表 (依赖 documents)
CREATE TABLE IF NOT EXISTS knowledge_graph_nodes (
    id SERIAL PRIMARY KEY,
    node_type VARCHAR(20) NOT NULL CHECK (node_type IN ('document', 'concept', 'entity', 'event')),
    title VARCHAR(500) NOT NULL,
    description TEXT,
    document_id INTEGER REFERENCES documents(id),
    embedding TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 27. 知识图谱关系表 (依赖 knowledge_graph_nodes)
CREATE TABLE IF NOT EXISTS knowledge_graph_relations (
    id SERIAL PRIMARY KEY,
    source_node_id INTEGER REFERENCES knowledge_graph_nodes(id) ON DELETE CASCADE,
    target_node_id INTEGER REFERENCES knowledge_graph_nodes(id) ON DELETE CASCADE,
    relation_type VARCHAR(20) NOT NULL CHECK (relation_type IN ('related_to', 'contains', 'references', 'derived_from', 'similar_to')),
    confidence FLOAT DEFAULT 1.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 28. 文档向量表 (依赖 documents)
CREATE TABLE IF NOT EXISTS document_vectors (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    chunk_content TEXT NOT NULL,
    chunk_summary TEXT,
    keywords JSONB,
    vector_data BYTEA NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- 29. AI对话记录表 (依赖 users)
CREATE TABLE IF NOT EXISTS ai_conversations (
    id SERIAL PRIMARY KEY,
    conversation_uuid VARCHAR(36) UNIQUE NOT NULL,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255),
    question TEXT NOT NULL,
    question_analysis TEXT,
    answer TEXT NOT NULL,
    referenced_docs JSONB,
    model VARCHAR(100),
    tokens INTEGER DEFAULT 0,
    question_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    answer_time TIMESTAMP,
    duration INTEGER DEFAULT 0,
    processing_steps JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- 30. AI配置表
CREATE TABLE IF NOT EXISTS ai_config (
    id SERIAL PRIMARY KEY,
    role_definition JSONB NOT NULL,
    rules JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- 31. 提示词模板表
CREATE TABLE IF NOT EXISTS prompt_templates (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL,
    description TEXT,
    content TEXT NOT NULL,
    is_active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- 32. AI模型配置表
CREATE TABLE IF NOT EXISTS model_config (
    id SERIAL PRIMARY KEY,
    type VARCHAR(50) NOT NULL,
    api_type VARCHAR(50) NOT NULL,
    model_id VARCHAR(255) NOT NULL,
    api_key VARCHAR(500) NOT NULL,
    api_base VARCHAR(500),
    description TEXT,
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);
"""

# 默认数据
DEFAULT_DATA_SQL = """
-- 角色数据
INSERT INTO roles (name, code, description, permissions)
VALUES 
    ('管理员', 'admin', '系统管理员，拥有所有权限', '["*"]'),
    ('编辑者', 'editor', '内容编辑者，可以创建和编辑文档', '["document.create", "document.edit", "document.delete"]'),
    ('普通用户', 'user', '普通用户，可以查看文档', '["document.read"]')
ON CONFLICT (code) DO NOTHING;

-- 管理员用户 (密码: admin123)
INSERT INTO users (email, username, hashed_password, full_name, role, is_active)
VALUES ('admin@example.com', 'admin', '$2b$12$H75sEPd/AEG3DohXNRQr6u1rAwjcNCLmV7LZYH9Nqf1Kzz0NeR.Sq', 'Administrator', 'admin', TRUE)
ON CONFLICT (email) DO NOTHING;

-- 测试用户 (密码: user123)
INSERT INTO users (email, username, hashed_password, full_name, role, is_active)
VALUES ('user@example.com', 'user', '$2b$12$e27rIeGFgL2Lfv9BrHuivu1dY7iaWcKHLXHtN/2VGSeHbwQgiemt6', 'Test User', 'user', TRUE)
ON CONFLICT (email) DO NOTHING;

-- 示例文档
INSERT INTO documents (title, content, permission, author_id)
VALUES ('欢迎使用企业知识库', '# 欢迎使用企业知识库\n\n这是一个帮助企业管理和共享知识的平台。\n\n## 功能特点\n\n- 文档管理\n- 知识搜索\n- 团队协作\n- 版本控制', 'public', 1)
ON CONFLICT DO NOTHING;

-- 示例分类
INSERT INTO categories (name, description)
VALUES ('技术文档', '技术相关文档'), ('产品文档', '产品相关文档')
ON CONFLICT DO NOTHING;

-- 示例标签
INSERT INTO tags (name)
VALUES ('重要'), ('更新'), ('教程')
ON CONFLICT DO NOTHING;

-- AI配置初始化
INSERT INTO ai_config (role_definition, rules)
VALUES (
    '{
        "name": "企业知识库智能助手",
        "description": "您的专属企业知识库智能助手，致力于为您提供准确、专业的知识服务。我可以帮助您查询文档、解答问题、分析信息。",
        "guidelines": "1. 始终保持专业、友好的态度\n2. 回答必须基于知识库内容\n3. 对于不确定的问题，明确告知用户\n4. 保护用户隐私和企业机密\n5. 遵守企业的信息安全政策\n6. 提供清晰、结构化的回答\n7. 必要时引用参考来源"
    }',
    '{
        "answerStrategy": "hybrid",
        "maxAnswerLength": 2000,
        "citeSources": true,
        "temperature": 0.7,
        "domains": ["data_standard", "law", "technical", "business"]
    }'
)
ON CONFLICT DO NOTHING;

-- 提示词模板
INSERT INTO prompt_templates (name, type, description, content)
VALUES 
    ('角色定义模板', 'role', 'AI助手的角色定义', '你是企业知识库的智能助手，专注于帮助用户查找和理解企业内部的知识文档。你的目标是提供准确、有用的信息，帮助用户解决工作中的问题。'),
    ('知识库回答规则', 'rule', '基于知识库回答的规则', '1. 优先从提供的参考文档中提取信息\n2. 如果文档中有明确答案，直接引用并标注来源\n3. 如果文档内容冲突，指出不同观点\n4. 如果没有相关文档，告知用户无法回答\n5. 回答要简洁明了，避免冗长'),
    ('直接回答规则', 'rule', '直接回答的规则', '1. 对于常见问题和常识性问题，可以直接回答\n2. 对于系统相关问题，提供使用指导\n3. 对于闲聊，保持友好回应\n4. 对于超出知识范围的问题，礼貌拒绝'),
    ('格式要求', 'format', '回答格式要求', '1. 使用Markdown格式组织内容\n2. 使用列表、标题等结构化元素\n3. 代码片段使用反引号包裹\n4. 引用来源时使用方括号标注')
ON CONFLICT DO NOTHING;
"""


def create_database():
    """创建数据库（如果不存在）"""
    try:
        conn = psycopg2.connect(
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            dbname='postgres'
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = '{DB_CONFIG['dbname']}'")
        if not cursor.fetchone():
            cursor.execute(f"CREATE DATABASE {DB_CONFIG['dbname']}")
            print(f"✓ 数据库 '{DB_CONFIG['dbname']}' 创建成功")
        else:
            print(f"✓ 数据库 '{DB_CONFIG['dbname']}' 已存在")
        
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"✗ 创建数据库失败: {e}")
        return False


def init_tables_and_data():
    """初始化表结构和默认数据"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        print("创建数据表...")
        cursor.execute(CREATE_TABLES_SQL)
        print("✓ 数据表创建成功")
        
        print("插入默认数据...")
        cursor.execute(DEFAULT_DATA_SQL)
        print("✓ 默认数据插入成功")
        
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"✗ 初始化失败: {e}")
        return False


if __name__ == "__main__":
    print("=" * 50)
    print("企业知识库 - 数据库初始化")
    print("=" * 50)
    
    if create_database() and init_tables_and_data():
        print("=" * 50)
        print("✓ 数据库初始化完成!")
        print("=" * 50)
        print("\n已创建的表:")
        print("  - users, departments, categories, tags")
        print("  - documents, document_versions, document_tags")
        print("  - comments, user_favorites, document_likes")
        print("  - document_shares, notifications, audit_logs")
        print("  - search_history, document_templates")
        print("  - approval_templates, approval_records, approval_history")
        print("  - attachments, teams, team_members, team_documents")
        print("  - subscriptions, roles, document_permissions")
        print("  - knowledge_graph_nodes, knowledge_graph_relations")
        print("  - document_vectors, ai_conversations, ai_config, prompt_templates, model_config")
        print("\nAI配置已初始化:")
        print("  - 角色定义: 企业知识库智能助手")
        print("  - 回答策略: 混合模式(hybrid)")
        print("  - 提示词模板: 4个模板已创建")
        print("\n默认账号:")
        print("  管理员: admin@example.com / admin123")
        print("  测试用户: user@example.com / user123")
        print("\n默认角色:")
        print("  管理员 (admin) - 拥有所有权限")
        print("  编辑者 (editor) - 可创建和编辑文档")
        print("  普通用户 (user) - 可查看文档")
    else:
        print("\n✗ 初始化失败，请检查配置")
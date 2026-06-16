from sqlalchemy import inspect
from kiro.core.database import engine, Base
from kiro.models import (
    User, Department, Document, DocumentVersion, DocumentShare,
    Category, Tag, DocumentTag, Comment, UserFavorite, DocumentLike,
    Subscription, Notification, AuditLog, SearchHistory, Role,
    AIConfig, PromptTemplate, DocumentVector, AIConversation,
    DocumentTemplate, ModelConfig, DocumentPermission
)


def init_db():
    print("Initializing database...")
    inspector = inspect(engine)

    existing_tables = inspector.get_table_names()

    tables_to_create = [
        Department.__table__,
        User.__table__,
        Category.__table__,
        Tag.__table__,
        Document.__table__,
        DocumentTag.__table__,
        DocumentVersion.__table__,
        DocumentShare.__table__,
        DocumentPermission.__table__,
        Comment.__table__,
        UserFavorite.__table__,
        DocumentLike.__table__,
        Subscription.__table__,
        Notification.__table__,
        AuditLog.__table__,
        SearchHistory.__table__,
        Role.__table__,
        DocumentVector.__table__,
        AIConversation.__table__,
        AIConfig.__table__,
        PromptTemplate.__table__,
        DocumentTemplate.__table__,
        ModelConfig.__table__,
    ]

    for table in tables_to_create:
        if table.name not in existing_tables:
            table.create(engine)
            print(f"Created table: {table.name}")
        else:
            print(f"Table already exists: {table.name}")

    print("Database initialization complete!")


def create_admin_user():
    from kiro.core.security import get_password_hash
    from kiro.core.database import SessionLocal

    db = SessionLocal()
    try:
        existing_admin = db.query(User).filter(User.email == "admin@example.com").first()
        if existing_admin:
            print("Admin user already exists")
            return

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
    finally:
        db.close()


def create_default_roles():
    from kiro.core.database import SessionLocal

    db = SessionLocal()
    try:
        existing_roles = db.query(Role).all()
        if existing_roles:
            print(f"Default roles already exist: {len(existing_roles)} roles")
            return

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
    finally:
        db.close()


def create_default_ai_config():
    from kiro.core.database import SessionLocal

    db = SessionLocal()
    try:
        existing_config = db.query(AIConfig).first()
        if existing_config:
            print("AI config already exists")
            return

        ai_config = AIConfig(
            role_definition={
                "name": "企业知识库智能助手",
                "description": "您的专属企业知识库智能助手，致力于为您提供准确、专业的知识服务。我可以帮助您查询文档、解答问题、分析信息。",
                "guidelines": "1. 始终保持专业、友好的态度\n2. 回答必须基于知识库内容\n3. 对于不确定的问题，明确告知用户\n4. 保护用户隐私和企业机密\n5. 遵守企业的信息安全政策\n6. 提供清晰、结构化的回答\n7. 必要时引用参考来源"
            },
            rules={
                "answerStrategy": "hybrid",
                "maxAnswerLength": 2000,
                "citeSources": True,
                "temperature": 0.7,
                "domains": ["data_standard", "law", "technical", "business"]
            }
        )
        db.add(ai_config)
        
        templates = [
            PromptTemplate(
                name="角色定义模板",
                type="role",
                description="AI助手的角色定义",
                content="你是企业知识库的智能助手，专注于帮助用户查找和理解企业内部的知识文档。你的目标是提供准确、有用的信息，帮助用户解决工作中的问题。"
            ),
            PromptTemplate(
                name="知识库回答规则",
                type="rule",
                description="基于知识库回答的规则",
                content="1. 优先从提供的参考文档中提取信息\n2. 如果文档中有明确答案，直接引用并标注来源\n3. 如果文档内容冲突，指出不同观点\n4. 如果没有相关文档，告知用户无法回答\n5. 回答要简洁明了，避免冗长"
            ),
            PromptTemplate(
                name="直接回答规则",
                type="rule",
                description="直接回答的规则",
                content="1. 对于常见问题和常识性问题，可以直接回答\n2. 对于系统相关问题，提供使用指导\n3. 对于闲聊，保持友好回应\n4. 对于超出知识范围的问题，礼貌拒绝"
            ),
            PromptTemplate(
                name="格式要求",
                type="format",
                description="回答格式要求",
                content="1. 使用Markdown格式组织内容\n2. 使用列表、标题等结构化元素\n3. 代码片段使用反引号包裹\n4. 引用来源时使用方括号标注"
            )
        ]
        
        db.add_all(templates)
        db.commit()
        print("AI config and prompt templates created successfully!")
        print("  - AI配置已初始化")
        print("  - 4个提示词模板已创建")
    finally:
        db.close()


if __name__ == "__main__":
    init_db()
    create_admin_user()
    create_default_roles()
    create_default_ai_config()

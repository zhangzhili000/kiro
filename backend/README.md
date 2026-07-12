# 企业知识库后端

## 环境要求

- Python 3.11+
- PostgreSQL 15+ (需要单独安装)
- Redis 7+ (可选)

## 安装

1. 创建虚拟环境：
```bash
cd backend
python -m venv venv
.\venv\Scripts\activate
```

2. 安装依赖：
```bash
pip install -r requirements.txt
```

3. 安装PostgreSQL数据库驱动（需要先安装PostgreSQL）：
```bash
pip install psycopg2-binary
```

4. 配置环境变量：
创建 `.env` 文件，内容如下：
```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/kiro
SECRET_KEY=your-secret-key-change-in-production
```

## 数据库初始化

1. 创建数据库：
```sql
CREATE DATABASE kiro;
```

2. 初始化表结构和默认数据：
```bash
cd backend
python -m kiro.utils.init_db
```

## 运行

```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

访问 http://localhost:8000/docs 查看API文档。

## 默认账号

- 邮箱：admin@example.com
- 密码：admin123

## 项目结构

```
backend/
├── kiro/
│   ├── api/v1/       # API路由
│   ├── core/         # 核心配置
│   ├── models/       # 数据库模型
│   ├── schemas/      # Pydantic模型
│   ├── services/     # 业务逻辑
│   ├── utils/        # 工具函数
│   └── main.py       # 应用入口
├── requirements.txt
└── README.md
```

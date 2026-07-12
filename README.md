# 企业知识库管理系统

中文 | [English](./README-en.md)

一个基于 AI 的企业级知识库管理系统，提供文档管理、知识图谱、智能问答等功能。

## 📋 项目简介

本系统旨在帮助企业高效管理和利用内部知识资源，通过 AI 技术实现智能问答、文档理解和知识关联。

## ✨ 功能特性

### 核心功能
- **文档管理** - 支持文档的上传、编辑、版本控制和权限管理
- **知识图谱** - 自动构建文档之间的知识关联网络
- **智能搜索** - 基于语义理解的全文搜索
- **AI 助手** - 集成大模型，支持智能问答和文档总结
- **团队协作** - 支持团队管理和文档协作
- **审批流程** - 文档发布审批机制

### 技术特性
- 前后端分离架构
- RESTful API 设计
- 支持 OAuth2.0 单点登录
- 实时通知推送
- 完整的权限控制系统

## 🛠️ 技术栈

### 后端
| 技术 | 版本 | 说明 |
|------|------|------|
| Python | 3.11+ | 编程语言 |
| FastAPI | 0.100+ | Web 框架 |
| SQLAlchemy | 2.0+ | ORM |
| PostgreSQL | 15+ | 数据库 |
| Redis | 7+ | 缓存 |
| FAISS | 1.7+ | 向量检索 |

### 前端
| 技术 | 版本 | 说明 |
|------|------|------|
| Vue.js | 3+ | 前端框架 |
| Vite | 5+ | 构建工具 |
| Pinia | 2+ | 状态管理 |
| Tailwind CSS | 3+ | 样式框架 |
| Vue Router | 4+ | 路由管理 |

## 🚀 快速开始

### 环境要求
- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Redis 7+

### 本地开发

#### 1. 克隆项目
```bash
git clone https://github.com/zhangzhili000/kiro.git
cd kiro
```

#### 2. 使用 Docker Compose 启动（推荐）

```bash
# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps
```

**服务访问地址：**
- 前端：http://localhost:5120
- 后端 API：http://localhost:8000
- API 文档：http://localhost:8000/docs

**服务说明：**
| 服务 | 端口 | 说明 |
| :--- | :--- | :--- |
| db | 5432 | PostgreSQL 数据库 |
| redis | 6379 | Redis 缓存 |
| backend | 8000 | 后端服务 |
| frontend | 5120 | 前端服务 |

#### 3. 手动启动（开发模式）

**启动后端：**
```bash
cd backend

# 安装依赖
pip install -r requirements.txt
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**启动前端：**
```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

### 数据库初始化

```sql
-- 创建数据库
CREATE DATABASE kiro;

-- 创建用户
CREATE USER kiro WITH ENCRYPTED PASSWORD 'your_password';

-- 授予权限
GRANT ALL PRIVILEGES ON DATABASE kiro TO kiro;
```

运行数据库迁移：
```bash
cd backend
python migrate_db.py
```

## ⚙️ 环境变量配置

### 后端环境变量

| 变量名 | 说明 | 默认值 |
| :--- | :--- | :--- |
| DATABASE_URL | 数据库连接地址 | postgresql://kiro:kiro123@localhost:5432/kiro |
| REDIS_URL | Redis 连接地址 | redis://localhost:6379/0 |
| SECRET_KEY | JWT 密钥 | your-secret-key-change-in-production |
| APP_NAME | 应用名称 | Kiro AI Platform |
| APP_VERSION | 应用版本 | 1.1.0 |
| DEBUG | 调试模式 | False |
| HOST | 服务监听地址 | 0.0.0.0 |
| PORT | 服务监听端口 | 8000 |
| CORS_ORIGINS | CORS 允许的来源 | ["*"] |
| VECTOR_DIMENSION | 向量维度 | 1536 |

### 前端环境变量

| 变量名 | 说明 | 默认值 |
| :--- | :--- | :--- |
| VITE_API_BASE_URL | 后端 API 地址 | http://localhost:8000/api/v1 |

## 📁 项目结构

```
.
├── backend/                    # 后端代码
│   ├── kiro_knbase/           # 知识库模块
│   │   ├── api/               # API 路由
│   │   ├── models/            # 数据库模型
│   │   ├── schemas/           # 数据结构定义
│   │   ├── services/          # 业务逻辑层
│   │   └── vector/            # 向量检索
│   ├── kiro_platform/         # 基座平台
│   │   ├── api/               # API 路由
│   │   ├── models/            # 数据库模型
│   │   ├── schemas/           # 数据结构定义
│   │   └── services/          # 业务逻辑层
│   ├── migrations/            # 数据库迁移脚本
│   ├── main.py                # 应用入口
│   ├── requirements.txt       # 依赖清单
│   └── Dockerfile             # Docker 构建文件
├── frontend/                  # 前端代码
│   ├── src/                   # 源代码
│   │   ├── api/               # API 调用
│   │   ├── components/        # 组件
│   │   ├── layouts/           # 布局组件
│   │   ├── stores/            # 状态管理
│   │   ├── views/             # 页面视图
│   │   └── router/            # 路由配置
│   ├── package.json           # 前端依赖
│   └── Dockerfile             # Docker 构建文件
├── docker-compose.yml         # Docker Compose 配置
├── README.md                  # 项目说明
├── README-en.md               # 英文说明
└── LICENSE                    # 许可证
```

## 🔧 开发指南

### 代码规范
- 后端：遵循 PEP 8 规范
- 前端：使用 ESLint 检查

### API 文档

启动后端服务后，访问以下地址查看 API 文档：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 测试

**后端测试：**
```bash
cd backend
python -m pytest
```

**前端测试：**
```bash
cd frontend
npm test
```

## 📦 Docker 部署

### Docker Compose

```bash
# 启动服务
docker-compose up -d

# 停止服务
docker-compose down

# 查看日志
docker-compose logs -f

# 重建服务
docker-compose up -d --build
```

### 生产环境配置

1. **修改默认密码**：在 docker-compose.yml 中修改数据库密码
2. **配置 HTTPS**：使用 Nginx 作为反向代理
3. **限制 CORS**：修改后端配置中的 CORS_ORIGINS

## 🌐 AI 模型配置

### 配置流程

1. 登录系统管理员账号
2. 进入"模型管理"页面
3. 添加模型配置（支持多种 API 类型）：
   - 百炼
   - DeepSeek
   - OpenAI 兼容
   - 智谱
   - 硅基流动
   - 自定义 API
4. 设置默认模型

## 📖 API 文档

### 核心接口

| 模块 | 接口前缀 | 说明 |
| :--- | :--- | :--- |
| 用户认证 | `/api/v1/auth` | 登录、注册、验证 |
| 文档管理 | `/api/v1/documents` | 文档 CRUD、上传、处理 |
| AI 问答 | `/api/v1/ai` | 智能问答、文档总结 |
| 分类管理 | `/api/v1/categories` | 文档分类 |
| 标签管理 | `/api/v1/tags` | 文档标签 |
| 团队管理 | `/api/v1/teams` | 团队管理 |

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 📞 联系方式

如有问题或建议，请通过以下方式联系：
- 提交 Issue
- 发送邮件至 1109723336@qq.com

---

**注意**: 这是一个企业级知识库管理系统的开源版本，部分企业功能可能已移除或简化。
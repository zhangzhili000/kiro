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
| Python | 3.13+ | 编程语言 |
| FastAPI | 0.100+ | Web 框架 |
| SQLAlchemy | 2.0+ | ORM |
| PostgreSQL | 15+ | 数据库 |
| Redis | 7+ | 缓存 |

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
- Python 3.13+
- Node.js 20+
- PostgreSQL 15+
- Redis 7+

### 本地开发

#### 1. 克隆项目
```bash
git clone https://github.com/zhangzhili000/kiro.git
cd kiro
```

#### 2. 启动后端服务
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### 3. 启动前端服务
```bash
cd frontend
npm install
npm run dev
```

#### 4. 访问应用
- 前端: http://localhost:5173
- 后端 API: http://localhost:8000

### Docker 部署

```bash
docker-compose up -d
```

## 📁 项目结构

```
.
├── backend/                    # 后端代码
│   ├── kiro/                  # 应用主目录
│   │   ├── api/              # API 路由
│   │   │   └── v1/           # 版本化 API
│   │   ├── core/             # 核心配置
│   │   ├── models/           # 数据库模型
│   │   ├── schemas/          # 数据结构定义
│   │   ├── services/         # 业务逻辑层
│   │   └── utils/            # 工具函数
│   └── requirements.txt      # 依赖清单
├── frontend/                  # 前端代码
│   ├── src/                  # 源代码
│   │   ├── api/             # API 调用
│   │   ├── components/       # 组件
│   │   ├── layouts/          # 布局组件
│   │   ├── stores/           # 状态管理
│   │   ├── views/            # 页面视图
│   │   └── router/           # 路由配置
│   └── package.json          # 前端依赖
├── docker-compose.yml        # Docker 部署配置
└── README.md                 # 项目说明
```

## 📖 API 文档

启动后端服务后，访问以下地址查看 API 文档：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 代码规范
- 后端：遵循 PEP 8 规范
- 前端：使用 ESLint 检查

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 📞 联系方式

如有问题或建议，请通过以下方式联系：
- 提交 Issue
- 发送邮件至 1109723336@qq.com

---

**注意**: 这是一个企业级知识库管理系统的开源版本，部分企业功能可能已移除或简化。

# Enterprise Knowledge Base Management System

[中文](./README.md) | English

An AI-powered enterprise-level knowledge base management system providing document management, knowledge graph, intelligent Q&A, and other features.

## 📋 Project Overview

This system aims to help enterprises efficiently manage and utilize internal knowledge resources, enabling intelligent Q&A, document understanding, and knowledge association through AI technology.

## ✨ Features

### Core Features
- **Document Management** - Support document upload, editing, version control, and permission management
- **Knowledge Graph** - Automatically build knowledge association networks between documents
- **Smart Search** - Semantic-based full-text search
- **AI Assistant** - Integrated with large language models for intelligent Q&A and document summarization
- **Team Collaboration** - Support team management and document collaboration
- **Approval Workflow** - Document publishing approval mechanism

### Technical Features
- Separation of front-end and back-end architecture
- RESTful API design
- OAuth2.0 single sign-on support
- Real-time notification push
- Complete permission control system

## 🛠️ Tech Stack

### Backend
| Technology | Version | Description |
|------------|---------|-------------|
| Python | 3.11+ | Programming language |
| FastAPI | 0.100+ | Web framework |
| SQLAlchemy | 2.0+ | ORM |
| PostgreSQL | 15+ | Database |
| Redis | 7+ | Cache |
| FAISS | 1.7+ | Vector search |

### Frontend
| Technology | Version | Description |
|------------|---------|-------------|
| Vue.js | 3+ | Frontend framework |
| Vite | 5+ | Build tool |
| Pinia | 2+ | State management |
| Tailwind CSS | 3+ | CSS framework |
| Vue Router | 4+ | Routing management |

## 🚀 Quick Start

### Requirements
- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Redis 7+

### Local Development

#### 1. Clone the Project
```bash
git clone https://github.com/zhangzhili000/kiro.git
cd kiro
```

#### 2. Start with Docker Compose (Recommended)

```bash
# Start all services
docker-compose up -d

# Check service status
docker-compose ps
```

**Service Access:**
- Frontend: http://localhost:5120
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

**Service Description:**
| Service | Port | Description |
| :--- | :--- | :--- |
| db | 5432 | PostgreSQL database |
| redis | 6379 | Redis cache |
| backend | 8000 | Backend service |
| frontend | 5120 | Frontend service |

#### 3. Manual Start (Development Mode)

**Start Backend:**
```bash
cd backend

# Install dependencies
pip install -r requirements.txt
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Start Frontend:**
```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

### Database Initialization

```sql
-- Create database
CREATE DATABASE kiro;

-- Create user
CREATE USER kiro WITH ENCRYPTED PASSWORD 'your_password';

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE kiro TO kiro;
```

Run database migration:
```bash
cd backend
python migrate_db.py
```

## ⚙️ Environment Variables

### Backend Environment Variables

| Variable | Description | Default |
| :--- | :--- | :--- |
| DATABASE_URL | Database connection URL | postgresql://kiro:kiro123@localhost:5432/kiro |
| REDIS_URL | Redis connection URL | redis://localhost:6379/0 |
| SECRET_KEY | JWT secret key | your-secret-key-change-in-production |
| APP_NAME | Application name | Kiro AI Platform |
| APP_VERSION | Application version | 1.1.0 |
| DEBUG | Debug mode | False |
| HOST | Service host | 0.0.0.0 |
| PORT | Service port | 8000 |
| CORS_ORIGINS | CORS allowed origins | ["*"] |
| VECTOR_DIMENSION | Vector dimension | 1536 |

### Frontend Environment Variables

| Variable | Description | Default |
| :--- | :--- | :--- |
| VITE_API_BASE_URL | Backend API URL | http://localhost:8000/api/v1 |

## 📁 Project Structure

```
.
├── backend/                    # Backend code
│   ├── kiro_knbase/           # Knowledge base module
│   │   ├── api/               # API routes
│   │   ├── models/            # Database models
│   │   ├── schemas/           # Data structure definitions
│   │   ├── services/          # Business logic layer
│   │   └── vector/            # Vector search
│   ├── kiro_platform/         # Platform core
│   │   ├── api/               # API routes
│   │   ├── models/            # Database models
│   │   ├── schemas/           # Data structure definitions
│   │   └── services/          # Business logic layer
│   ├── migrations/            # Database migration scripts
│   ├── main.py                # Application entry
│   ├── requirements.txt       # Dependencies
│   └── Dockerfile             # Docker build file
├── frontend/                  # Frontend code
│   ├── src/                   # Source code
│   │   ├── api/               # API calls
│   │   ├── components/        # Components
│   │   ├── layouts/           # Layout components
│   │   ├── stores/            # State management
│   │   ├── views/             # Page views
│   │   └── router/            # Router configuration
│   ├── package.json           # Frontend dependencies
│   └── Dockerfile             # Docker build file
├── docker-compose.yml         # Docker Compose configuration
├── README.md                  # Project documentation
├── README-en.md               # English documentation
└── LICENSE                    # License
```

## 🔧 Development Guide

### Code Standards
- Backend: Follow PEP 8 standards
- Frontend: Use ESLint for code checking

### API Documentation

After starting the backend service, access the following URLs to view API documentation:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Testing

**Backend Tests:**
```bash
cd backend
python -m pytest
```

**Frontend Tests:**
```bash
cd frontend
npm test
```

## 📦 Docker Deployment

### Docker Compose

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f

# Rebuild services
docker-compose up -d --build
```

### Production Configuration

1. **Change default passwords**: Modify database passwords in docker-compose.yml
2. **Configure HTTPS**: Use Nginx as reverse proxy
3. **Restrict CORS**: Modify CORS_ORIGINS in backend configuration

## 🌐 AI Model Configuration

### Configuration Process

1. Log in as admin
2. Navigate to "Model Management" page
3. Add model configurations (supports multiple API types):
   - Alibaba Tongyi
   - DeepSeek
   - OpenAI compatible
   - ZhiPu AI
   - SiliconFlow
   - Custom API
4. Set default model

## 📖 API Documentation

### Core APIs

| Module | API Prefix | Description |
| :--- | :--- | :--- |
| Authentication | `/api/v1/auth` | Login, register, validate |
| Documents | `/api/v1/documents` | Document CRUD, upload, process |
| AI Chat | `/api/v1/ai` | Intelligent Q&A, document summarization |
| Categories | `/api/v1/categories` | Document categories |
| Tags | `/api/v1/tags` | Document tags |
| Teams | `/api/v1/teams` | Team management |

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Contact

For questions or suggestions, please contact us via:
- Submit an Issue
- Send email to 1109723336@qq.com

---

**Note**: This is an open-source version of an enterprise-level knowledge base management system. Some enterprise features may have been removed or simplified.
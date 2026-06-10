# Enterprise Knowledge Base Management System

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
| Python | 3.13+ | Programming language |
| FastAPI | 0.100+ | Web framework |
| SQLAlchemy | 2.0+ | ORM |
| PostgreSQL | 15+ | Database |
| Redis | 7+ | Cache |

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
- Python 3.13+
- Node.js 20+
- PostgreSQL 15+
- Redis 7+

### Local Development

#### 1. Clone the Project
```bash
git clone https://github.com/zhangzhili000/kiro.git
cd kiro
```

#### 2. Start Backend Service
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn kiro.main:app --reload --host 0.0.0.0 --port 8000
```

#### 3. Start Frontend Service
```bash
cd frontend
npm install
npm run dev
```

#### 4. Access Application
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000

### Docker Deployment

```bash
docker-compose up -d
```

## 📁 Project Structure

```
.
├── backend/                    # Backend code
│   ├── kiro/                  # Application root
│   │   ├── api/              # API routes
│   │   │   └── v1/           # Versioned API
│   │   ├── core/             # Core configurations
│   │   ├── models/           # Database models
│   │   ├── schemas/          # Data structure definitions
│   │   ├── services/         # Business logic layer
│   │   └── utils/            # Utility functions
│   └── requirements.txt      # Dependencies
├── frontend/                  # Frontend code
│   ├── src/                  # Source code
│   │   ├── api/             # API calls
│   │   ├── components/       # Components
│   │   ├── layouts/          # Layout components
│   │   ├── stores/           # State management
│   │   ├── views/            # Page views
│   │   └── router/           # Router configuration
│   └── package.json          # Frontend dependencies
├── docker-compose.yml        # Docker deployment configuration
└── README.md                 # Project documentation
```

## 📖 API Documentation

After starting the backend service, access the following URLs to view API documentation:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Code Standards
- Backend: Follow PEP 8 standards
- Frontend: Use ESLint for code checking

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Contact

For questions or suggestions, please contact us via:
- Submit an Issue
- Send email to 1109723336@qq.com

---

**Note**: This is an open-source version of an enterprise-level knowledge base management system. Some enterprise features may have been removed or simplified.
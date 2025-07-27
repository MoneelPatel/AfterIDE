# AfterIDE - Web-Based Integrated Development Environment

A secure, web-based IDE featuring real-time code execution, terminal emulation, and collaborative review capabilities.

## 🚀 Quick Start

### Prerequisites
- Node.js 18+
- Python 3.11+
- Docker & Docker Compose
- PostgreSQL 15+

### Development Setup

1. **Clone and Setup**
```bash
git clone <repository-url>
cd AfterIDE
```

2. **Backend Setup**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

3. **Frontend Setup**
```bash
cd frontend
npm install
npm run dev
```

4. **Database Setup**
```bash
docker-compose up -d postgres redis
```

## 🏗️ Project Structure

```
AfterIDE/
├── backend/                 # FastAPI Python backend
│   ├── app/
│   │   ├── api/            # API routes and endpoints
│   │   ├── core/           # Core configuration and utilities
│   │   ├── models/         # Database models
│   │   ├── services/       # Business logic services
│   │   ├── websocket/      # WebSocket handlers
│   │   └── main.py         # FastAPI application entry point
│   ├── tests/              # Backend tests
│   ├── alembic/            # Database migrations
│   └── requirements.txt    # Python dependencies
├── frontend/               # React TypeScript frontend
│   ├── src/
│   │   ├── components/     # Reusable UI components
│   │   ├── pages/          # Page components
│   │   ├── hooks/          # Custom React hooks
│   │   ├── services/       # API and WebSocket services
│   │   ├── store/          # State management
│   │   ├── types/          # TypeScript type definitions
│   │   └── utils/          # Utility functions
│   ├── public/             # Static assets
│   └── package.json        # Node.js dependencies
├── docker-compose.yml      # Development environment
├── .env.example           # Environment variables template
└── README.md              # This file
```

## 🛠️ Technology Stack

### Frontend
- React 18 + TypeScript
- Vite (Build tool)
- Tailwind CSS (Styling)
- Monaco Editor (Code editor)
- xterm.js (Terminal emulation)
- WebSocket (Real-time communication)

### Backend
- FastAPI (Python web framework)
- PostgreSQL (Database)
- Redis (Caching & sessions)
- Docker (Containerization)
- WebSocket (Real-time communication)

## 🔒 Security Features

- Container-based code execution sandboxing
- Command validation and allowlisting
- Resource limiting and monitoring
- Input sanitization and validation
- Comprehensive audit logging

## 📊 Features

- ✅ Real-time code editor with Python support
- ✅ Integrated terminal with command execution
- ✅ File system synchronization
- ✅ Secure code execution environment
- ✅ Code submission and review system
- ✅ Performance monitoring and optimization

## 🚀 Deployment

See `DEPLOYMENT.md` for detailed deployment instructions.

## 📝 License

MIT License - see LICENSE file for details.


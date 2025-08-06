# AfterIDE - Web-Based Python IDE

AfterIDE is a modern, web-based Integrated Development Environment built with Python FastAPI backend and React TypeScript frontend. It provides a comprehensive development environment with real-time terminal, code editor, file management, and Python script execution capabilities.

## 🚀 Features

- **Real-time Terminal**: Interactive terminal with command execution
- **Code Editor**: Monaco Editor with Python syntax highlighting
- **File System**: Complete file management and workspace integration
- **Python Execution**: Run Python scripts directly in the browser
- **WebSocket Communication**: Real-time updates and collaboration
- **Authentication**: Secure user authentication and authorization
- **Database Integration**: SQLAlchemy with Alembic migrations
- **Comprehensive Testing**: Unit, integration, and end-to-end tests
- **Docker Support**: Containerized deployment
- **Railway Deployment**: Production-ready deployment configuration

## 🏗️ Project Structure

```
AfterIDE/
├── backend/                 # Python FastAPI backend
│   ├── app/                # Main application code
│   ├── alembic/            # Database migrations
│   ├── tests/              # Backend unit tests
│   ├── workspace/          # User workspace files
│   ├── requirements.txt    # Python dependencies
│   ├── main.py            # Entry point for Railway
│   └── Dockerfile         # Backend container
├── frontend/               # React TypeScript frontend
│   ├── src/               # Source code
│   ├── public/            # Static assets
│   ├── package.json       # Node.js dependencies
│   ├── vite.config.ts     # Vite configuration
│   └── Dockerfile.backup  # Frontend container
├── integration-tests/      # End-to-end and integration tests
│   ├── frontend/          # Frontend E2E tests (Playwright)
│   ├── backend/           # Backend integration tests
│   ├── docker/            # Test containers
│   └── run-all-tests.sh   # Test runner
├── scripts/               # Utility scripts
│   ├── run_tests.sh       # Test execution
│   ├── run_terminal_tests.py
│   └── test-api.sh
├── config/                # Configuration files
│   ├── pytest.ini        # Test configuration
│   └── test-requirements.txt
├── setup/                 # Setup and environment
│   └── env.example       # Environment template
├── railway.json          # Railway deployment config
├── nixpacks.toml         # Railway build config
├── requirements.txt      # Root Python dependencies
└── README.md            # This file
```

## 🛠️ Technology Stack

### Backend
- **Framework**: FastAPI with Uvicorn
- **Database**: SQLAlchemy with Alembic migrations
- **Authentication**: JWT with python-jose
- **WebSockets**: Native FastAPI WebSocket support
- **Container**: Docker with multi-stage builds
- **Testing**: pytest with comprehensive test suite

### Frontend
- **Framework**: React 18 with TypeScript
- **Build Tool**: Vite
- **Editor**: Monaco Editor + CodeMirror
- **Terminal**: xterm.js with WebGL rendering
- **Styling**: Tailwind CSS
- **State Management**: Zustand
- **Testing**: Vitest + Playwright for E2E
- **HTTP Client**: Axios with React Query

### DevOps
- **Deployment**: Railway with Nixpacks
- **Container Orchestration**: Docker Compose
- **CI/CD**: Automated testing and deployment
- **Monitoring**: Health checks and logging

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- Node.js 18+
- Docker (optional)
- Railway CLI (for deployment)

### Local Development

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd AfterIDE
   ```

2. **Setup environment**
   ```bash
   cp setup/env.example .env
   # Edit .env with your configuration
   ```

3. **Install backend dependencies**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

4. **Install frontend dependencies**
   ```bash
   cd frontend
   npm install
   ```

5. **Run the application**
   ```bash
   # Terminal 1 - Backend (from backend directory)
   python main.py
   
   # Terminal 2 - Frontend (from frontend directory)
   npm run dev
   ```

6. **Access the application**
   - Frontend: http://localhost:3008 (or next available port)
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

## 🧪 Testing

### Run all tests
```bash
cd scripts
./run_tests.sh
```

### Frontend tests
```bash
cd frontend
npm test              # Unit tests with Vitest
npm run test:ui       # Test UI
npx playwright test   # E2E tests
```

### Backend tests
```bash
cd backend
pytest               # Unit tests
pytest --cov=app     # With coverage
```

### Integration tests
```bash
cd integration-tests
./run-all-tests.sh
```

## 🚀 Deployment

### Railway Deployment
The project is configured for Railway deployment with automatic builds and deployments.

1. **Connect to Railway**
   ```bash
   railway login
   railway link
   ```

2. **Deploy**
   ```bash
   railway up
   ```

### Docker Deployment
```bash
# Build and run with Docker Compose
docker-compose up --build
```

## 📚 Documentation

- **API Documentation**: Available at `/docs` when running the backend
- **Integration Test Guide**: `integration-tests/INTEGRATION_TEST_GUIDE.md`
- **Security Documentation**: `backend/SECURITY.md`
- **Authentication Troubleshooting**: `frontend/AUTH_TROUBLESHOOTING.md`

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Check the documentation in the respective directories
- Review the troubleshooting guides
- Open an issue on GitHub

---

**Happy coding with AfterIDE! 🐍✨**


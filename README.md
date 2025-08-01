# AfterIDE Project

Welcome to your AfterIDE workspace! This is an online Python IDE with a terminal, text editor, and file directory.

## Project Structure

```
AfterIDE/
├── backend/          # Python FastAPI backend
├── frontend/         # React TypeScript frontend
├── workspace/        # User workspace files
├── config/           # Configuration files (pytest.ini, test-requirements.txt)
├── docs/             # Documentation (TESTS.md, CLEANUP_SUMMARY.md)
├── scripts/          # Utility scripts (run_tests.sh, run_terminal_tests.py)
├── deploy/           # Deployment files (docker-compose.yml)
├── setup/            # Setup files (env.example)
├── main.py           # Main entry point
├── requirements.txt  # Main Python dependencies
└── README.md         # This file
```

## Getting Started

1. **Setup Environment**: Copy `setup/env.example` to `.env` and configure
2. **Install Dependencies**: 
   - Backend: `cd backend && pip install -r requirements.txt`
   - Frontend: `cd frontend && npm install`
3. **Run the Application**:
   - Backend: `cd backend && python main.py`
   - Frontend: `cd frontend && npm run dev`

## Testing

Run the comprehensive test suite:
```bash
cd scripts
./run_tests.sh
```

For detailed testing information, see `docs/TESTS.md`.

## Features

- Real-time terminal with command execution
- File system integration
- Python script execution
- WebSocket-based communication
- Comprehensive test suite
- Docker deployment support

## Development

- **Backend**: FastAPI with SQLAlchemy
- **Frontend**: React with TypeScript
- **Testing**: pytest (backend) + vitest (frontend)
- **Deployment**: Docker Compose

Happy coding!


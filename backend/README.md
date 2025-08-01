# AfterIDE Backend

## 🚀 Quick Setup

Use our automated setup script that handles everything including pip upgrades:

```bash
cd backend
./setup.sh
```

## ✨ Features

- **Automatic Pip Upgrade**: No more annoying "pip version X is available" warnings!
- **Database Management**: Automatic migrations and setup
- **Virtual Environment**: Isolated Python environment
- **Development Ready**: All dependencies pre-configured

## 📋 Manual Setup (if needed)

If you prefer manual setup:

```bash
# 1. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 2. Upgrade pip (eliminates warnings)
python -m pip install --upgrade pip

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run migrations
alembic upgrade head

# 5. Start server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## 🔧 Development

### Starting the Server
```bash
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Running Tests
```bash
source venv/bin/activate
pytest
```

### Database Migrations
```bash
# Create migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head
```

## 🐛 Troubleshooting

### Pip Version Warnings
This project automatically upgrades pip to the latest version to eliminate warning messages. If you still see warnings:

```bash
python -m pip install --upgrade pip
```

### Virtual Environment Issues
If the virtual environment is corrupted:

```bash
rm -rf venv
./setup.sh
```

## 📁 Project Structure

```
backend/
├── app/                 # Main application code
├── alembic/            # Database migrations
├── venv/               # Virtual environment
├── requirements.txt    # Python dependencies
├── setup.sh           # Automated setup script
└── README.md          # This file
```

## 🌐 API Endpoints

- **Health Check**: `GET /health`
- **Authentication**: `POST /api/v1/auth/login`
- **Sessions**: `GET /api/v1/sessions/`
- **WebSockets**: `ws://localhost:8000/ws/`

## 💡 Tips

- Always use the setup script for new installations
- Pip is automatically kept up-to-date
- Virtual environment is automatically managed
- Database migrations run automatically during setup 
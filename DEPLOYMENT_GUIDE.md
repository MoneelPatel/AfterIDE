# AfterIDE Deployment Guide

This guide will help you deploy AfterIDE to Railway, starting with the backend and then adding the frontend.

## Current Setup

Your project is configured with 3 services:
1. **Backend** - FastAPI backend service (main deployment)
2. **postgres** - PostgreSQL database
3. **redis** - Redis cache

## Deployment Steps

### 1. Backend Deployment (Current Focus)

Your `railway.toml` is configured for backend deployment:

```toml
[build]
builder = "nixpacks"

[deploy]
startCommand = "cd backend && python main.py"
restartPolicyType = "on_failure"
restartPolicyMaxRetries = 10

[deploy.variables]
ENVIRONMENT = "production"
DEBUG = "false"
LOG_LEVEL = "INFO"
```

### 2. Environment Variables

Set these environment variables in Railway dashboard:

#### Required Variables:
- `SECRET_KEY=your-super-secret-key-here`
- `POSTGRES_PASSWORD=your-secure-password`

#### Optional Variables:
- `ENVIRONMENT=production`
- `DEBUG=false`
- `LOG_LEVEL=INFO`

### 3. Deployment Process

1. **Commit and Push**: Use the deployment script or manually:
   ```bash
   git add .
   git commit -m "Fix deployment configuration"
   git push origin main
   ```

2. **Deploy to Railway**: Railway will automatically deploy using nixpacks

3. **Set Environment Variables**: Configure in Railway dashboard

4. **Test Backend**: Verify the backend is working

### 4. Testing the Backend

After deployment, test these endpoints:
- **Root**: `https://your-app-name.up.railway.app/`
- **Health**: `https://your-app-name.up.railway.app/health`
- **API Docs**: `https://your-app-name.up.railway.app/docs`
- **API Status**: `https://your-app-name.up.railway.app/api/v1/status`

### 5. Frontend Deployment (Next Step)

Once the backend is working, we'll deploy the frontend as a separate service:

1. **Create Frontend Service**: Add to Railway dashboard
2. **Configure Build**: Use Node.js buildpack
3. **Set Environment**: Configure API URL to point to backend
4. **Deploy**: Build and deploy frontend

### 6. Troubleshooting

#### Build Failures:
- Check Railway logs for specific errors
- Verify all dependencies are in requirements-railway.txt
- Ensure Python version compatibility

#### Database Connection:
- Check PostgreSQL service is running
- Verify database credentials
- Check connection string format

#### API Issues:
- Verify backend is running
- Check CORS settings
- Test individual endpoints

## Current Status

✅ **Backend Configuration**: Fixed and ready for deployment
✅ **Nixpacks Configuration**: Updated with correct start command
✅ **Requirements**: All dependencies included
✅ **Database Services**: PostgreSQL and Redis configured

## Quick Deploy

Run the deployment script from the project root:
```bash
./deploy_backend.sh
```

## Next Steps

1. **Deploy Backend**: Push code and deploy to Railway
2. **Test Backend**: Verify all endpoints are working
3. **Deploy Frontend**: Add frontend as separate service
4. **Connect Services**: Configure frontend to use backend API

## Expected URLs

After successful deployment:
- **Backend**: `https://your-app-name.up.railway.app`
- **API Documentation**: `https://your-app-name.up.railway.app/docs`
- **Health Check**: `https://your-app-name.up.railway.app/health` 
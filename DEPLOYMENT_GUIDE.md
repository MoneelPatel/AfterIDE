# AfterIDE Deployment Guide

This guide will help you deploy both the frontend and backend services to Railway.

## Current Setup

Your project is configured with 4 services:
1. **afteride-backend** - FastAPI backend service
2. **afteride-frontend** - React frontend application
3. **postgres** - PostgreSQL database
4. **redis** - Redis cache

## Deployment Steps

### 1. Railway Configuration

Your `railway.toml` is already configured with all services. The key configuration:

```toml
[[services]]
name = "afteride-backend"
source = "backend"
buildCommand = "pip install -r requirements-railway.txt"
startCommand = "python main.py"

[[services]]
name = "afteride-frontend"
source = "frontend"
buildCommand = "npm ci && npm run build"
startCommand = "npx serve -s dist -l $PORT"
variables = [
  "NODE_ENV=production",
  "VITE_API_URL=${RAILWAY_STATIC_URL_AFTERIDE_BACKEND}/api/v1"
]
```

### 2. Environment Variables

You need to set these environment variables in Railway:

#### Backend Service Variables:
- `ENVIRONMENT=production`
- `DEBUG=false`
- `LOG_LEVEL=INFO`
- `SECRET_KEY=your-super-secret-key-here`
- `POSTGRES_PASSWORD=your-secure-password`

#### Frontend Service Variables:
- `NODE_ENV=production`
- `VITE_API_URL=${RAILWAY_STATIC_URL_AFTERIDE_BACKEND}/api/v1`

#### Database Service Variables:
- `POSTGRES_DB=afteride`
- `POSTGRES_USER=postgres`
- `POSTGRES_PASSWORD=${POSTGRES_PASSWORD}`

### 3. Deployment Process

1. **Push to GitHub**: Ensure all changes are committed and pushed
2. **Connect to Railway**: Link your GitHub repository to Railway
3. **Deploy Services**: Railway will automatically deploy all 4 services
4. **Set Environment Variables**: Configure the variables listed above
5. **Verify Deployment**: Check that all services are running

### 4. Service URLs

After deployment, you'll have:
- **Frontend**: `https://your-project-name.up.railway.app` (or custom domain)
- **Backend**: `https://afteride-backend-production.up.railway.app`
- **Database**: Internal service (not publicly accessible)
- **Redis**: Internal service (not publicly accessible)

### 5. Testing the Deployment

1. **Frontend**: Visit the frontend URL to see the React application
2. **Backend**: Visit `/health` endpoint to check backend status
3. **API**: Test API endpoints at `/api/v1/status`

### 6. Troubleshooting

#### Frontend not connecting to backend:
- Check `VITE_API_URL` environment variable
- Ensure backend service is running
- Verify CORS settings in backend

#### Database connection issues:
- Check PostgreSQL service is running
- Verify database credentials
- Check connection string format

#### Build failures:
- Check build logs in Railway dashboard
- Verify all dependencies are in requirements.txt/package.json
- Ensure Node.js and Python versions are compatible

## Current Status

✅ **Backend**: Configured and ready for deployment
✅ **Frontend**: Configured and ready for deployment  
✅ **Database**: PostgreSQL service configured
✅ **Redis**: Redis service configured
✅ **Environment Variables**: Configured in railway.toml

## Next Steps

1. **Deploy to Railway**: Push your code and deploy
2. **Set Environment Variables**: Configure in Railway dashboard
3. **Test Both Services**: Verify frontend and backend are working
4. **Set Custom Domain**: Configure your preferred domain name

## Access URLs

After deployment, you should be able to access:
- **Frontend Application**: `https://your-project-name.up.railway.app`
- **Backend API**: `https://afteride-backend-production.up.railway.app`
- **API Documentation**: `https://afteride-backend-production.up.railway.app/docs`
- **Health Check**: `https://afteride-backend-production.up.railway.app/health` 
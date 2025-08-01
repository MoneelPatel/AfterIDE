# AfterIDE Railway Deployment Guide

This guide will walk you through deploying your AfterIDE project to Railway.

## Prerequisites

1. **Railway Account**: Sign up at [railway.app](https://railway.app)
2. **GitHub Repository**: Your code should be in a GitHub repository
3. **Railway CLI** (optional): Install with `npm i -g @railway/cli`

## Step 1: Prepare Your Repository

Your repository is already configured with the necessary Railway files:
- `railway.json` - Railway configuration
- `railway.toml` - Multi-service configuration
- `.railwayignore` - Files to exclude from deployment
- `backend/Dockerfile` - Backend container configuration
- `frontend/Dockerfile` - Frontend container configuration
- `frontend/nginx.conf` - Nginx configuration for frontend

## Step 2: Deploy to Railway

### Option A: Deploy via Railway Dashboard (Recommended)

1. **Go to Railway Dashboard**
   - Visit [railway.app](https://railway.app)
   - Sign in with your GitHub account

2. **Create New Project**
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your AfterIDE repository

3. **Configure Services**
   Railway will automatically detect the services from your `railway.toml`:
   - `afteride-backend` - FastAPI backend
   - `afteride-frontend` - React frontend
   - `postgres` - PostgreSQL database
   - `redis` - Redis cache

4. **Set Environment Variables**
   In your Railway project dashboard, go to Variables tab and add:
   ```
   ENVIRONMENT=production
   DEBUG=false
   LOG_LEVEL=INFO
   SECRET_KEY=your-super-secret-key-here
   POSTGRES_PASSWORD=your-secure-password
   ```

5. **Deploy**
   - Railway will automatically build and deploy your services
   - Monitor the deployment logs in the dashboard

### Option B: Deploy via Railway CLI

1. **Install Railway CLI**
   ```bash
   npm i -g @railway/cli
   ```

2. **Login to Railway**
   ```bash
   railway login
   ```

3. **Initialize Project**
   ```bash
   cd AfterIDE
   railway init
   ```

4. **Deploy**
   ```bash
   railway up
   ```

## Step 3: Configure Services

### Backend Service
- **Source**: `backend/` directory
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- **Health Check**: `/health` endpoint

### Frontend Service
- **Source**: `frontend/` directory
- **Build Command**: `npm ci && npm run build`
- **Start Command**: `npx serve -s dist -l $PORT`

### Database Service
- **Image**: `postgres:15-alpine`
- **Environment Variables**:
  - `POSTGRES_DB=afteride`
  - `POSTGRES_USER=postgres`
  - `POSTGRES_PASSWORD=${POSTGRES_PASSWORD}`

### Redis Service
- **Image**: `redis:7-alpine`

## Step 4: Environment Variables

Set these environment variables in your Railway project:

### Required Variables
```
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
SECRET_KEY=your-super-secret-key-here
POSTGRES_PASSWORD=your-secure-password
```

### Optional Variables
```
ACCESS_TOKEN_EXPIRE_MINUTES=10080
SESSION_TIMEOUT=3600
MAX_EXECUTION_TIME=30
MAX_MEMORY_MB=512
```

## Step 5: Database Migration

After deployment, you may need to run database migrations:

1. **Access Backend Service**
   - Go to your backend service in Railway dashboard
   - Open the terminal

2. **Run Migrations**
   ```bash
   cd backend
   alembic upgrade head
   ```

3. **Create Admin User** (if needed)
   ```bash
   python create_admin_user.py
   ```

## Step 6: Verify Deployment

1. **Check Health Endpoint**
   - Visit: `https://your-backend-url.railway.app/health`
   - Should return: `{"status": "healthy", "version": "1.0.0", ...}`

2. **Check Frontend**
   - Visit your frontend URL
   - Should load the AfterIDE interface

3. **Check API Documentation**
   - Visit: `https://your-backend-url.railway.app/docs`
   - Should show FastAPI documentation

## Step 7: Custom Domain (Optional)

1. **Add Custom Domain**
   - Go to your Railway project settings
   - Add your custom domain
   - Update DNS records as instructed

2. **Update CORS Settings**
   - Update `CORS_ORIGINS` in your environment variables
   - Add your custom domain to the list

## Troubleshooting

### Common Issues

1. **Build Failures**
   - Check build logs in Railway dashboard
   - Ensure all dependencies are in `requirements.txt`
   - Verify Dockerfile syntax

2. **Database Connection Issues**
   - Verify `DATABASE_URL` environment variable
   - Check PostgreSQL service is running
   - Ensure database migrations are applied

3. **Frontend Not Loading**
   - Check frontend build logs
   - Verify nginx configuration
   - Check if backend API is accessible

4. **WebSocket Issues**
   - Verify WebSocket proxy configuration in nginx
   - Check if backend WebSocket endpoint is working

### Logs and Monitoring

- **View Logs**: Use Railway dashboard to view service logs
- **Monitor Resources**: Check CPU, memory, and disk usage
- **Set Up Alerts**: Configure alerts for service failures

## Cost Optimization

Railway's free tier includes:
- $5/month credit
- Shared infrastructure
- Automatic scaling

To optimize costs:
1. **Use shared infrastructure** when possible
2. **Monitor resource usage** regularly
3. **Scale down** during low usage periods
4. **Use environment variables** for configuration

## Security Considerations

1. **Environment Variables**
   - Never commit secrets to your repository
   - Use Railway's environment variable system
   - Rotate secrets regularly

2. **CORS Configuration**
   - Restrict CORS origins in production
   - Only allow necessary domains

3. **Database Security**
   - Use strong passwords
   - Enable SSL connections
   - Regular backups

## Next Steps

After successful deployment:

1. **Set up monitoring** and alerting
2. **Configure backups** for your database
3. **Set up CI/CD** for automatic deployments
4. **Add custom domain** and SSL certificate
5. **Implement logging** and error tracking

## Support

- **Railway Documentation**: [docs.railway.app](https://docs.railway.app)
- **Railway Discord**: [discord.gg/railway](https://discord.gg/railway)
- **AfterIDE Issues**: Create issues in your GitHub repository

---

**Happy Deploying! 🚀** 
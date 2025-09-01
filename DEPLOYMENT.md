# Musharaka Pro - Deployment Guide

## Deploy to Render

### Prerequisites
- GitHub repository with your code
- Render account (free tier available)

### Step-by-Step Deployment

#### 1. Prepare Your Repository
Make sure your repository contains all the required files:
- `app.py` - Main application
- `routes.py` - API routes
- `requirements.txt` - Python dependencies
- `Procfile` - Process definition
- `runtime.txt` - Python version
- `render.yaml` - Render configuration (optional)

#### 2. Connect to Render

1. **Go to [render.com](https://render.com) and sign up/login**
2. **Click "New +" → "Web Service"**
3. **Connect your GitHub repository**
4. **Select your repository**

#### 3. Configure the Service

**Basic Settings:**
- **Name:** `musharaka-pro` (or your preferred name)
- **Environment:** `Python 3`
- **Region:** Choose closest to your users
- **Branch:** `main` (or your default branch)

**Build & Deploy:**
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `gunicorn app:app`

**Environment Variables:**
- `FLASK_ENV=production`
- `DATABASE_URL` (will be set automatically when you add PostgreSQL)

#### 4. Add PostgreSQL Database

1. **Go to your service dashboard**
2. **Click "Add Database"**
3. **Select "PostgreSQL"**
4. **Choose "Free" plan**
5. **Name it:** `musharaka-db`
6. **Click "Add Database"**

#### 5. Deploy

1. **Click "Create Web Service"**
2. **Wait for the build to complete** (usually 2-5 minutes)
3. **Your app will be available at:** `https://your-app-name.onrender.com`

### Using render.yaml (Automatic Configuration)

If you have the `render.yaml` file in your repository:

1. **Push your code to GitHub**
2. **In Render, click "New +" → "Blueprint"**
3. **Connect your repository**
4. **Render will automatically create both the web service and database**

### Environment Variables

| Variable | Value | Description |
|----------|-------|-------------|
| `FLASK_ENV` | `production` | Sets Flask to production mode |
| `DATABASE_URL` | Auto-generated | PostgreSQL connection string |
| `PORT` | Auto-set | Port number (usually 10000) |

### Troubleshooting

#### Build Fails
- Check that all dependencies are in `requirements.txt`
- Ensure Python version in `runtime.txt` is supported
- Check build logs for specific errors

#### App Won't Start
- Verify `Procfile` or start command is correct
- Check that `gunicorn` is in requirements.txt
- Ensure all imports work correctly

#### Database Connection Issues
- Verify `DATABASE_URL` is set correctly
- Check that `psycopg2-binary` is in requirements.txt
- Ensure database is created and running

#### 502 Bad Gateway
- Check application logs
- Verify the app is binding to `0.0.0.0:$PORT`
- Ensure the app responds to health checks

### Monitoring

- **Logs:** Available in the Render dashboard
- **Metrics:** CPU, memory, and response time monitoring
- **Health Checks:** Automatic health monitoring at `/`

### Scaling

- **Free Tier:** 750 hours/month, sleeps after 15 minutes of inactivity
- **Starter Plan:** $7/month, always-on, 0.5GB RAM
- **Standard Plan:** $25/month, 1GB RAM, better performance

### Custom Domain

1. **Go to your service settings**
2. **Click "Custom Domains"**
3. **Add your domain**
4. **Follow DNS configuration instructions**

### SSL Certificate

Render automatically provides SSL certificates for all services.

## Alternative Deployment Options

### Heroku
```bash
# Install Heroku CLI
# Login and create app
heroku create your-app-name
heroku addons:create heroku-postgresql:hobby-dev
git push heroku main
```

### Railway
1. Connect GitHub repository
2. Select Python environment
3. Add PostgreSQL database
4. Deploy automatically

### DigitalOcean App Platform
1. Create new app from GitHub
2. Select Python environment
3. Add database component
4. Configure environment variables

## Local Development with Docker

```bash
# Build and run with Docker Compose
docker-compose up --build

# Access the app at http://localhost:5000
# Access PostgreSQL at localhost:5432
```

## Production Checklist

- [ ] Environment variables configured
- [ ] Database created and connected
- [ ] SSL certificate active
- [ ] Health checks passing
- [ ] Monitoring set up
- [ ] Backup strategy in place
- [ ] Error tracking configured (optional)
- [ ] Performance monitoring (optional)
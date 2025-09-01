# Musharaka Pro - Quick Start Guide

## 🚀 Deploy to Render in 5 Minutes

### Step 1: Push to GitHub
```bash
# Initialize git (if not already done)
git init
git add .
git commit -m "Initial commit"

# Add your GitHub repository
git remote add origin https://github.com/yourusername/musharaka-pro.git
git push -u origin main
```

### Step 2: Deploy on Render
1. **Go to [render.com](https://render.com)**
2. **Sign up/Login with GitHub**
3. **Click "New +" → "Web Service"**
4. **Connect your repository**
5. **Configure:**
   - **Name:** `musharaka-pro`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
6. **Add PostgreSQL Database:**
   - Click "Add Database"
   - Select "PostgreSQL"
   - Choose "Free" plan
7. **Deploy!**

### Step 3: Test Your Deployment
```bash
# Replace with your actual Render URL
export BASE_URL="https://your-app-name.onrender.com"
python3 test_deployment.py
```

## 🏠 Local Development

### Quick Setup
```bash
# Install dependencies
make install

# Run the application
make run

# Test locally
make test
```

### With Docker
```bash
# Build and run
docker-compose up --build

# Access at http://localhost:5000
```

## 📱 API Usage Examples

### Create a Project
```bash
curl -X POST https://your-app.onrender.com/api/projects \
  -H "Content-Type: application/json" \
  -d '{
    "code": "PROJ001",
    "name": "My Project",
    "base_currency": "EGP"
  }'
```

### Add Partners
```bash
# Create partner
curl -X POST https://your-app.onrender.com/api/partners \
  -H "Content-Type: application/json" \
  -d '{"name": "Partner A"}'

# Add to project (replace IDs with actual values)
curl -X POST https://your-app.onrender.com/api/projects/PROJECT_ID/partners \
  -H "Content-Type: application/json" \
  -d '{
    "partner_id": "PARTNER_ID",
    "share_pct": 60
  }'
```

### Deposit to Wallet
```bash
curl -X POST https://your-app.onrender.com/api/projects/PROJECT_ID/partners/PARTNER_ID/wallet/deposit \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 100000,
    "notes": "Initial deposit"
  }'
```

## 🔧 Troubleshooting

### Common Issues

**Build Fails:**
- Check `requirements.txt` has all dependencies
- Ensure Python version in `runtime.txt` is correct

**App Won't Start:**
- Verify `Procfile` is correct
- Check environment variables are set

**Database Issues:**
- Ensure PostgreSQL addon is added
- Check `DATABASE_URL` is set correctly

### Getting Help
- Check the logs in Render dashboard
- Run `make health` to test locally
- Review `DEPLOYMENT.md` for detailed instructions

## 📊 Monitoring

- **Health Check:** `https://your-app.onrender.com/`
- **Logs:** Available in Render dashboard
- **Metrics:** CPU, memory, response time

## 🔄 Updates

To update your deployment:
```bash
# Make changes to your code
git add .
git commit -m "Update application"
git push origin main

# Render will automatically redeploy
```

## 💡 Tips

1. **Free Tier Limits:** 750 hours/month, sleeps after 15 minutes
2. **Always-On:** Upgrade to Starter plan ($7/month) for always-on service
3. **Custom Domain:** Add your own domain in Render settings
4. **Environment Variables:** Set in Render dashboard under "Environment"

## 🎯 Next Steps

1. **Test all endpoints** using the test script
2. **Set up monitoring** and alerts
3. **Configure custom domain** (optional)
4. **Set up CI/CD** for automatic deployments
5. **Add authentication** if needed (not included in this version)
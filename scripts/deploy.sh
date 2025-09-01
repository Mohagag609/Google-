#!/bin/bash
# Deployment script for Musharaka Pro

set -e  # Exit on any error

echo "🚀 Starting Musharaka Pro deployment..."

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    echo "❌ Not in a git repository. Please initialize git first."
    exit 1
fi

# Check if we have uncommitted changes
if [ -n "$(git status --porcelain)" ]; then
    echo "📝 You have uncommitted changes. Committing them now..."
    git add .
    git commit -m "Deploy to Render - $(date)"
fi

# Push to remote
echo "📤 Pushing to remote repository..."
git push origin main

echo "✅ Deployment initiated!"
echo "🔗 Check your Render dashboard for deployment progress."
echo "📊 Once deployed, run: make test BASE_URL=https://your-app.onrender.com"
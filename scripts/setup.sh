#!/bin/bash
# Setup script for Musharaka Pro

set -e  # Exit on any error

echo "🔧 Setting up Musharaka Pro..."

# Check Python version
echo "🐍 Checking Python version..."
python3 --version

# Install dependencies
echo "📦 Installing dependencies..."
pip3 install -r requirements.txt --break-system-packages

# Initialize database
echo "🗄️  Initializing database..."
python3 -c "from app import app, db; app.app_context().push(); db.create_all(); print('Database initialized successfully')"

# Run health check
echo "🏥 Running health check..."
python3 healthcheck.py

echo "✅ Setup completed successfully!"
echo "🚀 Run 'make run' to start the application locally"
echo "🌐 Or run 'make deploy' to deploy to Render"
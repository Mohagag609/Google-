#!/bin/bash
# Quick start script for Musharaka Pro

echo "🚀 Starting Musharaka Pro - نظام إدارة المقاولات الاحترافي"
echo "================================================"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed"
    exit 1
fi

echo "✅ Python 3 found"

# Install dependencies
echo "📦 Installing dependencies..."
pip3 install --break-system-packages -r requirements.txt -q

# Initialize database
echo "🗄️ Initializing database..."
python3 -c "from app.app import app, db; app.app_context().push(); db.create_all(); print('✅ Database ready')"

# Start the application
echo "🌟 Starting application..."
echo "================================================"
echo "📍 Access the application at: http://localhost:5000"
echo "📍 Dashboard: http://localhost:5000/dashboard"
echo "📍 Backup: http://localhost:5000/backup"
echo "📍 Settings: http://localhost:5000/settings"
echo "================================================"
echo "Press Ctrl+C to stop the server"
echo ""

# Run the application
python3 run.py
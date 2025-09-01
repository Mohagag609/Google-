#!/bin/bash
# Start script for Musharaka Pro on Render

# Install dependencies
pip install -r requirements.txt

# Initialize database
python3 -c "from app import app, db; app.app_context().push(); db.create_all()"

# Start the application
gunicorn app:app --bind 0.0.0.0:$PORT
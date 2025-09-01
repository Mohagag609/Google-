#!/usr/bin/env python3
"""
Start script for Musharaka Pro
"""

import os
from app import app, db

# Initialize database tables
with app.app_context():
    db.create_all()

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

# Production command for Render (RECOMMENDED):
# gunicorn --bind 0.0.0.0:$PORT --workers 1 --timeout 120 --keep-alive 2 --max-requests 1000 --max-requests-jitter 100 app:app
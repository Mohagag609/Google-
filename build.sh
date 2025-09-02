#!/usr/bin/env bash
# Build script for Render deployment

set -o errexit

# Install dependencies
pip install -r requirements.txt

# Run database migrations (create tables)
python3 -c "from app import app; from app.db import db; app.app_context().push(); db.create_all()"

echo "Build completed successfully!"
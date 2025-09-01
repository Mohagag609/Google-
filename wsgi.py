"""
WSGI entry point for Musharaka Pro
"""

from app import app, db

# Initialize database tables
with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run()
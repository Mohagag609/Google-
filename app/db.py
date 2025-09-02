"""Database initialization and configuration"""
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

class TimestampMixin:
    """Mixin for timestamp fields"""
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

def init_db(app):
    """Initialize database with app"""
    # Configure database URL
    database_url = os.getenv('DATABASE_URL', 'sqlite:///musharaka.db')
    
    # Handle Render's postgres URL format
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    
    # Use SQLite locally if PostgreSQL is not available
    if 'postgresql' in database_url:
        try:
            import psycopg2
        except ImportError:
            print("PostgreSQL driver not found, using SQLite instead")
            database_url = 'sqlite:///musharaka.db'
    
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    
    with app.app_context():
        db.create_all()
        
    return db
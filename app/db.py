#!/usr/bin/env python3
"""
Database configuration for Musharaka Pro
"""

import os
from flask_sqlalchemy import SQLAlchemy
from flask import Flask

db = SQLAlchemy()

def init_db(app: Flask):
    """Initialize database with Flask app."""
    # Database configuration
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///musharaka.db')
    
    # Force SQLite to avoid PostgreSQL issues
    if 'postgres' in DATABASE_URL.lower():
        DATABASE_URL = 'sqlite:///musharaka.db'
    
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    
    # Create tables
    with app.app_context():
        db.create_all()
    
    return db
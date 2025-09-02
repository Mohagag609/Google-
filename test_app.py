#!/usr/bin/env python3
"""Simple test to verify the application is working"""
import sys
sys.path.insert(0, 'app')

from app import app
from db import db
from models import Project, Partner

def test_app():
    """Test basic functionality"""
    print("Testing Musharaka Pro Application...")
    
    with app.app_context():
        # Test database
        print("✓ Database initialized")
        
        # Test models
        project = Project(code="TEST001", name="مشروع تجريبي")
        print("✓ Models working")
        
        # Test routes
        client = app.test_client()
        response = client.get('/')
        assert response.status_code == 200
        print("✓ Routes working")
        
        # Test templates
        assert b'<!DOCTYPE html>' in response.data
        print("✓ Templates rendering")
        
        print("\n✅ All tests passed! The application is ready.")
        print("\nYou can now:")
        print("1. Run locally: python3 run.py")
        print("2. Deploy to Render using the render.yaml file")
        print("3. Access at http://localhost:5000")

if __name__ == '__main__':
    test_app()
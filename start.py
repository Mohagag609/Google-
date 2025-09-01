#!/usr/bin/env python3
"""
Start script for Musharaka Pro
"""

import sys
import os

# Add app directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app import app

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 Starting Musharaka Pro on http://localhost:{port}")
    print("📱 Open your browser and navigate to the URL above")
    print("🛑 Press Ctrl+C to stop the server")
    app.run(host='0.0.0.0', port=port, debug=True)
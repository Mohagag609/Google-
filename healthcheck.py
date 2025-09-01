#!/usr/bin/env python3
"""
Health check script for Musharaka Pro
"""

import requests
import sys
import os

def health_check():
    """Check if the application is healthy"""
    try:
        # Get the base URL from environment or use localhost
        base_url = os.getenv('BASE_URL', 'http://localhost:5000')
        
        # Test the root endpoint
        response = requests.get(f"{base_url}/", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('ok') and data.get('data', {}).get('name') == 'Musharaka Pro (no auth)':
                print("✅ Health check passed")
                return 0
            else:
                print("❌ Health check failed: Invalid response format")
                return 1
        else:
            print(f"❌ Health check failed: HTTP {response.status_code}")
            return 1
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Health check failed: {e}")
        return 1
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(health_check())
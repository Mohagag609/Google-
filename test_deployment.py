#!/usr/bin/env python3
"""
Test script for Musharaka Pro deployment
"""

import requests
import json
import sys
import os
from datetime import datetime

def test_endpoint(base_url, endpoint, method='GET', data=None, expected_status=200):
    """Test a single endpoint"""
    try:
        url = f"{base_url}{endpoint}"
        
        if method == 'GET':
            response = requests.get(url, timeout=10)
        elif method == 'POST':
            response = requests.post(url, json=data, timeout=10)
        else:
            print(f"❌ Unsupported method: {method}")
            return False
        
        if response.status_code == expected_status:
            print(f"✅ {method} {endpoint} - Status: {response.status_code}")
            return True
        else:
            print(f"❌ {method} {endpoint} - Expected: {expected_status}, Got: {response.status_code}")
            if response.text:
                print(f"   Response: {response.text[:200]}...")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ {method} {endpoint} - Error: {e}")
        return False

def run_tests():
    """Run deployment tests"""
    base_url = os.getenv('BASE_URL', 'http://localhost:5000')
    
    print(f"🧪 Testing Musharaka Pro at: {base_url}")
    print(f"⏰ Test started at: {datetime.now()}")
    print("-" * 50)
    
    tests = [
        # Basic endpoints
        ('/', 'GET', None, 200),
        ('/api/projects', 'GET', None, 200),
        
        # Create project
        ('/api/projects', 'POST', {
            'code': 'TEST001',
            'name': 'Test Project',
            'base_currency': 'EGP'
        }, 201),
        
        # Create partner
        ('/api/partners', 'POST', {
            'name': 'Test Partner'
        }, 201),
        
        # Create supplier
        ('/api/suppliers', 'POST', {
            'name': 'Test Supplier'
        }, 201),
        
        # Create item
        ('/api/items', 'POST', {
            'sku': 'TEST-ITEM-001',
            'name': 'Test Item',
            'uom': 'unit',
            'std_cost': 100.00
        }, 201),
    ]
    
    passed = 0
    total = len(tests)
    
    for endpoint, method, data, expected_status in tests:
        if test_endpoint(base_url, endpoint, method, data, expected_status):
            passed += 1
    
    print("-" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Deployment is successful.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the deployment.")
        return 1

if __name__ == "__main__":
    sys.exit(run_tests())
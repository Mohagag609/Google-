#!/bin/bash
# Test script for Musharaka Pro

set -e  # Exit on any error

BASE_URL=${1:-"http://localhost:5000"}

echo "🧪 Testing Musharaka Pro at: $BASE_URL"

# Wait for the application to start
echo "⏳ Waiting for application to start..."
sleep 5

# Run health check
echo "🏥 Running health check..."
python3 healthcheck.py

# Run deployment tests
echo "🧪 Running deployment tests..."
BASE_URL=$BASE_URL python3 test_deployment.py

echo "✅ All tests completed!"
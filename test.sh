#!/bin/bash

echo "=== Testing Auth Service ==="
echo ""

echo "1. Health Check:"
curl -s http://localhost:8001/health | jq .
echo ""

echo "2. Login API Test:"
curl -s -X POST http://localhost:8001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"loginId":"admin@saas-platform.local","password":"Admin@123"}' | jq .
echo ""

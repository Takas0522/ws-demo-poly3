#!/bin/bash
# Test Auth Service Login API

OUTPUT_FILE="/workspace/src/auth-service/login_test_result.json"

echo "Testing login API..." > "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

# Execute curl and save output
curl -s -X POST http://localhost:8001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"loginId":"admin@saas-platform.local","password":"Admin@123"}' \
  >> "$OUTPUT_FILE" 2>&1

echo "" >> "$OUTPUT_FILE"
echo "Test completed. Check $OUTPUT_FILE for results."

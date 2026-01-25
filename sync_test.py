import subprocess
import json

# Test health endpoint
print("=== Health Check ===")
result = subprocess.run(
    ['curl', '-s', 'http://localhost:8001/health'],
    capture_output=True,
    text=True
)
print(f"Status Code: {result.returncode}")
print(f"Response: {result.stdout}")

# Test login endpoint
print("\n=== Login Test ===")
result = subprocess.run(
    ['curl', '-s', '-X', 'POST', 
     'http://localhost:8001/api/auth/login',
     '-H', 'Content-Type: application/json',
     '-d', '{"loginId":"admin@saas-platform.local","password":"Admin@123"}'],
    capture_output=True,
    text=True
)
print(f"Status Code: {result.returncode}")
print(f"Response: {result.stdout}")

# Save to file
with open('/workspace/src/auth-service/test_output.txt', 'w') as f:
    f.write("=== Health Check ===\n")
    f.write(result.stdout + "\n\n")
    f.write("=== Login Test ===\n")
    
    # Parse and format JSON
    try:
        data = json.loads(result.stdout)
        f.write(json.dumps(data, indent=2, ensure_ascii=False))
    except:
        f.write(result.stdout)

print("\nOutput saved to test_output.txt")

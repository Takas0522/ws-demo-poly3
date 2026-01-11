# Auth Service (FastAPI)

JWT-based authentication service for the SaaS Management Application with tenant-aware authentication and refresh token mechanism.

## Features

### Authentication
- ✅ JWT token generation with 1-hour expiry (configurable)
- ✅ RS256 algorithm for JWT signing (asymmetric encryption)
- ✅ Refresh token mechanism with CosmosDB storage and TTL
- ✅ Password hashing using bcrypt via passlib
- ✅ Tenant-aware authentication
- ✅ Account lockout after failed login attempts
- ✅ Token revocation support
- ✅ Comprehensive error handling

### Authorization
- ✅ Permission validation middleware with dot notation
- ✅ Route-level permission decorators
- ✅ Wildcard permission support (`users.*`, `admin.*.view`, `*`)
- ✅ Admin override functionality
- ✅ Permission caching with TTL
- ✅ Multiple permission patterns (ANY/ALL)
- ✅ Detailed authorization error messages

## Tech Stack

- **Python 3.11+**
- **FastAPI** - Modern, fast web framework
- **Pydantic** - Data validation
- **python-jose** - JWT handling
- **passlib[bcrypt]** - Password hashing
- **azure-cosmos** - CosmosDB client
- **uvicorn** - ASGI server

## Installation

### Using pip

```bash
pip install -r requirements.txt
```

### Using Poetry (recommended)

```bash
poetry install
```

## Development

### Run the service

```bash
# Using uvicorn directly
uvicorn app.main:app --reload --port 3001

# Or with Python
python -m app.main
```

### Run tests

```bash
# Using pytest
pytest

# With coverage
pytest --cov=app tests/

# Specific test
pytest tests/test_security.py
```

### Code quality

```bash
# Format code
black app/ tests/

# Sort imports
isort app/ tests/

# Type checking
mypy app/

# Linting
flake8 app/ tests/
```

## Environment Variables

The service uses environment variables from the root `.env` file. Key variables:

```env
# Server
AUTH_SERVICE_PORT=3001
NODE_ENV=development

# JWT Configuration
JWT_SECRET=your-super-secret-jwt-key-change-this-in-production
JWT_ALGORITHM=RS256
JWT_EXPIRES_IN=3600
JWT_REFRESH_EXPIRES_IN=604800
JWT_PRIVATE_KEY_PATH=keys/private.pem
JWT_PUBLIC_KEY_PATH=keys/public.pem

# CosmosDB
COSMOSDB_ENDPOINT=https://localhost:8081
COSMOSDB_KEY=<your-cosmosdb-key>
COSMOSDB_DATABASE=saas-management

# Security
MAX_LOGIN_ATTEMPTS=5
LOCKOUT_DURATION_MINUTES=15
PASSWORD_MIN_LENGTH=8
PASSWORD_REQUIRE_UPPERCASE=true
PASSWORD_REQUIRE_LOWERCASE=true
PASSWORD_REQUIRE_NUMBERS=true
PASSWORD_REQUIRE_SPECIAL_CHARS=true

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

## API Endpoints

### Authentication

#### POST /auth/login
Authenticate user and return JWT tokens.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!",
  "tenant_id": "tenant-123"
}
```

**Response:**
```json
{
  "tokens": {
    "access_token": "******",
    "refresh_token": "******",
    "expires_in": 3600,
    "token_type": "Bearer"
  },
  "user": {
    "id": "user-123",
    "email": "user@example.com",
    "display_name": "John Doe",
    "status": "active"
  }
}
```

#### POST /auth/refresh
Refresh access token using refresh token.

**Request:**
```json
{
  "refresh_token": "******"
}
```

**Response:**
```json
{
  "tokens": {
    "access_token": "******",
    "refresh_token": "******",
    "expires_in": 3600,
    "token_type": "Bearer"
  }
}
```

#### POST /auth/logout
Logout user by revoking refresh tokens.

**Headers:**
```
Authorization: ******
```

**Request:**
```json
{
  "refresh_token": "******",
  "all_devices": false
}
```

**Response:**
```json
{
  "success": true,
  "message": "Logged out successfully"
}
```

#### GET /auth/verify
Verify current access token.

**Headers:**
```
Authorization: ******
```

**Response:**
```json
{
  "valid": true,
  "user": {
    "sub": "user-123",
    "email": "user@example.com",
    "tenantId": "tenant-123",
    "roles": ["user"],
    "permissions": ["users.read"]
  }
}
```

#### GET /auth/me
Get current user information from token.

**Headers:**
```
Authorization: ******
```

**Response:**
```json
{
  "id": "user-123",
  "email": "user@example.com",
  "display_name": "John Doe",
  "tenant_id": "tenant-123",
  "roles": ["user"],
  "permissions": ["users.read"]
}
```

### Health Check

#### GET /health
Check service health status.

**Response:**
```json
{
  "status": "healthy",
  "service": "auth-service",
  "version": "1.0.0",
  "timestamp": "2024-01-11T12:00:00.000Z",
  "uptime": 3600.5
}
```

## Project Structure

```
src/auth-service/
├── app/
│   ├── api/              # API route handlers
│   │   ├── auth.py       # Authentication endpoints
│   │   ├── root.py       # Root and health endpoints
│   │   └── examples_authorization.py  # Authorization examples
│   ├── core/             # Core functionality
│   │   ├── config.py     # Configuration management
│   │   └── security.py   # JWT and password utilities
│   ├── middleware/       # FastAPI middleware
│   │   ├── auth.py       # Authentication dependencies
│   │   └── authorization.py  # Authorization and permission checking
│   ├── models/           # Database models (future)
│   ├── schemas/          # Pydantic schemas
│   │   └── auth.py       # Request/response models
│   ├── services/         # Business logic
│   │   ├── auth.py       # Authentication service
│   │   └── cosmosdb.py   # CosmosDB service
│   ├── utils/            # Utility functions
│   └── main.py           # Application entry point
├── tests/                # Test files
│   ├── test_security.py  # Security tests
│   ├── test_jwt.py       # JWT token tests
│   ├── test_authorization.py  # Authorization tests
│   └── test_authorization_integration.py  # Integration tests
├── .gitignore
├── pyproject.toml        # Poetry configuration
├── requirements.txt      # Pip requirements
├── AUTHORIZATION.md      # Authorization middleware documentation
└── README.md
```

## Security Features

### Authentication
- **JWT-based Authentication**: Stateless authentication with access and refresh tokens using RS256 algorithm
- **RS256 Algorithm**: Asymmetric encryption using RSA public/private key pairs for enhanced security
- **Account Lockout**: Configurable failed login attempts and lockout duration
- **Password Hashing**: bcrypt via passlib with automatic salt generation
- **Password Validation**: Configurable complexity requirements
- **Token Revocation**: Support for single and multi-device logout
- **Tenant Isolation**: Users can only access their tenant's resources

### Authorization
- **Permission System**: Dot notation permission system (e.g., `users.read`, `documents.write`)
- **Wildcard Support**: Flexible permission patterns (`users.*`, `admin.*.view`, `*`)
- **Route Protection**: Decorators for easy route-level permission enforcement
- **Admin Override**: Configurable admin role bypass for permission checks
- **Permission Caching**: In-memory cache with TTL for improved performance
- **Detailed Errors**: Clear HTTP 403 responses with missing permission details

For detailed authorization documentation, see [AUTHORIZATION.md](AUTHORIZATION.md)

## RSA Key Management

The service uses RS256 algorithm which requires RSA key pairs:

### Generate Keys

```bash
# Generate a new RSA key pair
python3 -c "
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

# Generate private key
private_key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048,
    backend=default_backend()
)

# Serialize and save keys
private_pem = private_key.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption()
)

public_pem = private_key.public_key().public_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.SubjectPublicKeyInfo
)

with open('keys/private.pem', 'wb') as f:
    f.write(private_pem)
with open('keys/public.pem', 'wb') as f:
    f.write(public_pem)
"
```

### Key Storage

- **Development**: Keys are stored in the `keys/` directory
- **Production**: Use Azure Key Vault or similar secure key management service
- **Private Key**: Never commit to version control (excluded via .gitignore)
- **Public Key**: Can be shared and used for token verification

## Interactive API Documentation

FastAPI automatically generates interactive API documentation:

- **Swagger UI**: http://localhost:3001/docs
- **ReDoc**: http://localhost:3001/redoc

## Production Considerations

1. **JWT Algorithm**: ✅ Using RS256 for better security isolation with asymmetric encryption
2. **Key Management**: Use Azure Key Vault for RSA private keys in production
3. **HTTPS**: Always use HTTPS in production
4. **Monitoring**: Implement proper logging and monitoring
5. **Rate Limiting**: Add rate limiting middleware (e.g., slowapi)
6. **Security Headers**: Add security headers middleware
7. **Key Rotation**: Implement periodic RSA key rotation for enhanced security

## Migration from Node.js/TypeScript

This service replaces the previous Node.js/Express/TypeScript implementation with Python/FastAPI, providing:

- Better performance with async/await
- Automatic API documentation
- Built-in data validation with Pydantic
- Type hints for better code quality
- Easier testing with pytest

## License

MIT

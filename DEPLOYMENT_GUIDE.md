# DogTorVet API Deployment Guide

## Overview
This guide covers the deployment and configuration of the DogTorVet API for both development and production environments.

## Recent Fixes Applied

### 1. CORS Configuration (Production-Ready)
The CORS configuration has been updated to properly handle both development and production environments:

```python
# Production origins
- https://dogtorvetservices.onrender.com
- https://dogtorvet-ui.onrender.com
- https://www.dogtorvetservices.com
- https://dogtorvetservices.com

# Development origins
- http://localhost:3000, 5173, 5174
- http://127.0.0.1:3000, 5173, 5174
```

### 2. Route Consistency
All routes have been verified to ensure:
- ✅ Consistent use of trailing slashes
- ✅ Authentication on all endpoints
- ✅ Proper error handling
- ✅ Correct model validation

### 3. Pet Registration Fixes
- Fixed Pydantic v2 compatibility issues
- Made `breed_id` and `color` fields optional
- Fixed date validation for `dob` field
- Ensured proper ObjectId handling for optional fields

### 4. Model Updates
- Updated all models to use Pydantic v2 syntax
- Changed from `Config` class to `model_config` with `ConfigDict`
- Updated `dict()` method calls to `model_dump()`
- Fixed field validators to use `@field_validator`

## Environment Variables

### Required for Production
```bash
# Database
MONGODB_URL=mongodb+srv://username:password@cluster.mongodb.net/dogtorvet
DATABASE_NAME=dogtorvet

# Security
SECRET_KEY=your-production-secret-key-change-this
ENVIRONMENT=production

# Admin User (for initial seeding)
ROOT_USER_EMAIL=admin@yourdomain.com
ROOT_USER_PASSWORD=SecurePasswordChangeThis!
```

### Development Defaults
```bash
# Database
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=dogtorvet

# Security
SECRET_KEY=development-secret-key-CHANGE-IN-PRODUCTION
ENVIRONMENT=development

# Admin User
ROOT_USER_EMAIL=admin@dogtorvet.com
ROOT_USER_PASSWORD=ChangeMeInProduction123!
```

## Deployment Steps

### 1. Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your values

# Run the server
python main.py
# or
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Production Deployment (Render.com)

#### Backend Setup
1. Connect your GitHub repository to Render
2. Create a new Web Service
3. Set the following:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Environment**: Python 3.11+

4. Add environment variables in Render dashboard:
   ```
   MONGODB_URL=your_mongodb_connection_string
   DATABASE_NAME=dogtorvet
   SECRET_KEY=your_secure_secret_key
   ENVIRONMENT=production
   ROOT_USER_EMAIL=admin@yourdomain.com
   ROOT_USER_PASSWORD=YourSecurePassword123!
   ```

#### Frontend Setup
1. Update the API URL in your frontend code:
   ```typescript
   // src/api/axios.ts
   const API_URL = import.meta.env.VITE_API_URL || 'https://your-backend-url.onrender.com/api';
   ```

2. Build the frontend with the correct environment variable:
   ```bash
   VITE_API_URL=https://your-backend-url.onrender.com/api npm run build
   ```

### 3. MongoDB Atlas Setup
1. Create a free cluster on MongoDB Atlas
2. Whitelist Render's IP addresses (or allow access from anywhere for simplicity)
3. Create a database user with read/write permissions
4. Get your connection string and update `MONGODB_URL`

## Testing

### Run Endpoint Tests
```bash
# Make sure the server is running first
python test_endpoints.py
```

This will test:
- Authentication
- All CRUD operations
- Route consistency
- Error handling

### Manual Testing with curl
```bash
# Login
curl -X POST http://localhost:8000/api/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@dogtorvet.com","password":"ChangeMeInProduction123!"}'

# Use the token for authenticated requests
curl -X GET http://localhost:8000/api/pets/ \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

## Common Issues and Solutions

### 1. CORS Errors
- Ensure your frontend URL is in the allowed origins list
- Check that the environment variable is set correctly
- Verify the frontend is using the correct API URL

### 2. MongoDB Connection Issues
- Verify MongoDB is running (local) or accessible (cloud)
- Check connection string format
- Ensure database user has proper permissions

### 3. Authentication Failures
- Verify the secret key is set
- Check token expiration settings
- Ensure the root user was seeded properly

### 4. Import Errors (Pylance)
The import errors shown by Pylance are typically due to virtual environment issues and don't affect runtime. To fix:
```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Select the interpreter in VS Code
# Ctrl+Shift+P -> Python: Select Interpreter -> Choose venv
```

## Security Checklist

Before deploying to production:
- [ ] Change all default passwords
- [ ] Generate a secure `SECRET_KEY`
- [ ] Set `ENVIRONMENT=production`
- [ ] Use HTTPS for all endpoints
- [ ] Configure proper MongoDB access controls
- [ ] Review and restrict CORS origins
- [ ] Enable rate limiting
- [ ] Set up proper logging and monitoring

## Monitoring

### Health Check Endpoints
- `GET /` - Basic API info
- `GET /health` - Detailed health status

### Logs
The application uses structured logging. In production, consider:
- Aggregating logs with a service like Papertrail or Loggly
- Setting up alerts for errors
- Monitoring API response times

## Support

For issues or questions:
1. Check the logs for detailed error messages
2. Verify all environment variables are set correctly
3. Test with the `test_endpoints.py` script
4. Check MongoDB connection and permissions 
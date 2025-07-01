## DogTorVet FastAPI Backend

A modern, high-performance veterinary management system API built with FastAPI and MongoDB.

### 🎯 Features

- 🚀 **FastAPI Framework**: High-performance, modern Python API framework
- 🔐 **JWT Authentication**: Secure token-based authentication with refresh tokens
- 📊 **MongoDB Integration**: NoSQL database with async operations
- 🔍 **Auto-generated Documentation**: Interactive API docs at `/docs` and `/redoc`
- 🛡️ **Input Validation**: Pydantic models for request/response validation
- 🌐 **CORS Support**: Cross-origin resource sharing for frontend integration
- ⚡ **Async Operations**: Non-blocking database operations for better performance
- 🎯 **RESTful Design**: Clean, consistent API endpoints
- 🔧 **Role-based Access**: Admin, veterinarian, and assistant roles
- 📱 **Modern Response Format**: Consistent JSON responses with pagination
- 🌱 **Database Seeding**: Automatic root user creation on startup
- 🔒 **Environment Variables**: Secure configuration management

### 🚀 Quick Start

#### Prerequisites
- Python 3.8+
- MongoDB Atlas account (or local MongoDB)
- Git

#### Local Development

1. **Clone and setup**
   ```bash
   git clone <repository-url>
   cd FastAPI
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Environment Configuration**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration:
   ```

   ```env
   # Required Environment Variables
   MONGODB_URL=mongodb+srv://user:pass@cluster.mongodb.net/db
   SECRET_KEY=your-super-secret-jwt-key
   ROOT_USER_PASSWORD=your-admin-password
   ```

3. **Run the application**
   ```bash
   python main.py
   ```

4. **Access the API**
   - **API**: http://localhost:8000
   - **Swagger Docs**: http://localhost:8000/docs
   - **ReDoc**: http://localhost:8000/redoc
   - **Health Check**: http://localhost:8000/health

### 🌱 Database Seeding

The application automatically creates a root admin user on startup. You can also run the seeder manually:

```bash
# Create root user
python seed.py

# Check if root user exists
python seed.py --check

# Reset root user password
python seed.py --reset-password
```

**Default Root User:**
- Email: `admin@dogtorvet.com`
- Password: Set via `ROOT_USER_PASSWORD` environment variable
- Role: `admin`

### 📚 API Endpoints

#### Authentication
- `POST /api/register` - Register new user
- `POST /api/login` - User login
- `POST /api/refresh` - Refresh access token
- `POST /api/logout` - User logout
- `GET /api/me` - Get current user info

#### Core Entities
- **Users**: `/api/users/*` (Admin management)
- **Clients**: `/api/clients/*` (Pet owners)
- **Pets**: `/api/pets/*` (Animal records)
- **Species**: `/api/species/*` (Animal species)
- **Breeds**: `/api/breeds/*` (Animal breeds)
- **Services**: `/api/services/*` (Veterinary services)
- **Products**: `/api/products/*` (Clinic products)
- **Appointments**: `/api/appointments/*` (Scheduling)
- **Invoices**: `/api/invoices/*` (Billing)

Full API documentation available at `/docs` when running.

### 🚀 Production Deployment (Render)

#### Automatic Deployment

1. **Connect Repository**
   - Link your GitHub repo to Render
   - The `render.yaml` automatically configures deployment

2. **Environment Variables**
   - Render auto-generates secure values for `SECRET_KEY` and `ROOT_USER_PASSWORD`
   - Update `MONGODB_URL` with your MongoDB Atlas connection string

3. **Deploy**
   - Push to main branch triggers automatic deployment
   - Database seeding runs automatically on startup

#### Manual Environment Setup

Required environment variables:

```env
# Database
MONGODB_URL=mongodb+srv://user:pass@cluster.mongodb.net/db
DATABASE_NAME=dogtorvet

# Security (Render auto-generates these)
SECRET_KEY=auto-generated-secure-key
ROOT_USER_PASSWORD=auto-generated-secure-password

# Application
DEBUG=false
ENVIRONMENT=production
HOST=0.0.0.0
PORT=8000

# CORS
ALLOWED_ORIGINS=http://localhost:3000,https://your-frontend.onrender.com
```

### 🏗️ Project Structure

```
FastAPI/
├── 📄 main.py              # Application entry point with auto-seeding
├── ⚙️ config.py            # Environment-based configuration
├── 🗄️ database.py          # MongoDB async connection
├── 📁 models/              # Pydantic data models
│   ├── user.py
│   ├── client.py
│   ├── pet.py
│   └── ...
├── 📁 routes/              # API route handlers
│   ├── auth.py
│   ├── users.py
│   ├── pets.py
│   └── ...
├── 📁 utils/               # Authentication & dependencies
├── 📁 seeders/             # Database seeding
│   ├── __init__.py
│   └── root_user_seeder.py
├── 📋 requirements.txt     # Python dependencies
├── 🐳 Dockerfile           # Container configuration
├── ☁️ render.yaml          # Render deployment config
├── 📝 .env.example         # Environment template
└── 📖 README.md           # This documentation
```

### 🔧 Development Workflow

1. **Add New Entity**
   ```bash
   # 1. Create Pydantic model in models/
   # 2. Create route handler in routes/
   # 3. Register router in main.py
   # 4. Test with auto-generated docs
   ```

2. **Environment Variables**
   - Development: Use `.env` file
   - Production: Set in Render dashboard or `render.yaml`
   - Never commit sensitive values to Git

3. **Database Operations**
   - All operations are async using Motor (async MongoDB driver)
   - Automatic connection management with lifespan events
   - Built-in error handling and validation

### 🧪 Testing

#### Using Interactive Docs
1. Start the server: `python main.py`
2. Open: http://localhost:8000/docs
3. Authenticate using the root user credentials
4. Test all endpoints interactively

#### API Testing Tools
- **Swagger UI**: Built-in at `/docs`
- **ReDoc**: Alternative docs at `/redoc`
- **Postman**: Import OpenAPI spec from `/openapi.json`
- **curl**: Command-line testing
- **VS Code REST Client**: Use `.http` files

### 🔐 Security Features

- **JWT Authentication**: Secure token-based auth
- **Password Hashing**: bcrypt with configurable rounds
- **Environment Variables**: Sensitive data stored securely
- **CORS Configuration**: Controlled cross-origin access
- **Input Validation**: Pydantic model validation
- **Role-based Access**: Admin/Vet/Assistant permissions

### 📈 Performance Features

- **Async Operations**: Non-blocking database operations
- **Connection Pooling**: MongoDB connection optimization
- **Pagination**: Efficient data loading with skip/limit
- **Caching**: Response optimization for static data
- **Lightweight**: Minimal memory footprint for cloud hosting

### 🔄 Migration from Laravel

This FastAPI backend provides identical functionality to the Laravel API:

| Feature | Laravel | FastAPI | Status |
|---------|---------|---------|--------|
| Authentication | Passport OAuth2 | JWT | ✅ Complete |
| Database | MySQL/PostgreSQL | MongoDB | ✅ Complete |
| Models | Eloquent ORM | Pydantic | ✅ Complete |
| Routes | 50+ endpoints | 50+ endpoints | ✅ Complete |
| Validation | Form Requests | Pydantic | ✅ Complete |
| Documentation | Manual | Auto-generated | ✅ Improved |

### 🚨 Troubleshooting

#### Common Issues

1. **MongoDB Connection Errors**
   ```bash
   # Check MONGODB_URL format
   # Verify network access to MongoDB Atlas
   # Ensure database user has proper permissions
   ```

2. **Import Errors**
   ```bash
   # Activate virtual environment
   source venv/bin/activate  # or venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Environment Variables**
   ```bash
   # Copy example file
   cp .env.example .env
   # Edit with your values
   ```

#### Logging
- Development: Detailed logs to console
- Production: Structured logging for monitoring
- Health check endpoint: `/health`

### 🎉 Success Indicators

✅ **Deployment Successful** when you see:
```
✅ Connected to MongoDB
🎉 Root user 'admin@dogtorvet.com' created successfully!
✅ Database seeding completed
INFO: Started server process
INFO: Uvicorn running on http://0.0.0.0:8000
```

✅ **API Working** when:
- `/health` returns 200 OK
- `/docs` shows interactive documentation
- Authentication endpoints accept login requests
- All CRUD operations work as expected

---

**🚀 Ready for production deployment on Render with automatic scaling and MongoDB Atlas integration!** 
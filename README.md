# DogTorVet API - Backend

A modern veterinary management system API built with FastAPI, MongoDB, and Python.

## 🚀 Production Deployment

The API is deployed on Render at: **https://dogtorvet-api.onrender.com**

### API Documentation

- **Interactive Docs**: https://dogtorvet-api.onrender.com/docs
- **ReDoc**: https://dogtorvet-api.onrender.com/redoc
- **Health Check**: https://dogtorvet-api.onrender.com/health

### Environment Configuration

The API automatically configures for production when deployed on Render:
- **Database**: MongoDB Atlas (production cluster)
- **Authentication**: JWT with secure tokens
- **CORS**: Configured for production frontend
- **Security**: HTTPS enforced, secure headers

## 🛠️ Development

### Prerequisites

- Python 3.11+
- MongoDB (local or Atlas)
- pip

### Installation

```bash
pip install -r requirements.txt
```

### Development Server

```bash
python main.py
```

The API will be available at `http://localhost:8000`

### Environment Variables

Create a `.env` file for local development:

```env
DATABASE_URL=mongodb://localhost:27017/dogtorvet
SECRET_KEY=your-secret-key-here
DEBUG=true
ENVIRONMENT=development
```

## 📁 Project Structure

```
app/
├── api/           # API endpoints
│   └── v1/       # Version 1 API routes
├── core/          # Core configuration
├── crud/          # Database operations
├── db/            # Database connection
├── models/        # Database models
├── schemas/       # Pydantic schemas
└── services/      # Business logic
```

## 🎯 Features

- **RESTful API**: Complete CRUD operations
- **Authentication**: JWT-based auth with refresh tokens
- **Authorization**: Role-based access control
- **Database**: MongoDB with Motor async driver
- **Validation**: Pydantic schema validation
- **Documentation**: Auto-generated OpenAPI docs
- **CORS**: Cross-origin resource sharing
- **Error Handling**: Comprehensive error responses

## 🔧 Key Technologies

- **FastAPI** - Modern Python web framework
- **MongoDB** - NoSQL database
- **Motor** - Async MongoDB driver
- **Pydantic** - Data validation
- **JWT** - Authentication
- **Uvicorn** - ASGI server

## 🔒 Security Features

- JWT token authentication
- Password hashing with bcrypt
- CORS protection
- Input validation
- SQL injection prevention
- XSS protection
- Rate limiting ready

## 📊 API Endpoints

### Authentication
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/refresh` - Refresh token
- `POST /api/v1/auth/logout` - User logout

### Core Entities
- **Users**: `/api/v1/users`
- **Clients**: `/api/v1/clients`
- **Pets**: `/api/v1/pets`
- **Appointments**: `/api/v1/appointments`
- **Invoices**: `/api/v1/invoices`
- **Services**: `/api/v1/services`
- **Products**: `/api/v1/products`

### Medical Records
- **Allergies**: `/api/v1/allergies`
- **Vaccinations**: `/api/v1/vaccinations`
- **Species**: `/api/v1/species`
- **Breeds**: `/api/v1/breeds`

## 🚀 Performance

- Async/await throughout
- Database connection pooling
- Optimized queries
- Response caching ready
- CDN integration ready

## 📈 Monitoring

- Health check endpoint
- Structured logging
- Error tracking
- Performance metrics
- Database monitoring

## 🔧 Deployment

### Render Configuration

The API is configured for automatic deployment on Render with:
- Python environment
- MongoDB Atlas connection
- Environment variables
- Health checks
- Auto-scaling ready

### Environment Variables

Production environment variables are configured in `render.yaml`:
- Database connection
- Security keys
- CORS origins
- Admin user setup 
# DogTorVet API Documentation

## Overview

The DogTorVet API is a RESTful web service built with FastAPI that provides comprehensive veterinary clinic management functionality. All endpoints return JSON responses and require authentication (except auth endpoints).

**Base URL**: `https://dogtorver-api/api` (production) or `http://localhost:8000/api` (development)

**Authentication**: JWT Bearer tokens required for all endpoints except `/auth/login` and `/auth/register`

## Table of Contents

1. [Authentication](#authentication)
2. [Users Management](#users-management)
3. [Clients](#clients)
4. [Pets](#pets)
5. [Species & Breeds](#species--breeds)
6. [Appointments](#appointments)
7. [Services](#services)
8. [Products](#products)
9. [Invoices](#invoices)
10. [Invoice Items](#invoice-items)
11. [Allergies](#allergies)
12. [Vaccinations](#vaccinations)
13. [Analytics](#analytics)
14. [Audit Logs](#audit-logs)

## Common Response Formats

### Success Response
```json
{
  "data": {...},
  "message": "Success message"
}
```

### Paginated Response
```json
{
  "data": [...],
  "meta": {
    "current_page": 1,
    "per_page": 15,
    "total": 100,
    "last_page": 7,
    "from": 1,
    "to": 15
  },
  "links": {
    "prev": null,
    "next": "?page=2&per_page=15",
    "first": "?page=1&per_page=15",
    "last": "?page=7&per_page=15"
  },
  "path": "/api/resource"
}
```

### Error Response
```json
{
  "detail": "Error message"
}
```

## Authentication

### POST /auth/register
Register a new user account.

**Request Body:**
```json
{
  "first_name": "string",
  "last_name": "string", 
  "email": "user@example.com",
  "password": "string (min 6 chars)",
  "phone": "string (optional)",
  "role": "admin|vet (optional, default: vet)",
  "specialization": "string (optional)"
}
```

**Response:** User object with generated ID

### POST /auth/login
Authenticate and receive JWT tokens.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "string"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Login successful",
  "data": {
    "token": "access_token_here",
    "refresh_token": "refresh_token_here",
    "token_type": "bearer"
  }
}
```

### POST /auth/refresh
Refresh access token using refresh token.

**Headers:** `Authorization: Bearer {refresh_token}`

**Response:** New token pair

### GET /auth/me
Get current authenticated user info.

**Headers:** `Authorization: Bearer {access_token}`

**Response:** User object

## Users Management

### GET /users
Get paginated list of users.

**Query Parameters:**
- `page` (int): Page number (default: 1)
- `per_page` (int): Items per page (default: 15, max: 100)
- `search` (string): Search by name or email

**Response:** Paginated list of users

### GET /users/{user_id}
Get specific user by ID.

**Response:** User object

### POST /users
Create new user (admin only).

**Request Body:** Same as registration

**Response:** Created user object

### PUT /users/{user_id}
Update user information.

**Request Body:** Partial user object (only fields to update)

**Response:** Updated user object

### DELETE /users/{user_id}
Soft delete user (sets status to false).

**Response:** Success message

## Clients

### GET /clients
Get paginated list of clients (pet owners).

**Query Parameters:**
- `page`, `per_page`: Pagination
- `search`: Search by name or phone

**Response:** Paginated list of clients

### GET /clients/{client_id}
Get specific client details.

### POST /clients
Create new client.

**Request Body:**
```json
{
  "name": "string",
  "gender": "male|female|other",
  "phone_number": "string (unique)",
  "other_contact_info": "string (optional)"
}
```

### PUT /clients/{client_id}
Update client information.

### DELETE /clients/{client_id}
Soft delete client.

## Pets

### GET /pets
Get paginated list of pets.

**Query Parameters:**
- `page`, `per_page`: Pagination
- `search`: Search by name or color
- `client_id`: Filter by owner
- `species_id`: Filter by species
- `breed_id`: Filter by breed
- `gender`: Filter by gender
- `status`: Filter by status (active/inactive/all)
- `include`: Comma-separated relationships (client,species,breed,allergies,vaccinations)

**Response:** Paginated list with optional relationships

### GET /pets/{pet_id}
Get specific pet details.

### POST /pets
Register new pet.

**Request Body:**
```json
{
  "name": "string",
  "gender": "male|female",
  "dob": "2020-01-01",
  "species_id": "string",
  "breed_id": "string",
  "weight": 10.5,
  "color": "string",
  "medical_history": "string (optional)",
  "client_id": "string"
}
```

### PUT /pets/{pet_id}
Update pet information.

### DELETE /pets/{pet_id}
Soft delete pet.

### POST /pets/{pet_id}/allergies
Add allergy to pet.

### DELETE /pets/{pet_id}/allergies/{allergy_id}
Remove allergy from pet.

### POST /pets/{pet_id}/vaccinations
Add vaccination record.

### DELETE /pets/{pet_id}/vaccinations/{vaccination_id}
Remove vaccination record.

## Species & Breeds

### GET /species
Get list of animal species.

**Query Parameters:**
- Pagination and search
- `status`: Filter active/inactive/all

### POST /species
Create new species (unique name).

### GET /breeds
Get list of breeds.

**Query Parameters:**
- `species_id`: Filter by species
- Other standard filters

### POST /breeds
Create new breed (unique per species).

## Appointments

### GET /appointments
Get appointment list.

**Query Parameters:**
- `appointment_status`: scheduled|confirmed|in_progress|completed|cancelled|no_show
- `appointment_date_from`, `appointment_date_to`: Date range
- `include`: Related data (client,pet,service,user)

### POST /appointments
Schedule new appointment.

**Request Body:**
```json
{
  "client_id": "string",
  "pet_id": "string",
  "service_id": "string (optional)",
  "user_id": "string (vet ID)",
  "appointment_date": "2024-01-01T10:00:00",
  "duration_minutes": 30,
  "notes": "string (optional)"
}
```

### PUT /appointments/{appointment_id}
Update appointment (including status changes).

## Services

### GET /services
Get available veterinary services.

### POST /services
Create new service type.

**Request Body:**
```json
{
  "name": "string",
  "description": "string",
  "price": 50.00,
  "duration_minutes": 30
}
```

## Products

### GET /products
Get product inventory.

### POST /products
Add new product.

**Request Body:**
```json
{
  "name": "string",
  "description": "string", 
  "price": 20.00,
  "stock_quantity": 100,
  "sku": "string (unique, optional)"
}
```

**Note:** Stock is automatically decremented when invoices are marked as paid.

## Invoices

### GET /invoices
Get invoice list with client/pet info populated.

### POST /invoices
Create new invoice.

**Request Body:**
```json
{
  "client_id": "string",
  "pet_id": "string (optional)",
  "invoice_date": "2024-01-01",
  "due_date": "2024-01-31 (optional)",
  "discount_percent": 10,
  "payment_status": "pending|paid|overdue|cancelled",
  "notes": "string (optional)"
}
```

**Note:** Invoice number is auto-generated as `INV{YY}{MM}{DD}NO{sequence}`

### PUT /invoices/{invoice_id}
Update invoice. When payment_status changes to "paid", product stock is decremented.

### GET /invoices/{invoice_id}/pdf
Generate PDF invoice (currently disabled).

## Invoice Items

### GET /invoice-items
Get invoice line items.

**Query Parameters:**
- `invoice_id`: Filter by invoice
- `item_type`: service|product

### POST /invoice-items
Add item to invoice.

**Request Body:**
```json
{
  "invoice_id": "string",
  "item_type": "service|product",
  "service_id": "string (if service)",
  "product_id": "string (if product)", 
  "item_name": "string",
  "item_description": "string (optional)",
  "unit_price": 25.00,
  "quantity": 2,
  "discount_percent": 0
}
```

**Note:** `net_price` is calculated automatically. Invoice totals update automatically.

### PUT /invoice-items/{item_id}
Update line item.

### DELETE /invoice-items/{item_id}
Soft delete line item (updates invoice totals).

## Allergies

### GET /allergies
Get allergy types list.

**Query Parameters:**
- `status`: active|inactive|all
- `search`: Search by name/description

### POST /allergies
Create new allergy type.

**Request Body:**
```json
{
  "name": "string (unique)",
  "description": "string (optional)"
}
```

### PUT /allergies/{allergy_id}/toggle-status
Toggle active/inactive status.

## Vaccinations

### GET /vaccinations
Get vaccination types list.

### POST /vaccinations
Create new vaccination type.

**Request Body:**
```json
{
  "name": "string (unique)",
  "description": "string (optional)",
  "duration_months": 12
}
```

## Analytics

### GET /analytics/dashboard
Get dashboard statistics.

**Query Parameters:**
- `period`: Days to analyze (7, 30, 90, 365)

**Response:**
```json
{
  "overview": {
    "total_clients": 150,
    "total_pets": 200,
    "total_appointments": 500,
    "recent_appointments": 50,
    "period_revenue": 5000.00,
    "upcoming_appointments": 10
  },
  "trends": {
    "appointments": [...],
    "revenue": [...]
  },
  "analytics": {
    "top_services": [...],
    "species_distribution": [...],
    "revenue_growth": 15.5
  }
}
```

### GET /analytics/appointments-by-month
Get monthly appointment counts for a year.

### GET /analytics/revenue-by-month
Get monthly revenue for a year.

### GET /analytics/performance
Get system performance metrics (admin only).

### GET /analytics/reports/revenue
Generate detailed revenue report.

**Query Parameters:**
- `start_date`, `end_date`: Date range (YYYY-MM-DD)
- `group_by`: day|week|month

## Audit Logs

### GET /audit-logs/deletions
Get hard deletion history (admin only).

**Query Parameters:**
- `collection_name`: Filter by collection
- `user_id`: Filter by who deleted
- `start_date`, `end_date`: Date range
- `limit`: Max records (default: 100)

### GET /audit-logs/deletions/{audit_log_id}
Get specific deletion details with restoration possibility check.

### POST /audit-logs/deletions/{audit_log_id}/restore
Restore a hard-deleted document (admin only).

### POST /audit-logs/hard-delete/{collection}/{document_id}
Perform hard deletion with audit trail (admin only).

**Query Parameters:**
- `reason`: Optional deletion reason

**Warning:** This permanently deletes data. Soft deletion is preferred.

## Error Codes

- `400` - Bad Request (validation error)
- `401` - Unauthorized (invalid/missing token)
- `403` - Forbidden (insufficient permissions)
- `404` - Not Found
- `422` - Unprocessable Entity (invalid data format)
- `500` - Internal Server Error

## Rate Limiting

- Authentication endpoints: 5-10 requests/minute
- Regular endpoints: 100 requests/minute per user

## Best Practices

1. **Always use pagination** for list endpoints
2. **Include only needed relationships** with the `include` parameter
3. **Use soft deletion** (status=false) instead of hard deletion
4. **Check unique constraints** before creating/updating
5. **Handle token refresh** in your client application
6. **Log errors** for debugging

## Webhook Events (Future)

Planned webhook events for external integrations:
- `appointment.created`
- `appointment.reminder`
- `invoice.paid`
- `inventory.low_stock`

## SDK Examples

### JavaScript/TypeScript
```typescript
const response = await fetch('http://localhost:8000/api/clients', {
  headers: {
    'Authorization': `Bearer ${accessToken}`,
    'Content-Type': 'application/json'
  }
});
const data = await response.json();
```

### Python
```python
import httpx

async with httpx.AsyncClient() as client:
    response = await client.get(
        "http://localhost:8000/api/clients",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    data = response.json()
```

---

For interactive API testing, visit `/docs` (Swagger UI) or `/redoc` (ReDoc) when running the server.
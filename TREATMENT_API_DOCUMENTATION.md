# Treatment Suggestions API Documentation

## Overview

The Treatment Suggestions API provides endpoints for managing skin condition treatment recommendations. This API allows administrators to create, update, and delete treatment suggestions, while providing public access for the analysis section to retrieve treatment data.

## Base URL
```
http://localhost:5000/api/treatment
```

## Authentication

### Admin Endpoints
Admin endpoints require JWT authentication with admin role:
- **Header:** `Authorization: Bearer <JWT_TOKEN>`
- **Login Endpoint:** `POST /api/auth/login`
- **Admin Credentials:**
  - Email: `admin@facialdermaai.com`
  - Password: `Admin@123`
  - Role: `admin`

### Public Endpoints
Public endpoints do not require authentication and can be accessed by the frontend analysis section.

## Data Schema

### Treatment Suggestion Object
```json
{
  "id": "string",
  "name": "string",
  "treatments": ["string"],
  "prevention": ["string"],
  "resources": ["string"],
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

## Endpoints

### 1. Get All Treatment Suggestions
**Endpoint:** `GET /api/treatment/suggestions`  
**Authentication:** None (Public)  
**Description:** Retrieve all treatment suggestions for skin conditions.

#### Response
**Status:** 200 OK
```json
[
  {
    "id": "507f1f77bcf86cd799439011",
    "name": "Acne",
    "treatments": [
      "Use a gentle, non-comedogenic cleanser twice daily",
      "Apply benzoyl peroxide 2.5% wash"
    ],
    "prevention": [
      "Avoid picking or squeezing pimples",
      "Change pillowcases weekly"
    ],
    "resources": [
      "American Academy of Dermatology (AAD) – Acne: https://www.aad.org/public/diseases/acne"
    ],
    "created_at": "2025-12-13T10:30:00Z",
    "updated_at": "2025-12-13T10:30:00Z"
  }
]
```

#### Error Responses
- **500 Internal Server Error:** Database or server error

---

### 2. Get Treatment Suggestion by Name
**Endpoint:** `GET /api/treatment/suggestions/{name}`  
**Authentication:** None (Public)  
**Description:** Retrieve a specific treatment suggestion by condition name.

#### Parameters
- **name** (path): Name of the skin condition (e.g., "Acne", "Eczema")

#### Response
**Status:** 200 OK
```json
{
  "id": "507f1f77bcf86cd799439011",
  "name": "Acne",
  "treatments": [
    "Use a gentle, non-comedogenic cleanser twice daily",
    "Apply benzoyl peroxide 2.5% wash"
  ],
  "prevention": [
    "Avoid picking or squeezing pimples",
    "Change pillowcases weekly"
  ],
  "resources": [
    "American Academy of Dermatology (AAD) – Acne: https://www.aad.org/public/diseases/acne"
  ],
  "created_at": "2025-12-13T10:30:00Z",
  "updated_at": "2025-12-13T10:30:00Z"
}
```

#### Error Responses
- **404 Not Found:** Treatment suggestion not found
- **500 Internal Server Error:** Database or server error

---

### 3. Create Treatment Suggestion
**Endpoint:** `POST /api/treatment/suggestions`  
**Authentication:** Required (Admin only)  
**Description:** Create a new treatment suggestion.

#### Headers
- `Authorization: Bearer <JWT_TOKEN>`
- `Content-Type: application/json`

#### Request Body
```json
{
  "name": "Acne",
  "treatments": [
    "Use a gentle, non-comedogenic cleanser twice daily",
    "Apply benzoyl peroxide 2.5% wash",
    "Use salicylic acid 0.5–2% exfoliant or cleanser",
    "Apply an oil-free, non-comedogenic moisturizer"
  ],
  "prevention": [
    "Avoid picking or squeezing pimples",
    "Change pillowcases weekly",
    "Use non-comedogenic makeup"
  ],
  "resources": [
    "American Academy of Dermatology (AAD) – Acne: https://www.aad.org/public/diseases/acne",
    "NHS (UK) – Acne: https://www.nhs.uk/conditions/acne",
    "Mayo Clinic – Acne: https://www.mayoclinic.org/diseases-conditions/acne"
  ]
}
```

#### Response
**Status:** 201 Created
```json
{
  "id": "507f1f77bcf86cd799439011",
  "name": "Acne",
  "treatments": [...],
  "prevention": [...],
  "resources": [...],
  "created_at": "2025-12-13T10:30:00Z",
  "updated_at": "2025-12-13T10:30:00Z"
}
```

#### Error Responses
- **400 Bad Request:** Invalid data or duplicate name
- **401 Unauthorized:** Missing or invalid token
- **403 Forbidden:** Insufficient permissions (not admin)
- **500 Internal Server Error:** Database or server error

---

### 4. Update Treatment Suggestion
**Endpoint:** `PUT /api/treatment/suggestions/{name}`  
**Authentication:** Required (Admin only)  
**Description:** Update an existing treatment suggestion.

#### Parameters
- **name** (path): Name of the skin condition to update

#### Headers
- `Authorization: Bearer <JWT_TOKEN>`
- `Content-Type: application/json`

#### Request Body
Only include fields you want to update:
```json
{
  "treatments": [
    "Use a gentle, non-comedogenic cleanser twice daily",
    "Apply benzoyl peroxide 2.5% wash",
    "Use salicylic acid 0.5–2% exfoliant or cleanser",
    "Apply an oil-free, non-comedogenic moisturizer",
    "Consider consulting a dermatologist for severe cases"
  ]
}
```

#### Response
**Status:** 200 OK
```json
{
  "id": "507f1f77bcf86cd799439011",
  "name": "Acne",
  "treatments": [...],
  "prevention": [...],
  "resources": [...],
  "created_at": "2025-12-13T10:30:00Z",
  "updated_at": "2025-12-13T11:45:00Z"
}
```

#### Error Responses
- **401 Unauthorized:** Missing or invalid token
- **403 Forbidden:** Insufficient permissions (not admin)
- **404 Not Found:** Treatment suggestion not found
- **500 Internal Server Error:** Database or server error

---

### 5. Delete Treatment Suggestion
**Endpoint:** `DELETE /api/treatment/suggestions/{name}`  
**Authentication:** Required (Admin only)  
**Description:** Delete a treatment suggestion.

#### Parameters
- **name** (path): Name of the skin condition to delete

#### Headers
- `Authorization: Bearer <JWT_TOKEN>`

#### Response
**Status:** 200 OK
```json
{
  "message": "Treatment suggestion for 'Acne' deleted successfully"
}
```

#### Error Responses
- **401 Unauthorized:** Missing or invalid token
- **403 Forbidden:** Insufficient permissions (not admin)
- **404 Not Found:** Treatment suggestion not found
- **500 Internal Server Error:** Database or server error

## Sample Data

Based on the `treatmentSuggestions.json` file, here are the expected skin conditions:

- **Acne**
- **Eczema**
- **Melasma**
- **Seborrheic Dermatitis**
- **Rosacea**
- **Normal** (for normal skin)

## Testing with Postman

### 1. Login as Admin
```
POST /api/auth/login
Content-Type: application/json

{
  "emailOrUsername": "admin@facialdermaai.com",
  "password": "Admin@123",
  "role": "admin"
}
```

### 2. Use Token for Admin Operations
Add header: `Authorization: Bearer <token_from_login>`

### 3. Test Endpoints
Follow the examples above for each endpoint.

## Error Handling

All endpoints return appropriate HTTP status codes and error messages:

- **200 OK:** Successful GET/PUT operations
- **201 Created:** Successful POST operations
- **400 Bad Request:** Invalid request data
- **401 Unauthorized:** Authentication required
- **403 Forbidden:** Insufficient permissions
- **404 Not Found:** Resource not found
- **500 Internal Server Error:** Server/database errors

## Database

- **Collection:** `treatment_suggestions`
- **Indexes:** Unique index on `name` field
- **Engine:** MongoDB with Motor (async driver)

## Notes

- The API does not import data from `treatmentSuggestions.json` - data must be created via the admin endpoints
- All timestamps are in UTC
- The `name` field is case-sensitive and must be unique
- Arrays can be empty but must be provided as arrays
- Public endpoints are designed for the frontend analysis section
- Admin endpoints are protected and require proper authentication</content>
<parameter name="filePath">d:\FYP\FacialDermaAi_backend\TREATMENT_API_DOCUMENTATION.md
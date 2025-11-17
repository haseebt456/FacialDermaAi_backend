# Dermatologist Review Workflow - Testing Guide

## Overview
This guide provides step-by-step instructions for testing the new dermatologist review workflow features.

## Features Implemented

### FR01 - User Management ✓
- **FR01-01**: User Registration (existing, supports patient and dermatologist roles)
- **FR01-02**: User Login (existing, with role validation)
- **FR01-03**: Profile Management (existing `/api/users/me` endpoint)

### FR02 - Multiple User Role Management ✓
- **FR02-01**: Multiple user roles supported (patient, dermatologist)
- **FR02-02**: Role-based access control (RBAC) implemented
- **FR02-03**: Dermatologist review and feedback system implemented

## New API Endpoints

### 1. List Dermatologists
```
GET /api/users/dermatologists
Authorization: Bearer <token>
Query Parameters:
  - q: (optional) Search by username or email
  - limit: (optional, default 50) Max results
  - offset: (optional, default 0) Pagination offset

Response: 200 OK
{
  "dermatologists": [
    {
      "id": "string",
      "username": "string",
      "email": "string",
      "createdAt": "datetime"
    }
  ],
  "total": number,
  "limit": number,
  "offset": number
}
```

### 2. Create Review Request
```
POST /api/review-requests
Authorization: Bearer <patient-token>
Content-Type: application/json

Body:
{
  "predictionId": "24-char-hex-string",
  "dermatologistId": "24-char-hex-string"
}

Response: 201 Created
{
  "id": "string",
  "predictionId": "string",
  "patientId": "string",
  "dermatologistId": "string",
  "status": "pending",
  "comment": null,
  "createdAt": "datetime",
  "reviewedAt": null,
  "patientUsername": "string",
  "dermatologistUsername": "string"
}

Errors:
- 400: Invalid input or selected user is not a dermatologist
- 403: Not a patient or not prediction owner
- 404: Prediction or dermatologist not found
- 409: Duplicate request (same prediction + dermatologist)
```

### 3. List Review Requests
```
GET /api/review-requests
Authorization: Bearer <token>
Query Parameters:
  - status: (optional) Filter by "pending" or "reviewed"
  - limit: (optional, default 50) Max results
  - offset: (optional, default 0) Pagination offset

Response: 200 OK
{
  "requests": [
    {
      "id": "string",
      "predictionId": "string",
      "patientId": "string",
      "dermatologistId": "string",
      "status": "pending|reviewed",
      "comment": "string|null",
      "createdAt": "datetime",
      "reviewedAt": "datetime|null",
      "patientUsername": "string",
      "dermatologistUsername": "string"
    }
  ],
  "total": number,
  "limit": number,
  "offset": number
}

Notes:
- Patients see requests they created
- Dermatologists see requests assigned to them
```

### 4. Get Review Request Details
```
GET /api/review-requests/{id}
Authorization: Bearer <token>

Response: 200 OK
{
  "id": "string",
  "predictionId": "string",
  "patientId": "string",
  "dermatologistId": "string",
  "status": "pending|reviewed",
  "comment": "string|null",
  "createdAt": "datetime",
  "reviewedAt": "datetime|null",
  "patientUsername": "string",
  "dermatologistUsername": "string"
}

Errors:
- 400: Invalid request ID
- 403: Not authorized (must be patient owner or assigned dermatologist)
- 404: Request not found
```

### 5. Submit Review
```
POST /api/review-requests/{id}/review
Authorization: Bearer <dermatologist-token>
Content-Type: application/json

Body:
{
  "comment": "string (1-2000 chars)"
}

Response: 200 OK
{
  "id": "string",
  "predictionId": "string",
  "patientId": "string",
  "dermatologistId": "string",
  "status": "reviewed",
  "comment": "string",
  "createdAt": "datetime",
  "reviewedAt": "datetime",
  "patientUsername": "string",
  "dermatologistUsername": "string"
}

Errors:
- 400: Already reviewed, not assigned, or validation error
- 403: Not a dermatologist or not assigned to this request
- 404: Request not found
```

### 6. List Notifications
```
GET /api/notifications
Authorization: Bearer <token>
Query Parameters:
  - unreadOnly: (optional, default false) Return only unread
  - limit: (optional, default 50) Max results
  - offset: (optional, default 0) Pagination offset

Response: 200 OK
{
  "notifications": [
    {
      "id": "string",
      "userId": "string",
      "type": "review_requested|review_submitted",
      "message": "string",
      "ref": {
        "requestId": "string",
        "predictionId": "string"
      },
      "isRead": boolean,
      "createdAt": "datetime"
    }
  ],
  "total": number,
  "unreadCount": number,
  "limit": number,
  "offset": number
}
```

### 7. Mark Notification as Read
```
PATCH /api/notifications/{id}/read
Authorization: Bearer <token>

Response: 204 No Content

Errors:
- 400: Invalid notification ID
- 404: Notification not found or not owned
```

## Complete Workflow Test

### Prerequisites
1. Server running on `http://localhost:5000`
2. API testing tool (Postman, Thunder Client, or curl)

### Step 1: Register Users

**Register Patient:**
```json
POST http://localhost:5000/api/auth/signup
Content-Type: application/json

{
  "username": "patient1",
  "email": "patient1@example.com",
  "password": "TestPass123",
  "role": "patient"
}
```

**Register Dermatologist:**
```json
POST http://localhost:5000/api/auth/signup
Content-Type: application/json

{
  "username": "dr_smith",
  "email": "dr.smith@example.com",
  "password": "TestPass123",
  "role": "dermatologist"
}
```

### Step 2: Login

**Patient Login:**
```json
POST http://localhost:5000/api/auth/login
Content-Type: application/json

{
  "emailOrUsername": "patient1@example.com",
  "password": "TestPass123",
  "role": "patient"
}

// Save the returned token as PATIENT_TOKEN
// Save the user.id as PATIENT_ID
```

**Dermatologist Login:**
```json
POST http://localhost:5000/api/auth/login
Content-Type: application/json

{
  "emailOrUsername": "dr.smith@example.com",
  "password": "TestPass123",
  "role": "dermatologist"
}

// Save the returned token as DERM_TOKEN
// Save the user.id as DERM_ID
```

### Step 3: Patient Lists Dermatologists

```
GET http://localhost:5000/api/users/dermatologists
Authorization: Bearer <PATIENT_TOKEN>

// Should return list including dr_smith
```

### Step 4: Patient Creates Prediction

```
POST http://localhost:5000/api/predictions/predict
Authorization: Bearer <PATIENT_TOKEN>
Content-Type: multipart/form-data

file: [select an image file]

// Save the returned prediction.id as PREDICTION_ID
```

### Step 5: Patient Creates Review Request

```json
POST http://localhost:5000/api/review-requests
Authorization: Bearer <PATIENT_TOKEN>
Content-Type: application/json

{
  "predictionId": "<PREDICTION_ID>",
  "dermatologistId": "<DERM_ID>"
}

// Save the returned request.id as REQUEST_ID
// Dermatologist receives email and in-app notification
```

### Step 6: Dermatologist Checks Notifications

```
GET http://localhost:5000/api/notifications
Authorization: Bearer <DERM_TOKEN>

// Should show "New review request from patient1"
```

### Step 7: Dermatologist Lists Pending Requests

```
GET http://localhost:5000/api/review-requests?status=pending
Authorization: Bearer <DERM_TOKEN>

// Should show the request created in Step 5
```

### Step 8: Dermatologist Views Request Details

```
GET http://localhost:5000/api/review-requests/<REQUEST_ID>
Authorization: Bearer <DERM_TOKEN>

// Should show full request details including prediction info
```

### Step 9: Dermatologist Submits Review

```json
POST http://localhost:5000/api/review-requests/<REQUEST_ID>/review
Authorization: Bearer <DERM_TOKEN>
Content-Type: application/json

{
  "comment": "Based on the analysis, this appears to be a mild case. I recommend using a gentle moisturizer and avoiding direct sunlight. If symptoms persist, please schedule a follow-up consultation."
}

// Status changes to "reviewed"
// Patient receives email and in-app notification
```

### Step 10: Patient Checks Notifications

```
GET http://localhost:5000/api/notifications
Authorization: Bearer <PATIENT_TOKEN>

// Should show "Dr. dr_smith added a review to your prediction"
```

### Step 11: Patient Views Reviewed Request

```
GET http://localhost:5000/api/review-requests/<REQUEST_ID>
Authorization: Bearer <PATIENT_TOKEN>

// Should show status: "reviewed" with the dermatologist's comment
```

### Step 12: Patient Lists Their Requests

```
GET http://localhost:5000/api/review-requests
Authorization: Bearer <PATIENT_TOKEN>

// Should show all requests created by the patient
```

## RBAC Validation Tests

### Test 1: Patient Cannot Submit Review
```
POST http://localhost:5000/api/review-requests/<REQUEST_ID>/review
Authorization: Bearer <PATIENT_TOKEN>

Expected: 403 Forbidden
```

### Test 2: Non-Owner Cannot View Request
Create a third user and try to access a request they're not involved in:
```
GET http://localhost:5000/api/review-requests/<REQUEST_ID>
Authorization: Bearer <OTHER_USER_TOKEN>

Expected: 403 Forbidden
```

### Test 3: Duplicate Request Prevention
Try to create the same request twice:
```json
POST http://localhost:5000/api/review-requests
Authorization: Bearer <PATIENT_TOKEN>

{
  "predictionId": "<SAME_PREDICTION_ID>",
  "dermatologistId": "<SAME_DERM_ID>"
}

Expected: 409 Conflict
```

### Test 4: Patient Cannot Request Review for Others' Predictions
```json
POST http://localhost:5000/api/review-requests
Authorization: Bearer <PATIENT_TOKEN>

{
  "predictionId": "<ANOTHER_PATIENT_PREDICTION_ID>",
  "dermatologistId": "<DERM_ID>"
}

Expected: 403 Forbidden
```

## Database Collections

### review_requests
- Fields: `_id`, `predictionId`, `patientId`, `dermatologistId`, `status`, `comment`, `createdAt`, `reviewedAt`
- Indexes:
  - Unique: `{predictionId: 1, dermatologistId: 1}`
  - `{dermatologistId: 1, status: 1, createdAt: -1}`
  - `{patientId: 1, status: 1, createdAt: -1}`
  - `{predictionId: 1}`

### notifications
- Fields: `_id`, `userId`, `type`, `message`, `ref`, `isRead`, `createdAt`
- Indexes:
  - `{userId: 1, isRead: 1, createdAt: -1}`

## Email Notifications

### Review Request Email (to Dermatologist)
- Subject: "New Review Request - FacialDerma AI"
- Content: Patient name, prediction ID, call to action

### Review Submitted Email (to Patient)
- Subject: "Expert Review Added - FacialDerma AI"
- Content: Dermatologist name, prediction ID, call to view review

## Swagger UI

Access interactive API documentation at:
```
http://localhost:5000/docs
```

Try out all endpoints directly from the browser with the built-in testing interface.

## Success Criteria

✓ Patients can list dermatologists
✓ Patients can request reviews on their predictions
✓ Duplicate requests are prevented
✓ Dermatologists receive notifications (in-app + email)
✓ Dermatologists can view and filter pending/reviewed requests
✓ Dermatologists can submit one review per request
✓ Patients receive notifications when review is submitted (in-app + email)
✓ Role-based access control enforced throughout
✓ Database indexes created for optimal performance
✓ Existing auth and prediction endpoints remain unchanged

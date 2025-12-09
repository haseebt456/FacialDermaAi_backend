# Admin API Documentation - Complete Testing Guide

## Overview

This document provides a comprehensive guide for testing the FacialDerma AI admin verification system. The system allows administrators to manage dermatologist verifications, user accounts, and monitor platform statistics.

## System Architecture

### Database Collections
- `users` - User accounts (patients, dermatologists, admins)
- `dermatologist_verifications` - Verification requests for dermatologists
- `predictions` - Skin analysis predictions
- `review_requests` - Dermatologist review requests

### User Roles
- **Admin**: Full access to admin panel and user management
- **Dermatologist**: Can access dermatologist features (pending/approved/rejected states)
- **Patient**: Standard user with analysis capabilities

## API Endpoints

### Authentication Required
All admin endpoints require:
- Bearer token in Authorization header
- User must have `role: "admin"`

### 1. Dashboard Statistics
**GET** `/api/admin/dashboard/stats`

Returns platform statistics for admin dashboard.

**Response:**
```json
{
  "totalUsers": 150,
  "totalPatients": 120,
  "totalDermatologists": 25,
  "pendingVerifications": 5,
  "totalPredictions": 450,
  "totalReviewRequests": 89
}
```

### 2. Dermatologist Verifications

#### Get Pending Verifications
**GET** `/api/admin/dermatologists/pending`

Returns list of dermatologists awaiting verification.

**Response:**
```json
[
  {
    "id": "verification_id",
    "dermatologistId": "user_id",
    "documentUrl": null,
    "status": "pending",
    "submittedAt": "2025-12-09T10:00:00Z",
    "name": "Dr. John Smith",
    "email": "john@example.com",
    "username": "johnsmith",
    "license": "MED123456",
    "specialization": "Dermatology",
    "clinic": "City Hospital",
    "experience": 10,
    "bio": "Experienced dermatologist",
    "reviewComments": null,
    "createdAt": "2025-12-09T10:00:00Z"
  }
]
```

#### Get Rejected Verifications
**GET** `/api/admin/dermatologists/rejected`

Returns list of dermatologists whose verification was rejected.

#### Verify Dermatologist
**POST** `/api/admin/dermatologists/{dermatologist_id}/verify`

Approve or reject a dermatologist verification.

**Request Body:**
```json
{
  "status": "approved", // or "rejected"
  "reviewComments": "Optional review comments"
}
```

**Response:**
```json
{
  "message": "Dermatologist verification updated successfully",
  "verification": {
    "id": "verification_id",
    "status": "approved",
    "reviewComments": "Approved after document verification"
  }
}
```

### 3. User Management

#### Get All Users
**GET** `/api/admin/users?skip=0&limit=50&role=patient`

Returns paginated list of users with optional filtering.

**Query Parameters:**
- `skip`: Number of users to skip (default: 0)
- `limit`: Maximum users to return (default: 50)
- `role`: Filter by role ("patient", "dermatologist", "admin")

**Response:**
```json
[
  {
    "id": "user_id",
    "username": "johndoe",
    "email": "john@example.com",
    "role": "patient",
    "isSuspended": false,
    "name": "John Doe",
    "createdAt": "2025-12-01T08:00:00Z"
  }
]
```

#### Suspend User
**POST** `/api/admin/users/{user_id}/suspend`

Suspends a user account.

#### Unsuspend User
**POST** `/api/admin/users/{user_id}/unsuspend`

Removes suspension from a user account.

#### Delete User
**DELETE** `/api/admin/users/{user_id}`

Permanently deletes a user account and all associated data.

## Complete Testing Process

### Prerequisites
1. Backend server running on `http://localhost:5000`
2. Frontend running on `http://localhost:3000`
3. MongoDB database connected
4. Admin user account created

### Step 1: Create Test Accounts

#### Create Admin Account
```bash
# Use the init_admin_system.py script or manually create in MongoDB
python init_admin_system.py
```

#### Create Test Dermatologist Accounts
Use the signup API to create dermatologist accounts:

```bash
curl -X POST http://localhost:5000/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "role": "dermatologist",
    "name": "Dr. Test User",
    "username": "testderm",
    "email": "test@example.com",
    "password": "TestPass123!",
    "license": "TEST123456"
  }'
```

**Expected Response:**
```json
{
  "message": "Registration successful! Please verify your email. Your dermatologist account will be activated after admin approval."
}
```

#### Create Test Patient Accounts
```bash
curl -X POST http://localhost:5000/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "role": "patient",
    "name": "Test Patient",
    "username": "testpatient",
    "email": "patient@example.com",
    "password": "TestPass123!"
  }'
```

### Step 2: Verify Email (Required for Login)

#### Check Email Verification
After signup, check the email verification token in the database or use the verification link sent to email.

```bash
# Find verification token in database
# Then verify email:
curl "http://localhost:5000/api/auth/verify-email?token=YOUR_TOKEN_HERE"
```

### Step 3: Admin Login and Testing

#### Admin Login
```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@facialderma.com",
    "password": "AdminPass123!"
  }'
```

**Expected Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "user": {
    "id": "admin_id",
    "username": "admin",
    "email": "admin@facialderma.com",
    "role": "admin"
  }
}
```

#### Get Dashboard Statistics
```bash
curl -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  http://localhost:5000/api/admin/dashboard/stats
```

#### Check Pending Verifications
```bash
curl -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  http://localhost:5000/api/admin/dermatologists/pending
```

You should see the test dermatologist created in Step 1.

### Step 4: Test Dermatologist Verification

#### Approve a Dermatologist
```bash
curl -X POST \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "approved",
    "reviewComments": "License verified, credentials approved"
  }' \
  http://localhost:5000/api/admin/dermatologists/TEST_DERMATOLOGIST_ID/verify
```

#### Reject a Dermatologist
```bash
curl -X POST \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "rejected",
    "reviewComments": "License number already exists"
  }' \
  http://localhost:5000/api/admin/dermatologists/TEST_DERMATOLOGIST_ID/verify
```

### Step 5: Test User Management

#### Get All Users
```bash
curl -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  "http://localhost:5000/api/admin/users?limit=10"
```

#### Suspend a User
```bash
curl -X POST \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  http://localhost:5000/api/admin/users/USER_ID/suspend
```

#### Unsuspend a User
```bash
curl -X POST \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  http://localhost:5000/api/admin/users/USER_ID/unsuspend
```

#### Delete a User
```bash
curl -X DELETE \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  http://localhost:5000/api/admin/users/USER_ID
```

### Step 6: Frontend Testing

#### Admin Panel Testing
1. Login as admin at `http://localhost:3000/Login`
2. Navigate to `/Admin`
3. Verify dashboard shows correct statistics
4. Check "Pending Verifications" tab shows dermatologists awaiting approval
5. Test approve/reject actions
6. Check "Rejected Verifications" tab after rejecting dermatologists
7. Test user management in "Users" tab

#### Dermatologist Login Testing

##### Pending Dermatologist
1. Login as pending dermatologist
2. Should see yellow warning modal: "Verification Pending"
3. Can dismiss modal and access basic features
4. Cannot access dermatologist-specific pages until approved

##### Approved Dermatologist
1. Login as approved dermatologist
2. No modal appears
3. Can access all dermatologist features (`/Dermatologist`, `/DProfile`)

##### Rejected Dermatologist
1. Login as rejected dermatologist
2. Should see red blocking screen: "Verification Rejected"
3. Cannot access dermatologist features
4. Can go to profile or logout

### Step 7: Database Verification

#### Check Verification Records
```javascript
// In MongoDB shell
use facialderma_ai
db.dermatologist_verifications.find({})
```

#### Check User Records
```javascript
db.users.find({role: "dermatologist"})
```

#### Verify Status Updates
After approval/rejection, check that:
- `dermatologist_verifications` collection has updated status
- User profile includes `verificationStatus` field

### Step 8: Error Testing

#### Test Invalid License Numbers
1. Try registering two dermatologists with same license
2. Second registration should fail with 400 error

#### Test Unauthorized Access
```bash
# Try admin endpoints without token
curl http://localhost:5000/api/admin/dashboard/stats
# Should return 401 Unauthorized

# Try admin endpoints with non-admin token
curl -H "Authorization: Bearer PATIENT_TOKEN" \
  http://localhost:5000/api/admin/dashboard/stats
# Should return 403 Forbidden
```

#### Test Invalid Verification Status
```bash
curl -X POST \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status": "invalid_status"}' \
  http://localhost:5000/api/admin/dermatologists/ID/verify
# Should return 400 Bad Request
```

### Step 9: Integration Testing

#### Complete User Journey
1. Patient registers and logs in
2. Patient uploads image and gets prediction
3. Patient requests dermatologist review
4. Dermatologist (if approved) receives notification
5. Dermatologist reviews and responds
6. Admin monitors all activities via dashboard

#### Verification Workflow
1. Dermatologist registers with unique license
2. Email verification required
3. Admin reviews pending verifications
4. Admin approves/rejects with comments
5. Dermatologist sees status on login
6. Approved dermatologists can access full features

## Troubleshooting

### Common Issues

#### 1. "uvicorn not recognized"
```bash
# Activate virtual environment
cd FacialDermaAi_backend
.\venv\Scripts\Activate.ps1
# Then run server
uvicorn app.main:app --host 0.0.0.0 --port 5000 --reload
```

#### 2. Database Connection Issues
- Check MongoDB is running
- Verify MONGO_URI in .env file
- Check database name in settings

#### 3. Admin Account Not Found
```bash
# Run admin initialization
python init_admin_system.py
```

#### 4. Verification Status Not Updating
- Check dermatologist_verifications collection
- Ensure verification record exists for the user
- Verify API response for verification update

#### 5. Frontend Not Showing Modals
- Check user object has verificationStatus field
- Verify VerificationCheck component is properly imported
- Check browser console for errors

### Debug Commands

#### Check User Verification Status
```bash
curl -H "Authorization: Bearer DERMATOLOGIST_TOKEN" \
  http://localhost:5000/api/users/me
```

#### Check All Verifications
```bash
curl -H "Authorization: Bearer ADMIN_TOKEN" \
  http://localhost:5000/api/admin/dermatologists/pending
```

#### Database Queries
```javascript
// Find all dermatologists
db.users.find({role: "dermatologist"})

// Find pending verifications
db.dermatologist_verifications.find({status: "pending"})

// Find user by email
db.users.findOne({email: "test@example.com"})
```

## API Response Codes

- `200`: Success
- `201`: Created
- `400`: Bad Request (validation errors)
- `401`: Unauthorized (invalid/missing token)
- `403`: Forbidden (insufficient permissions)
- `404`: Not Found
- `422`: Unprocessable Entity (validation errors)
- `500`: Internal Server Error

## Security Notes

- All admin endpoints require authentication
- Admin role verification on each request
- Password hashing for all user accounts
- JWT tokens with expiration
- Input validation on all endpoints
- License number uniqueness validation
- SQL injection protection via parameterized queries

## Performance Considerations

- Pagination on user lists (default 50 items)
- Database indexes on frequently queried fields
- Efficient MongoDB aggregation for statistics
- Background email sending for notifications

---

**Last Updated:** December 9, 2025
**Version:** 1.0
**API Version:** v1</content>
<parameter name="filePath">d:\FYP\FacialDermaAi_backend\ADMIN_API.md
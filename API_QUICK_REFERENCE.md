# Email Verification - Quick API Reference

## Base URL
```
http://localhost:5000/api/auth
```

---

## 1. Register User (New - With Email Verification)

### Endpoint
```http
POST /register
Content-Type: application/json
```

### Request
```json
{
    "role": "patient",
    "name": "John Doe",
    "username": "johndoe",
    "email": "john@example.com",
    "password": "securepass123"
}
```

### Response (201)
```json
{
    "message": "Registration successful! Please check your email to verify your account."
}
```

### Errors
- **400** - Email already registered
- **400** - Username already taken
- **400** - Validation error

---

## 2. Verify Email

### Endpoint
```http
GET /verify-email?token={verification_token}
```

### Query Parameters
- `token` (required) - Token from verification email

### Response (200)
```json
{
    "message": "Email verified successfully! You can now log in to your account."
}
```

### Errors
- **400** - Token missing
- **404** - Invalid token
- **400** - Token expired
- **400** - Already verified

---

## 3. Login (Updated - Checks Verification)

### Endpoint
```http
POST /login
Content-Type: application/json
```

### Request
```json
{
    "emailOrUsername": "john@example.com",
    "password": "securepass123",
    "role": "patient"
}
```

### Response (200)
```json
{
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "user": {
        "id": "507f1f77bcf86cd799439011",
        "username": "johndoe",
        "email": "john@example.com",
        "role": "patient",
        "name": "John Doe"
    }
}
```

### Errors
- **401** - User not found
- **401** - Invalid password
- **403** - Role mismatch
- **403** - Email not verified ⬅️ NEW

---

## 4. Signup (Old - No Verification Required)

### Endpoint
```http
POST /signup
Content-Type: application/json
```

### Request
```json
{
    "role": "patient",
    "name": "Jane Doe",
    "username": "janedoe",
    "email": "jane@example.com",
    "password": "securepass123"
}
```

### Response (201)
```json
{
    "message": "User registered successfully"
}
```

**Note:** Users registered via `/signup` can login immediately without email verification. Use `/register` for new registrations with email verification.

---

## Testing with cURL

### Register
```bash
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "role": "patient",
    "username": "testuser",
    "email": "test@example.com",
    "password": "testpass123"
  }'
```

### Verify Email
```bash
curl -X GET "http://localhost:5000/api/auth/verify-email?token=YOUR_TOKEN_HERE"
```

### Login
```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "emailOrUsername": "test@example.com",
    "password": "testpass123",
    "role": "patient"
  }'
```

---

## Frontend Routes Needed

1. **Registration Page** - `/signup`
   - Form to collect user data
   - POST to `/api/auth/signup`
   - Show success message about checking email

2. **Email Verification Page** - `/verify`
   - Reads `?token=xxx` from URL
   - GET to `/api/auth/verify-email?token=xxx`
   - Shows success/error message
   - Redirects to login on success

3. **Login Page** - `/login`
   - Form for email/username + password
   - POST to `/api/auth/login`
   - Handle "Email not verified" error
   - Show message to check email

---

## Email Flow

1. User fills registration form → `/register`
2. Backend creates user with `is_verified: false`
3. Backend sends email with link: `http://frontend.com/verify?token=xxx`
4. User clicks link in email
5. Frontend loads `/verify` page, extracts token
6. Frontend calls `/verify-email?token=xxx`
7. Backend verifies token, marks user as verified
8. User redirected to login
9. User can now log in successfully

---

## Database Fields

### Before Verification
```json
{
    "_id": "...",
    "username": "johndoe",
    "email": "john@example.com",
    "is_verified": false,
    "verification_token": "abc123...",
    "token_expiry": "2025-12-02T10:30:00Z",
    ...
}
```

### After Verification
```json
{
    "_id": "...",
    "username": "johndoe",
    "email": "john@example.com",
    "is_verified": true,
    // verification_token removed
    // token_expiry removed
    ...
}
```

---

## Configuration

### Required Environment Variables
```env
EMAIL_USER=your-email@gmail.com
EMAIL_PASS=your-gmail-app-password
FRONTEND_URL=http://localhost:3000
VERIFICATION_TOKEN_EXPIRY_MINUTES=15
```

---

## Common Status Codes

- **200** - Success
- **201** - Created (registration successful)
- **400** - Bad Request (validation error, expired token, etc.)
- **401** - Unauthorized (wrong password)
- **403** - Forbidden (email not verified, role mismatch)
- **404** - Not Found (invalid token, user not found)
- **500** - Internal Server Error

---

## Error Response Format

All errors follow this structure:
```json
{
    "detail": {
        "error": "Human-readable error message"
    }
}
```

Examples:
```json
{
    "detail": {
        "error": "Email not verified. Please check your inbox and verify your email address."
    }
}
```

```json
{
    "detail": {
        "error": "Verification link has expired. Please request a new verification email."
    }
}
```

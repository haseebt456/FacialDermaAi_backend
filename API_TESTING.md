# FacialDerma AI Backend - API Testing Examples

This file contains ready-to-use curl commands for testing all API endpoints.

## Setup

First, set your base URL and save your token:
```powershell
$BASE_URL = "http://localhost:5000"
$TOKEN = "your-jwt-token-here"  # Update after login
```

## 1. Health Check

```powershell
curl -X GET http://localhost:5000/
```

Expected: `FacialDerma AI Backend Running!`

## 2. User Signup

```powershell
curl -X POST http://localhost:5000/api/auth/signup `
  -H "Content-Type: application/json" `
  -d '{
    "role": "patient",
    "username": "johndoe",
    "email": "john@example.com",
    "password": "securepass123"
  }'
```

Expected: `{"message":"User registered successfully"}`

### Test Validation Errors:

**Duplicate username:**
```powershell
curl -X POST http://localhost:5000/api/auth/signup `
  -H "Content-Type: application/json" `
  -d '{
    "role": "patient",
    "username": "johndoe",
    "email": "different@example.com",
    "password": "pass123"
  }'
```

**Username with spaces (should fail):**
```powershell
curl -X POST http://localhost:5000/api/auth/signup `
  -H "Content-Type: application/json" `
  -d '{
    "role": "patient",
    "username": "john doe",
    "email": "john2@example.com",
    "password": "pass123"
  }'
```

## 3. User Login

```powershell
curl -X POST http://localhost:5000/api/auth/login `
  -H "Content-Type: application/json" `
  -d '{
    "emailOrUsername": "johndoe",
    "password": "securepass123",
    "role": "patient"
  }'
```

**Save the token from response!**

### Test Login Errors:

**Wrong password:**
```powershell
curl -X POST http://localhost:5000/api/auth/login `
  -H "Content-Type: application/json" `
  -d '{
    "emailOrUsername": "johndoe",
    "password": "wrongpassword",
    "role": "patient"
  }'
```

**Role mismatch:**
```powershell
curl -X POST http://localhost:5000/api/auth/login `
  -H "Content-Type: application/json" `
  -d '{
    "emailOrUsername": "johndoe",
    "password": "securepass123",
    "role": "dermatologist"
  }'
```

Expected: `{"error":"Role mismatch. You are registered as a patient."}`

## 4. Get Current User

**Replace YOUR_TOKEN_HERE with actual token from login:**

```powershell
curl -X GET http://localhost:5000/api/users/me `
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### Test Auth Errors:

**No token:**
```powershell
curl -X GET http://localhost:5000/api/users/me
```

Expected: `{"error":"No token, authorization denied"}`

**Invalid token:**
```powershell
curl -X GET http://localhost:5000/api/users/me `
  -H "Authorization: Bearer invalid.token.here"
```

Expected: `{"error":"Token is not valid"}`

## 5. Upload Image for Prediction

**Replace YOUR_TOKEN_HERE and path/to/image.jpg:**

```powershell
curl -X POST http://localhost:5000/api/predictions/predict `
  -H "Authorization: Bearer YOUR_TOKEN_HERE" `
  -F "image=@C:\path\to\your\face-image.jpg"
```

Expected:
```json
{
  "predicted_label": "Acne",
  "confidence_score": 0.945,
  "image_url": "http://localhost:5000/uploads/face-image.jpg"
}
```

### Test Validation Errors:

**Blurry image:**
Should return: `{"error":"Image is blury.Please try again with a clear picture"}`

**No face in image:**
Should return: `{"error":"No face detected in the image"}`

## 6. Get Predictions History

```powershell
curl -X GET http://localhost:5000/api/predictions `
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

Expected: Array of prediction objects

## 7. Access Uploaded Image

```powershell
curl -X GET http://localhost:5000/uploads/face-image.jpg
```

Or open in browser: `http://localhost:5000/uploads/face-image.jpg`

## Complete Test Flow

```powershell
# 1. Signup
$signup = curl -X POST http://localhost:5000/api/auth/signup `
  -H "Content-Type: application/json" `
  -d '{\"role\":\"patient\",\"username\":\"testuser\",\"email\":\"test@example.com\",\"password\":\"test123\"}' | ConvertFrom-Json

# 2. Login
$login = curl -X POST http://localhost:5000/api/auth/login `
  -H "Content-Type: application/json" `
  -d '{\"emailOrUsername\":\"testuser\",\"password\":\"test123\",\"role\":\"patient\"}' | ConvertFrom-Json

# Extract token
$TOKEN = $login.token

# 3. Get user info
curl -X GET http://localhost:5000/api/users/me `
  -H "Authorization: Bearer $TOKEN"

# 4. Upload image (replace with actual path)
curl -X POST http://localhost:5000/api/predictions/predict `
  -H "Authorization: Bearer $TOKEN" `
  -F "image=@C:\path\to\face.jpg"

# 5. Get predictions
curl -X GET http://localhost:5000/api/predictions `
  -H "Authorization: Bearer $TOKEN"
```

## Using PowerShell Invoke-RestMethod

Alternative to curl (more PowerShell-native):

```powershell
# Signup
$signupBody = @{
    role = "patient"
    username = "testuser2"
    email = "test2@example.com"
    password = "test123"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:5000/api/auth/signup" `
    -Method Post `
    -ContentType "application/json" `
    -Body $signupBody

# Login
$loginBody = @{
    emailOrUsername = "testuser2"
    password = "test123"
    role = "patient"
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri "http://localhost:5000/api/auth/login" `
    -Method Post `
    -ContentType "application/json" `
    -Body $loginBody

$token = $response.token

# Get user
$headers = @{
    Authorization = "Bearer $token"
}

Invoke-RestMethod -Uri "http://localhost:5000/api/users/me" `
    -Method Get `
    -Headers $headers

# Upload image
$headers = @{
    Authorization = "Bearer $token"
}

$filePath = "C:\path\to\image.jpg"
$form = @{
    image = Get-Item -Path $filePath
}

Invoke-RestMethod -Uri "http://localhost:5000/api/predictions/predict" `
    -Method Post `
    -Headers $headers `
    -Form $form
```

## Notes

- All timestamps are in ISO 8601 format (UTC)
- Predictions are sorted by `createdAt` descending (newest first)
- Email notifications are sent asynchronously (won't block API responses)
- JWT tokens expire after 1 day (configurable in .env)
- Image files must contain a clear, visible face
- Supported image formats: jpg, jpeg, png

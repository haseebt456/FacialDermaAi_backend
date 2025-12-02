# Email Verification Implementation Guide

## Overview
This guide explains the complete email verification system implemented in the FacialDerma AI backend.

## Features Implemented

### 1. **User Registration with Email Verification** (`POST /api/auth/register`)
- Creates user account with `is_verified = False`
- Generates secure 32-byte verification token using `secrets.token_urlsafe(32)`
- Token expires in 15 minutes (configurable via `VERIFICATION_TOKEN_EXPIRY_MINUTES`)
- Sends verification email with clickable link
- Token is stored securely in database with expiry timestamp

### 2. **Email Verification** (`GET /api/auth/verify-email?token=xxx`)
- Validates the verification token
- Checks if token has expired
- Checks if email is already verified
- Marks user as verified and removes token (single-use)
- Returns appropriate success or error messages

### 3. **Login Protection** (`POST /api/auth/login`)
- Blocks login attempts from unverified users
- Returns clear error message: "Email not verified. Please check your inbox."
- Only applies to users registered via `/register` endpoint

### 4. **Backward Compatibility**
- Old `/signup` endpoint remains unchanged for existing users
- Users registered via `/signup` can log in immediately (no verification required)
- New users should use `/register` for email verification

---

## Configuration

### Environment Variables (`.env`)

```env
# Email Configuration
EMAIL_USER=your-email@gmail.com
EMAIL_PASS=your-app-password
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587

# Frontend URL for verification links
FRONTEND_URL=http://localhost:3000

# Token expiry (minutes)
VERIFICATION_TOKEN_EXPIRY_MINUTES=15
```

### Config File (`app/config.py`)

```python
class Settings(BaseSettings):
    FRONTEND_URL: str = "http://localhost:3000"
    VERIFICATION_TOKEN_EXPIRY_MINUTES: int = 15
```

---

## Database Schema Changes

### User Document Structure

```python
{
    "_id": ObjectId("..."),
    "role": "patient",
    "username": "johndoe",
    "email": "john@example.com",
    "emailLower": "john@example.com",
    "password": "hashed_password",
    "name": "John Doe",  # Optional
    "createdAt": datetime,
    
    # New verification fields
    "is_verified": False,  # Boolean flag
    "verification_token": "secure_random_token_32_bytes",  # Deleted after verification
    "token_expiry": datetime,  # Deleted after verification
}
```

**Note:** After successful verification:
- `is_verified` is set to `True`
- `verification_token` field is removed
- `token_expiry` field is removed

---

## API Endpoints

### 1. Register User (New Endpoint)

**Endpoint:** `POST /api/auth/register`

**Request Body:**
```json
{
    "role": "patient",
    "name": "John Doe",
    "username": "johndoe",
    "email": "john@example.com",
    "password": "securepass123"
}
```

**Success Response (201):**
```json
{
    "message": "Registration successful! Please check your email to verify your account."
}
```

**Error Responses:**
```json
// 400 - Email exists
{
    "detail": {
        "error": "Email already registered"
    }
}

// 400 - Username exists
{
    "detail": {
        "error": "Username already taken"
    }
}
```

---

### 2. Verify Email

**Endpoint:** `GET /api/auth/verify-email?token={token}`

**Query Parameters:**
- `token` (required): Verification token from email link

**Success Response (200):**
```json
{
    "message": "Email verified successfully! You can now log in to your account."
}
```

**Error Responses:**
```json
// 400 - Missing token
{
    "detail": {
        "error": "Verification token is required"
    }
}

// 404 - Invalid token
{
    "detail": {
        "error": "Invalid verification token"
    }
}

// 400 - Expired token
{
    "detail": {
        "error": "Verification link has expired. Please request a new verification email."
    }
}

// 400 - Already verified
{
    "detail": {
        "error": "Email is already verified. You can now log in."
    }
}
```

---

### 3. Login (Updated)

**Endpoint:** `POST /api/auth/login`

**Request Body:**
```json
{
    "emailOrUsername": "john@example.com",
    "password": "securepass123",
    "role": "patient"
}
```

**Success Response (200):**
```json
{
    "token": "jwt_token_here",
    "user": {
        "id": "user_id",
        "username": "johndoe",
        "email": "john@example.com",
        "role": "patient",
        "name": "John Doe"
    }
}
```

**Error Response - Unverified Email (403):**
```json
{
    "detail": {
        "error": "Email not verified. Please check your inbox and verify your email address."
    }
}
```

---

## Email Template

### Verification Email

**Subject:** "Verify Your Email - FacialDerma AI"

**Body:**
```html
<html>
    <body>
        <h2>Welcome to FacialDerma AI, {username}!</h2>
        <p>Thank you for registering. Please verify your email address to activate your account.</p>
        <br>
        <p><strong>Click the link below to verify your email:</strong></p>
        <p>
            <a href="{verification_link}" 
               style="display: inline-block; padding: 10px 20px; background-color: #4CAF50; 
                      color: white; text-decoration: none; border-radius: 5px;">
                Verify Email
            </a>
        </p>
        <br>
        <p>Or copy and paste this link into your browser:</p>
        <p style="word-break: break-all; color: #666;">{verification_link}</p>
        <br>
        <p><small>This link will expire in 15 minutes.</small></p>
        <br>
        <p>If you didn't create an account, please ignore this email.</p>
        <br>
        <p>Best regards,<br>The FacialDerma AI Team</p>
    </body>
</html>
```

**Verification Link Format:**
```
http://localhost:3000/verify?token=abc123xyz789...
```

---

## Frontend Integration

### React Component Example

```javascript
// VerifyEmail.jsx
import { useEffect, useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import axios from 'axios';

export default function VerifyEmail() {
    const [searchParams] = useSearchParams();
    const navigate = useNavigate();
    const [status, setStatus] = useState('verifying'); // verifying, success, error
    const [message, setMessage] = useState('');

    useEffect(() => {
        const token = searchParams.get('token');
        
        if (!token) {
            setStatus('error');
            setMessage('Invalid verification link');
            return;
        }

        const verifyEmail = async () => {
            try {
                const response = await axios.get(
                    `http://localhost:5000/api/auth/verify-email?token=${token}`
                );
                
                setStatus('success');
                setMessage(response.data.message);
                
                // Redirect to login after 3 seconds
                setTimeout(() => {
                    navigate('/login');
                }, 3000);
                
            } catch (error) {
                setStatus('error');
                setMessage(
                    error.response?.data?.detail?.error || 
                    'Email verification failed'
                );
            }
        };

        verifyEmail();
    }, [searchParams, navigate]);

    return (
        <div className="verify-container">
            {status === 'verifying' && (
                <div>
                    <h2>Verifying your email...</h2>
                    <p>Please wait</p>
                </div>
            )}
            
            {status === 'success' && (
                <div className="success">
                    <h2>✓ Email Verified!</h2>
                    <p>{message}</p>
                    <p>Redirecting to login...</p>
                </div>
            )}
            
            {status === 'error' && (
                <div className="error">
                    <h2>✗ Verification Failed</h2>
                    <p>{message}</p>
                    <button onClick={() => navigate('/login')}>
                        Go to Login
                    </button>
                </div>
            )}
        </div>
    );
}
```

### Registration Form Example

```javascript
// Register.jsx
import { useState } from 'react';
import axios from 'axios';

export default function Register() {
    const [formData, setFormData] = useState({
        role: 'patient',
        name: '',
        username: '',
        email: '',
        password: ''
    });
    const [message, setMessage] = useState('');
    const [error, setError] = useState('');

    const handleSubmit = async (e) => {
        e.preventDefault();
        setMessage('');
        setError('');

        try {
            const response = await axios.post(
                'http://localhost:5000/api/auth/register',
                formData
            );
            
            setMessage(response.data.message);
            // Show success message and instructions to check email
            
        } catch (err) {
            setError(
                err.response?.data?.detail?.error || 
                'Registration failed'
            );
        }
    };

    return (
        <form onSubmit={handleSubmit}>
            {/* Form fields */}
            
            {message && (
                <div className="success-message">
                    {message}
                </div>
            )}
            
            {error && (
                <div className="error-message">
                    {error}
                </div>
            )}
            
            <button type="submit">Register</button>
        </form>
    );
}
```

---

## Security Features

### 1. **Secure Token Generation**
```python
import secrets
verification_token = secrets.token_urlsafe(32)  # 256-bit entropy
```

### 2. **Token Expiry**
- Default: 15 minutes
- Prevents indefinite token validity
- Configurable via environment variable

### 3. **Single-Use Tokens**
- Token deleted after successful verification
- Cannot be reused even if intercepted

### 4. **Password Hashing**
```python
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
```

### 5. **Email Validation**
- Pydantic's `EmailStr` validator
- Lowercase storage for consistency

---

## Testing

### 1. Test Registration

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

**Expected:** Email sent with verification link

---

### 2. Test Email Verification

```bash
curl -X GET "http://localhost:5000/api/auth/verify-email?token=YOUR_TOKEN_HERE"
```

**Expected:** Success message, user marked as verified

---

### 3. Test Login Before Verification

```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "emailOrUsername": "test@example.com",
    "password": "testpass123",
    "role": "patient"
  }'
```

**Expected:** 403 error with message about unverified email

---

### 4. Test Login After Verification

Same as above, but **Expected:** Success with JWT token

---

## Error Handling

### Token Expiration
- Tokens expire after 15 minutes
- User sees: "Verification link has expired"
- **Solution:** Implement "Resend Verification Email" endpoint (optional enhancement)

### Invalid Token
- User sees: "Invalid verification token"
- Possible causes: Typo, manual manipulation, or deleted user

### Already Verified
- User sees: "Email is already verified"
- Safe to ignore, user can proceed to login

---

## Production Deployment Checklist

- [ ] Update `FRONTEND_URL` in production `.env`
- [ ] Configure proper SMTP credentials (Gmail App Password or SendGrid)
- [ ] Set appropriate `VERIFICATION_TOKEN_EXPIRY_MINUTES` (15-60 minutes)
- [ ] Ensure MongoDB indexes on `verification_token` and `emailLower`
- [ ] Test email delivery in production environment
- [ ] Monitor email bounce rates
- [ ] Implement "Resend Verification Email" feature (optional)
- [ ] Add email verification reminder on login page
- [ ] Set up email logging/tracking

---

## Optional Enhancements

### 1. Resend Verification Email
```python
@router.post("/resend-verification")
async def resend_verification(email: EmailStr):
    user = await get_user_by_email(email)
    if not user:
        raise HTTPException(404, "User not found")
    
    if user.get("is_verified"):
        raise HTTPException(400, "Email already verified")
    
    # Generate new token
    new_token = secrets.token_urlsafe(32)
    new_expiry = datetime.utcnow() + timedelta(minutes=15)
    
    await users.update_one(
        {"_id": user["_id"]},
        {"$set": {
            "verification_token": new_token,
            "token_expiry": new_expiry
        }}
    )
    
    await send_verification_email(email, user["username"], new_token)
    return {"message": "Verification email resent"}
```

### 2. Email Change Verification
- Require verification when user updates email
- Similar flow with different token type

### 3. Welcome Email After Verification
- Send congratulatory email after successful verification
- Include getting started guide

---

## Troubleshooting

### Email Not Received
1. Check spam/junk folder
2. Verify SMTP credentials in `.env`
3. Check `EMAIL_USER` and `EMAIL_PASS` are correct
4. Ensure Gmail "Less secure app access" is enabled OR use App Password
5. Check server logs for email sending errors

### Token Expired
- Implement "Resend Verification Email" feature
- Or increase `VERIFICATION_TOKEN_EXPIRY_MINUTES`

### Users Can't Verify
- Check `FRONTEND_URL` matches actual frontend domain
- Ensure `/verify` route exists in frontend
- Test verification link manually

---

## Support

For issues or questions:
- Check server logs: `tail -f logs/app.log`
- Review email sending logs
- Test SMTP connection manually
- Verify MongoDB user document structure

---

**Implementation Complete! ✓**

All features are production-ready with proper error handling, security measures, and structured responses.

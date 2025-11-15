# FacialDerma AI Backend

Production-ready FastAPI backend for facial dermatology AI diagnosis. This service consolidates authentication, user management, and ML-based skin condition predictions into a single, efficient Python application.

## Features

- **Authentication & Authorization**: JWT-based auth with bcrypt password hashing
- **User Management**: Role-based access (patient/dermatologist)
- **ML Predictions**: Integrated Keras/TensorFlow model for dermatological diagnosis
- **Image Validation**: Automatic blur and face detection
- **Email Notifications**: Async SMTP for signup and login alerts
- **MongoDB**: Async database operations with Motor
- **Static File Serving**: Direct image URL access

## Supported Conditions

The ML model can detect:
- Acne
- Melanoma
- Normal (healthy skin)
- Perioral Dermatitis
- Rosacea
- Warts

## Requirements

- Python 3.9+
- MongoDB (local or Atlas)
- Keras model file: `ResNet_Model.keras`
- Gmail account with App Password (for email notifications)

## Project Structure

```
FacialDermaAi_backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app entry point
│   ├── config.py            # Settings from environment
│   ├── auth/                # Authentication routes & services
│   │   ├── routes.py
│   │   ├── schemas.py
│   │   └── service.py
│   ├── users/               # User endpoints
│   │   ├── routes.py
│   │   └── schemas.py
│   ├── predictions/         # ML prediction endpoints
│   │   ├── routes.py
│   │   ├── schemas.py
│   │   └── repo.py
│   ├── ml/                  # ML inference pipeline
│   │   ├── model_loader.py
│   │   ├── preprocess.py
│   │   ├── inference.py
│   │   └── validators.py
│   ├── db/                  # Database connection
│   │   └── mongo.py
│   ├── email/               # Email service
│   │   └── mailer.py
│   ├── middleware/          # Request logging
│   │   └── logging.py
│   └── deps/                # Auth dependencies
│       └── auth.py
├── uploads/                 # Uploaded images
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## Quick Start

### 1. Clone and Setup

```powershell
cd E:\FYP\FacialDermaAi_backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and fill in your values:

```powershell
Copy-Item .env.example .env
```

Edit `.env`:

```env
PORT=5000
MONGO_URI=mongodb://localhost:27017/facialdermaai
JWT_SECRET=your-super-secret-jwt-key-change-this-in-production
EMAIL_USER=your-email@gmail.com
EMAIL_PASS=your-gmail-app-password
ORIGIN=http://localhost:3000
```

**Gmail Setup**: 
1. Enable 2FA on your Gmail account
2. Generate an App Password: https://myaccount.google.com/apppasswords
3. Use that 16-character password in `EMAIL_PASS`

### 3. Add ML Model

Place your trained Keras model file in the root directory:

```
ResNet_Model.keras
```

If the model file is not present, the application will start but predictions will fail.

### 4. Start MongoDB

Ensure MongoDB is running locally or use MongoDB Atlas.

**Local MongoDB (Windows)**:
```powershell
mongod
```

### 5. Run the Application

```powershell
uvicorn app.main:app --host 0.0.0.0 --port 5000 --reload
```

The server will start at: `http://localhost:5000`

Health check: `http://localhost:5000/` should return `"FacialDerma AI Backend Running!"`

## API Endpoints

### Health Check

**GET /** 
```
Returns: "FacialDerma AI Backend Running!"
```

### Authentication

#### Signup
**POST /api/auth/signup**

```json
{
  "role": "patient",
  "username": "johndoe",
  "email": "john@example.com",
  "password": "securepass123"
}
```

Response (201):
```json
{
  "message": "User registered successfully"
}
```

Errors:
- 400: `{ "error": "Email or username already exists" }`
- 400: `{ "error": "All fields are required" }`

#### Login
**POST /api/auth/login**

```json
{
  "emailOrUsername": "johndoe",
  "password": "securepass123",
  "role": "patient"
}
```

Response (200):
```json
{
  "token": "eyJhbGciOiJIUzI1NiIs...",
  "user": {
    "id": "507f1f77bcf86cd799439011",
    "username": "johndoe",
    "email": "john@example.com",
    "role": "patient"
  }
}
```

Errors:
- 401: `{ "error": "User Not Found" }`
- 401: `{ "error": "Invalid Password" }`
- 403: `{ "error": "Role mismatch. You are registered as a patient." }`

### Users

#### Get Current User
**GET /api/users/me**

Headers: `Authorization: Bearer <token>`

Response (200):
```json
{
  "id": "507f1f77bcf86cd799439011",
  "username": "johndoe",
  "email": "john@example.com",
  "role": "patient"
}
```

Errors:
- 401: `{ "error": "No token, authorization denied" }`
- 401: `{ "error": "Token is not valid" }`
- 404: `{ "error": "User not found" }`

### Predictions

#### Get User Predictions
**GET /api/predictions**

Headers: `Authorization: Bearer <token>`

Response (200):
```json
[
  {
    "id": "507f1f77bcf86cd799439012",
    "userId": "507f1f77bcf86cd799439011",
    "result": {
      "predicted_label": "Acne",
      "confidence_score": 0.945
    },
    "imageUrl": "http://localhost:5000/uploads/photo.jpg",
    "createdAt": "2025-11-15T10:30:00Z"
  }
]
```

#### Predict from Image
**POST /api/predictions/predict**

Headers: `Authorization: Bearer <token>`  
Content-Type: `multipart/form-data`

Form field: `image` (file)

Response (200):
```json
{
  "predicted_label": "Acne",
  "confidence_score": 0.945,
  "image_url": "http://localhost:5000/uploads/photo.jpg"
}
```

Errors:
- 400: `{ "error": "Image is blury.Please try again with a clear picture" }`
- 400: `{ "error": "No face detected in the image" }`

### Static Files

**GET /uploads/{filename}**

Returns the uploaded image file.

## Testing with cURL

### Signup
```powershell
curl -X POST http://localhost:5000/api/auth/signup `
  -H "Content-Type: application/json" `
  -d '{\"role\":\"patient\",\"username\":\"testuser\",\"email\":\"test@example.com\",\"password\":\"testpass123\"}'
```

### Login
```powershell
curl -X POST http://localhost:5000/api/auth/login `
  -H "Content-Type: application/json" `
  -d '{\"emailOrUsername\":\"testuser\",\"password\":\"testpass123\",\"role\":\"patient\"}'
```

Save the token from the response.

### Get Current User
```powershell
curl -X GET http://localhost:5000/api/users/me `
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### Upload Image for Prediction
```powershell
curl -X POST http://localhost:5000/api/predictions/predict `
  -H "Authorization: Bearer YOUR_TOKEN_HERE" `
  -F "image=@path\to\your\image.jpg"
```

### Get Predictions History
```powershell
curl -X GET http://localhost:5000/api/predictions `
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

## Development

### Install Dependencies
```powershell
pip install -r requirements.txt
```

### Run with Hot Reload
```powershell
uvicorn app.main:app --reload --port 5000
```

### Project Dependencies

Key packages:
- **FastAPI**: Modern web framework
- **Uvicorn**: ASGI server
- **Motor**: Async MongoDB driver
- **Pydantic**: Data validation
- **python-jose**: JWT handling
- **Passlib**: Password hashing (bcrypt)
- **TensorFlow**: ML model inference
- **OpenCV + cvlib**: Image validation
- **aiosmtplib**: Async email sending

## Security Notes

- **JWT**: Tokens expire after 1 day
- **Passwords**: Hashed with bcrypt before storage
- **CORS**: Configure `ORIGIN` in `.env` for production
- **Secrets**: Never commit `.env` file - use `.env.example` as template

## Troubleshooting

### Model Not Loading
```
WARNING: Model file not found: ResNet_Model.keras
```
**Solution**: Place `ResNet_Model.keras` in the project root directory.

### MongoDB Connection Failed
```
ERROR: Failed to connect to MongoDB
```
**Solution**: Ensure MongoDB is running and `MONGO_URI` is correct in `.env`.

### Email Sending Failed
```
ERROR: Failed to send email
```
**Solution**: 
- Verify Gmail credentials in `.env`
- Ensure App Password is generated (not regular password)
- Check internet connection

### OpenCV Import Error (Windows)
```
ImportError: DLL load failed
```
**Solution**: Install Visual C++ Redistributable
- Download from: https://aka.ms/vs/17/release/vc_redist.x64.exe

### Face Detection Not Working
```
ERROR: No face detected in the image
```
**Solution**: Ensure the image contains a clearly visible face with good lighting.

## Production Deployment

1. **Set strong JWT_SECRET** (use cryptographically random string)
2. **Configure CORS** to specific frontend origin
3. **Use MongoDB Atlas** or secure MongoDB instance
4. **Enable HTTPS** via reverse proxy (nginx/Caddy)
5. **Set up logging** to file or external service
6. **Monitor uploads/** directory size
7. **Consider using cloud storage** for uploaded images (S3, Azure Blob)

## License

Proprietary - FacialDerma AI Project

## Support

For issues or questions, contact the development team.

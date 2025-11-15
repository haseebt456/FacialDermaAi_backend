# FacialDerma AI Backend - Quick Start Script
# Run this script to set up and start the backend

Write-Host "=== FacialDerma AI Backend Setup ===" -ForegroundColor Cyan

# Check if virtual environment exists
if (-Not (Test-Path "venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
.\venv\Scripts\Activate.ps1

# Install dependencies
Write-Host "Installing dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt

# Check if .env exists
if (-Not (Test-Path ".env")) {
    Write-Host "Creating .env from .env.example..." -ForegroundColor Yellow
    Copy-Item .env.example .env
    Write-Host "IMPORTANT: Please edit .env file with your actual credentials!" -ForegroundColor Red
    Write-Host "Required: MONGO_URI, JWT_SECRET, EMAIL_USER, EMAIL_PASS" -ForegroundColor Red
    $continue = Read-Host "Press Enter to continue after editing .env, or Ctrl+C to exit"
}

# Check for model file
if (-Not (Test-Path "ResNet_Model.keras")) {
    Write-Host "WARNING: ResNet_Model.keras not found!" -ForegroundColor Red
    Write-Host "Please add the model file to the root directory." -ForegroundColor Yellow
    Write-Host "The app will start, but predictions will fail without the model." -ForegroundColor Yellow
}

# Create uploads directory
if (-Not (Test-Path "uploads")) {
    New-Item -ItemType Directory -Path "uploads" | Out-Null
    Write-Host "Created uploads directory" -ForegroundColor Green
}

Write-Host "`n=== Starting FacialDerma AI Backend ===" -ForegroundColor Cyan
Write-Host "Server will start at: http://localhost:5000" -ForegroundColor Green
Write-Host "Press Ctrl+C to stop the server`n" -ForegroundColor Yellow

# Start the server
uvicorn app.main:app --host 0.0.0.0 --port 5000 --reload

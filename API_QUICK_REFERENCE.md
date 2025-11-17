# Quick API Reference - Dermatologist Review Workflow

## Base URL
```
http://localhost:5000
```

## Authentication
All endpoints require JWT token in header:
```
Authorization: Bearer <token>
```

## Quick Start - Patient Flow

### 1. List Dermatologists
```http
GET /api/users/dermatologists?q=smith&limit=10
```

### 2. Create Review Request
```json
POST /api/review-requests
{
  "predictionId": "6734...",
  "dermatologistId": "6734..."
}
```

### 3. Check Notifications
```http
GET /api/notifications?unreadOnly=true
```

### 4. View Request
```http
GET /api/review-requests/{requestId}
```

## Quick Start - Dermatologist Flow

### 1. Check Notifications
```http
GET /api/notifications?unreadOnly=true
```

### 2. List Pending Requests
```http
GET /api/review-requests?status=pending
```

### 3. View Request Details
```http
GET /api/review-requests/{requestId}
```

### 4. Submit Review
```json
POST /api/review-requests/{requestId}/review
{
  "comment": "Your expert review here..."
}
```

### 5. List Reviewed Requests
```http
GET /api/review-requests?status=reviewed
```

## Common Responses

### Success (201 Created)
```json
{
  "id": "67342abc...",
  "status": "pending",
  "createdAt": "2025-11-16T20:00:00Z",
  ...
}
```

### Error (400 Bad Request)
```json
{
  "error": "Invalid ObjectId format"
}
```

### Error (403 Forbidden)
```json
{
  "error": "Access denied. Required role: dermatologist"
}
```

### Error (409 Conflict)
```json
{
  "error": "A review request to this dermatologist already exists for this prediction"
}
```

## Testing Tips

### Get Tokens
```bash
# Login and save token
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"emailOrUsername":"user@test.com","password":"pass","role":"patient"}'

# Extract token from response and use in subsequent requests
```

### Test with Swagger UI
```
http://localhost:5000/docs
```
- Click "Authorize" button
- Enter: `Bearer <your-token>`
- Test all endpoints interactively

## Role Requirements

| Endpoint | Patient | Dermatologist |
|----------|---------|---------------|
| GET /api/users/dermatologists | ✓ | ✓ |
| POST /api/review-requests | ✓ | ✗ |
| GET /api/review-requests | ✓ (own) | ✓ (assigned) |
| GET /api/review-requests/{id} | ✓ (own) | ✓ (assigned) |
| POST /api/review-requests/{id}/review | ✗ | ✓ |
| GET /api/notifications | ✓ | ✓ |
| PATCH /api/notifications/{id}/read | ✓ | ✓ |

## Status Codes

- `200` OK - Success
- `201` Created - Resource created
- `204` No Content - Success (no body)
- `400` Bad Request - Invalid input
- `401` Unauthorized - Missing/invalid token
- `403` Forbidden - Insufficient permissions
- `404` Not Found - Resource doesn't exist
- `409` Conflict - Duplicate resource

## Collections

### review_requests
- Stores review requests linking patients, dermatologists, and predictions
- Status: `pending` → `reviewed`
- Unique constraint: (predictionId, dermatologistId)

### notifications
- Stores in-app notifications
- Types: `review_requested`, `review_submitted`
- Can be marked as read

## Full Documentation

See `DERMATOLOGIST_WORKFLOW.md` for complete testing guide.

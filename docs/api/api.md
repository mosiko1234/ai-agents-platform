# docs/api.md

# AI Agents Platform - תיעוד API

## כללי

### Base URL
```
https://api.aiagents.example.com/v1
```

### אימות
כל הבקשות חייבות לכלול header של API key:
```http
X-API-Key: your-api-key
```

### פורמט תשובות
כל התשובות מוחזרות בפורמט JSON:
```json
{
    "status": "success|error",
    "data": {},
    "message": "תיאור אופציונלי"
}
```

### טיפול בשגיאות
קודי שגיאה סטנדרטיים:
- `400` - בקשה לא תקינה
- `401` - לא מורשה
- `403` - אין הרשאה
- `404` - לא נמצא
- `429` - יותר מדי בקשות
- `500` - שגיאת שרת

## Endpoints

### שליחת הודעה

#### בקשה
```http
POST /messages

{
    "agent_id": "shimon",
    "content": "האם ניתן לבצע עיקול על חשבון בנק?",
    "platform": "whatsapp|telegram",
    "user_id": "user123",
    "context": {
        "group_id": "group123",
        "thread_id": "thread123",
        "language": "he"
    }
}
```

#### תשובה
```json
{
    "status": "success",
    "data": {
        "response": "תשובת הסוכן",
        "references": [
            {
                "type": "חוק",
                "name": "חוק ההוצאה לפועל",
                "reference": "סעיף 7"
            }
        ],
        "confidence_score": 0.85,
        "processing_time": 1.2
    }
}
```

### קבלת סטטוס סוכן

#### בקשה
```http
GET /agents/{agent_id}/status
```

#### תשובה
```json
{
    "status": "success",
    "data": {
        "agent_id": "shimon",
        "status": "active",
        "last_active": "2024-01-23T10:30:00Z",
        "total_requests": 1500,
        "success_rate": 0.95,
        "average_response_time": 1.3,
        "knowledge_update_time": "2024-01-23T00:00:00Z"
    }
}
```

### עדכון ידע סוכן

#### בקשה
```http
POST /agents/{agent_id}/update

{
    "force": false,
    "categories": ["execution", "debt_collection"]
}
```

#### תשובה
```json
{
    "status": "success",
    "data": {
        "update_id": "update123",
        "started_at": "2024-01-23T12:00:00Z",
        "status": "in_progress"
    }
}
```

### קבלת מטריקות

#### בקשה
```http
GET /metrics?period=24h
```

#### תשובה
```json
{
    "status": "success",
    "data": {
        "total_requests": 5000,
        "success_rate": 0.97,
        "average_response_time": 1.4,
        "requests_by_agent": {
            "shimon": 5000
        },
        "requests_by_platform": {
            "whatsapp": 3000,
            "telegram": 2000
        }
    }
}
```

### WebHooks

#### WhatsApp
```http
POST /webhook/whatsapp

{
    "entry": [{
        "changes": [{
            "value": {
                "messages": [{
                    "from": "user123",
                    "text": {
                        "body": "תוכן ההודעה"
                    }
                }]
            }
        }]
    }]
}
```

#### Telegram
```http
POST /webhook/telegram

{
    "message": {
        "message_id": 123,
        "from": {
            "id": "user123"
        },
        "chat": {
            "id": "chat123"
        },
        "text": "תוכן ההודעה"
    }
}
```

## Rate Limiting

### מגבלות
- API: 100 בקשות לדקה
- Webhook: 1000 בקשות לדקה
- עדכוני ידע: 1 לשעה לסוכן

### Headers
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1706013600
```

## דוגמאות שימוש

### Python
```python
import requests

API_URL = "https://api.aiagents.example.com/v1"
API_KEY = "your-api-key"

headers = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

# שליחת שאלה
response = requests.post(
    f"{API_URL}/messages",
    headers=headers,
    json={
        "agent_id": "shimon",
        "content": "שאלה משפטית",
        "platform": "whatsapp",
        "user_id": "user123"
    }
)

print(response.json())
```

### cURL
```bash
# שליחת שאלה
curl -X POST "https://api.aiagents.example.com/v1/messages" \
     -H "X-API-Key: your-api-key" \
     -H "Content-Type: application/json" \
     -d '{
         "agent_id": "shimon",
         "content": "שאלה משפטית",
         "platform": "whatsapp",
         "user_id": "user123"
     }'
```
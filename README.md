# docs/README.md

# AI Agents Platform - תיעוד מערכת

## תוכן עניינים
1. [סקירה כללית](#overview)
2. [ארכיטקטורה](#architecture)
3. [התקנה והגדרה](#setup)
4. [API](#api)
5. [ניהול והפעלה](#operations)
6. [פיתוח](#development)

## סקירה כללית <a name="overview"></a>

מערכת AI Agents היא פלטפורמה להפעלת סוכני בינה מלאכותית המתמחים בתחומים שונים. כרגע המערכת כוללת את:

- **שמעון**: סוכן המתמחה בהוצאה לפועל ואכיפת פסקי דין
- (סוכנים נוספים בפיתוח)

### יכולות עיקריות
- תקשורת עם קבוצות WhatsApp ו-Telegram
- עיבוד שאלות משפטיות
- גישה למאגרי מידע משפטיים
- למידה והתעדכנות מתמדת

## ארכיטקטורה <a name="architecture"></a>

### רכיבים מרכזיים
```
AI Agents Platform
├── API Service
│   ├── FastAPI Backend
│   └── WebSocket Server
├── AI Agents
│   ├── Agent Manager
│   └── Knowledge Base
├── Integrations
│   ├── WhatsApp
│   └── Telegram
└── Storage
    ├── Cosmos DB
    └── Redis Cache
```

### טכנולוגיות
- **שפות**: Python 3.11
- **Framework**: FastAPI
- **תשתית**: Azure (AKS, Cosmos DB)
- **AI**: Azure OpenAI Service
- **ניטור**: Prometheus & Grafana

## התקנה והגדרה <a name="setup"></a>

### דרישות מערכת
- Python 3.11+
- Docker & Docker Compose
- Azure CLI
- kubectl

### התקנה לפיתוח
```bash
# Clone the repository
git clone https://github.com/your-org/ai-agents-platform.git
cd ai-agents-platform

# Run setup script
./scripts/setup.sh
```

### משתני סביבה
```bash
# .env file
AZURE_CLIENT_ID=your_client_id
AZURE_CLIENT_SECRET=your_client_secret
AZURE_TENANT_ID=your_tenant_id
OPENAI_API_KEY=your_openai_key
```

## API <a name="api"></a>

### Endpoints

#### הודעות
```http
POST /api/v1/messages
Content-Type: application/json

{
    "agent_id": "shimon",
    "content": "שאלה משפטית",
    "platform": "whatsapp",
    "user_id": "user123",
    "context": {}
}
```

#### סטטוס סוכן
```http
GET /api/v1/agents/{agent_id}/status
```

#### עדכון ידע
```http
POST /api/v1/agents/{agent_id}/update
```

### אבטחה
- אימות באמצעות API Key
- הגבלת קצב פניות
- HTTPS חובה

## ניהול והפעלה <a name="operations"></a>

### פריסה
```bash
# Deploy to environment
./scripts/deploy.sh [dev|staging|prod]
```

### ניטור
- Prometheus metrics: `http://localhost:9090`
- Grafana dashboards: `http://localhost:3000`

### תחזוקה
- גיבויים אוטומטיים
- ניקוי לוגים ישנים
- עדכוני ידע תקופתיים

## פיתוח <a name="development"></a>

### תהליך עבודה
1. יצירת ענף חדש מ-develop
2. פיתוח ובדיקות
3. Pull Request ל-develop
4. Code Review
5. מיזוג ל-develop

### בדיקות
```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=src
```

### לינטינג
```bash
# Format code
poetry run black src/

# Sort imports
poetry run isort src/

# Type checking
poetry run mypy src/
```

### הוספת סוכן חדש
1. יצירת תיקייה חדשה ב-`src/agents/`
2. הגדרת מחלקת הסוכן
3. הגדרת בסיס ידע
4. רישום הסוכן במערכת
5. בדיקות ותיעוד
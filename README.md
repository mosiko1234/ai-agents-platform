# AI Agents Platform

פלטפורמה מתקדמת לניהול והפעלת סוכני AI חכמים.

## תיאור
מערכת המאפשרת הפעלה וניהול של מספר סוכני AI, כאשר כל סוכן מתמחה בתחום ספציפי. המערכת מבוססת על Azure ו-OpenAI.

## סוכנים פעילים
- שמעון - מומחה להוצאה לפועל ואכיפת פסקי דין
- (סוכנים נוספים בפיתוח)

## דרישות מערכת
- Python 3.11+
- Docker
- Terraform
- Azure CLI
- Kubernetes CLI (kubectl)

## התקנה

```bash
# Clone the repository
git clone https://github.com/your-username/ai-agents-platform.git
cd ai-agents-platform

# Create virtual environment
python -m venv venv
source venv/bin/activate  # או בווינדוס: .\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# ערוך את קובץ .env עם הערכים המתאימים
```

## פיתוח

### הרצה לוקלית
```bash
docker-compose up
```

### הוספת סוכן חדש
1. צור תיקייה חדשה תחת `src/agents/`
2. העתק את תבנית הסוכן הבסיסית
3. התאם את הקוד לצרכי הסוכן החדש

## תרומה לפרויקט
1. Fork את הריפו
2. צור ענף חדש (`git checkout -b feature/amazing-feature`)
3. Commit את השינויים (`git commit -m 'Add amazing feature'`)
4. Push לענף (`git push origin feature/amazing-feature`)
5. פתח Pull Request

## רישיון
כל הזכויות שמורות

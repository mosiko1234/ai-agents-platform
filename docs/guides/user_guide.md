# docs/user_guide.md

# מדריך למשתמש ומנהל מערכת - AI Agents Platform

## תוכן עניינים
1. [למשתמש](#user-guide)
   - [התחברות למערכת](#login)
   - [שימוש בסוכנים](#using-agents)
   - [שאלות נפוצות](#faq)
2. [למנהל מערכת](#admin-guide)
   - [ניהול משתמשים](#user-management)
   - [ניטור ובקרה](#monitoring)
   - [תחזוקה](#maintenance)
3. [פתרון בעיות](#troubleshooting)

## למשתמש <a name="user-guide"></a>

### התחברות למערכת <a name="login"></a>

#### הרשמה לשירות
1. צור קשר עם מנהל המערכת לקבלת הרשאות
2. קבל את פרטי ההתחברות במייל
3. התחבר למערכת באמצעות הפרטים שקיבלת

#### חיבור לקבוצות
1. WhatsApp:
   ```
   1. הוסף את מספר הבוט: +972-XX-XXXXXXX
   2. שלח הודעת "הרשמה" 
   3. עקוב אחר ההוראות להשלמת ההרשמה
   ```

2. Telegram:
   ```
   1. חפש את הבוט: @ShimonAIBot
   2. לחץ על Start
   3. הזן את קוד ההרשאה שקיבלת
   ```

### שימוש בסוכנים <a name="using-agents"></a>

#### שמעון - עוזר משפטי

##### סוגי שאלות נתמכות:
- שאלות על הליכי הוצאה לפועל
- מידע על עיקולים וגביית חובות
- הנחיות לביצוע פעולות משפטיות
- בירור סטטוס תיקים

##### דוגמאות לשאלות:
```
✓ "מה התנאים להגשת בקשת עיקול?"
✓ "איך מבצעים עיקול על חשבון בנק?"
✓ "מה המשמעות של צו כינוס נכסים?"
```

##### טיפים לשאלות יעילות:
1. היה ספציפי ומדויק
2. ציין פרטים רלוונטיים
3. שאל שאלה אחת בכל פעם
4. ציין את הקונטקסט אם רלוונטי

### שאלות נפוצות <a name="faq"></a>

#### כלליות
ש: כמה זמן לוקח לקבל תשובה?
ת: בדרך כלל תוך 30 שניות.

ש: האם אפשר לשאול בשפות אחרות?
ת: כרגע המערכת תומכת בעברית בלבד.

#### טכניות
ש: מה לעשות אם אין תשובה?
ת: נסה לשלוח שוב אחרי דקה. אם הבעיה נמשכת, פנה לתמיכה.

ש: איך מדווחים על תקלה?
ת: שלח הודעה עם המילה "תקלה" ותיאור הבעיה.

## למנהל מערכת <a name="admin-guide"></a>

### ניהול משתמשים <a name="user-management"></a>

#### הוספת משתמש חדש
```bash
# CLI
./manage.sh user add --email user@example.com --role standard

# API
curl -X POST "https://api.example.com/v1/users" \
     -H "Authorization: Bearer ${TOKEN}" \
     -d '{"email": "user@example.com", "role": "standard"}'
```

#### ניהול הרשאות
```bash
# הענקת הרשאות
./manage.sh user grant --email user@example.com --permission "read:cases"

# הסרת הרשאות
./manage.sh user revoke --email user@example.com --permission "write:cases"
```

### ניטור ובקרה <a name="monitoring"></a>

#### דשבורדים
1. System Health: `http://monitor.example.com/d/system`
2. User Activity: `http://monitor.example.com/d/users`
3. Agent Performance: `http://monitor.example.com/d/agents`

#### התראות
הגדרת התראות חדשות:
```yaml
# alerts.yml
alerts:
  - name: high_error_rate
    condition: error_rate > 0.1
    for: 5m
    severity: critical
    channels: 
      - slack
      - email
```

#### דוחות
```bash
# דוח פעילות יומי
./manage.sh report daily

# דוח ביצועים
./manage.sh report performance --days 7
```

### תחזוקה <a name="maintenance"></a>

#### גיבויים
```bash
# גיבוי מלא
./manage.sh backup full

# שחזור מגיבוי
./manage.sh restore --backup-id backup_20240123
```

#### עדכוני מערכת
```bash
# בדיקת עדכונים זמינים
./manage.sh system check-updates

# ביצוע עדכון
./manage.sh system update
```

#### ניקוי מערכת
```bash
# ניקוי לוגים ישנים
./manage.sh cleanup logs --older-than 30d

# ניקוי מטמון
./manage.sh cleanup cache
```

## פתרון בעיות <a name="troubleshooting"></a>

### בעיות נפוצות

#### המערכת לא מגיבה
1. בדוק סטטוס שירותים:
```bash
./manage.sh status services
```

2. בדוק לוגים:
```bash
./manage.sh logs --service api --tail 100
```

3. בדוק מטריקות:
```bash
./manage.sh metrics --service api
```

#### שגיאות אימות
1. בדוק תוקף טוקן:
```bash
./manage.sh token verify ${TOKEN}
```

2. חדש טוקן:
```bash
./manage.sh token refresh ${TOKEN}
```

### תהליך דיווח תקלות

1. איסוף מידע:
   - לוגים רלוונטיים
   - מטריקות מערכת
   - פרטי משתמש/סוכן
   
2. תיעוד התקלה:
   ```bash
   ./manage.sh issue create \
     --type bug \
     --severity medium \
     --description "תיאור התקלה" \
     --logs-file logs.txt
   ```

3. מעקב אחר טיפול:
   ```bash
   ./manage.sh issue status ${ISSUE_ID}
   ```

### רשימת בדיקה לפתרון בעיות

- [ ] בדיקת סטטוס שירותים
- [ ] בדיקת לוגים
- [ ] בדיקת מטריקות
- [ ] בדיקת קישוריות
- [ ] בדיקת הרשאות
- [ ] בדיקת תצורה
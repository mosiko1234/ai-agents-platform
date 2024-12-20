# src/api/integrations/config.py

from typing import Dict
from pydantic import BaseSettings
import os

class IntegrationSettings(BaseSettings):
    """הגדרות בסיסיות לאינטגרציות"""
    
    # WhatsApp Configuration
    WHATSAPP_API_VERSION: str = "v16.0"
    WHATSAPP_BASE_URL: str = "https://graph.facebook.com"
    WHATSAPP_PHONE_NUMBER_ID: str = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
    WHATSAPP_ACCESS_TOKEN: str = os.getenv("WHATSAPP_ACCESS_TOKEN", "")
    
    # Telegram Configuration
    TELEGRAM_API_VERSION: str = "v6.7"
    TELEGRAM_BASE_URL: str = "https://api.telegram.org/bot{token}"
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_WEBHOOK_URL: str = os.getenv("TELEGRAM_WEBHOOK_URL", "")
    
    # Common Settings
    DEBUG_MODE: bool = os.getenv("DEBUG", "False").lower() == "true"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    class Config:
        case_sensitive = True

settings = IntegrationSettings()

# WhatsApp Configuration
WHATSAPP_CONFIG = {
    "api_version": settings.WHATSAPP_API_VERSION,
    "base_url": settings.WHATSAPP_BASE_URL,
    "message_template": {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "type": "text"
    },
    "max_message_length": 4096,
    "message_footer": "\n\n---\nנשלח על ידי שמעון AI - עוזר משפטי חכם",
    "response_templates": {
        "error": "מצטער, אירעה שגיאה בעיבוד הבקשה. אנא נסה שוב מאוחר יותר.",
        "processing": "אני מעבד את השאלה שלך, אנא המתן...",
        "missing_context": "אני צריך מידע נוסף כדי לענות על השאלה. אנא פרט יותר.",
        "not_legal": "השאלה אינה בתחום המשפטי. אני מתמחה בשאלות בנושא הוצאה לפועל ואכיפת פסקי דין."
    },
    "allowed_types": ["text", "document"],
    "document_types": [".pdf", ".doc", ".docx", ".txt"]
}

# Telegram Configuration
TELEGRAM_CONFIG = {
    "api_version": settings.TELEGRAM_API_VERSION,
    "base_url": settings.TELEGRAM_BASE_URL,
    "max_message_length": 4096,
    "message_footer": "\n\n---\nנשלח על ידי שמעון AI - עוזר משפטי חכם",
    "response_templates": {
        "error": "🚫 מצטער, אירעה שגיאה בעיבוד הבקשה. אנא נסה שוב מאוחר יותר.",
        "processing": "⌛ מעבד את השאלה שלך...",
        "missing_context": "❓ אני צריך מידע נוסף. אנא פרט יותר.",
        "not_legal": "📢 השאלה אינה בתחום המשפטי. אני מתמחה בשאלות בנושא הוצאה לפועל ואכיפת פסקי דין."
    },
    "keyboard_templates": {
        "main_menu": {
            "inline_keyboard": [
                [
                    {"text": "📚 מידע על הוצאה לפועל", "callback_data": "info_execution"},
                    {"text": "💼 שאלות נפוצות", "callback_data": "faq"}
                ],
                [
                    {"text": "📋 הגשת בקשה", "callback_data": "submit_request"},
                    {"text": "📞 יצירת קשר", "callback_data": "contact"}
                ]
            ]
        },
        "categories": {
            "inline_keyboard": [
                [
                    {"text": "עיקולים", "callback_data": "category_seizure"},
                    {"text": "פסקי דין", "callback_data": "category_rulings"}
                ],
                [
                    {"text": "גביית חובות", "callback_data": "category_debt"},
                    {"text": "פשיטת רגל", "callback_data": "category_bankruptcy"}
                ],
                [{"text": "חזרה לתפריט הראשי", "callback_data": "main_menu"}]
            ]
        }
    }
}

# Rate Limiting Configuration
RATE_LIMITS = {
    "whatsapp": {
        "messages_per_second": 10,
        "messages_per_minute": 60,
        "messages_per_hour": 1000,
        "messages_per_day": 10000
    },
    "telegram": {
        "messages_per_second": 30,
        "messages_per_minute": 120,
        "messages_per_hour": 3000,
        "messages_per_day": 50000
    }
}

# Common Message Processing
COMMON_PROCESSING = {
    "max_retries": 3,
    "retry_delay": 1,  # seconds
    "timeout": 30,  # seconds
    "chunk_size": 4000,  # characters
    "allowed_mime_types": [
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "text/plain"
    ],
    "max_file_size": 10 * 1024 * 1024  # 10MB
}

# Response Formatting
RESPONSE_FORMATTING = {
    "max_references": 5,
    "max_suggestions": 3,
    "link_preview": False,
    "format_options": {
        "bold_markers": ["**", "*"],
        "italic_markers": ["_"],
        "bullet_points": "• ",
        "numbered_list_format": "{}. ",
        "quote_marker": "> "
    }
}

# Error Messages
ERROR_MESSAGES = {
    "rate_limit": "חרגת ממגבלת השימוש. אנא נסה שוב בעוד מספר דקות.",
    "invalid_token": "מפתח API לא תקין",
    "network_error": "בעיית תקשורת. אנא נסה שוב.",
    "invalid_format": "פורמט הודעה לא תקין",
    "file_too_large": "הקובץ גדול מדי. הגודל המקסימלי הוא 10MB.",
    "unsupported_type": "סוג קובץ לא נתמך",
    "processing_error": "שגיאה בעיבוד ההודעה",
    "maintenance": "המערכת בתחזוקה. אנא נסה שוב מאוחר יותר."
}
# src/api/routers/shimon.py

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, Security
from fastapi.security import APIKeyHeader
from typing import Dict, Optional, List
import logging
from datetime import datetime

from core.schemas import Message, AgentResponse
from core.agent_manager import AgentManager
from core.exceptions import AgentError

router = APIRouter(prefix="/agents/shimon", tags=["shimon"])
logger = logging.getLogger(__name__)

# Initialize security
API_KEY_HEADER = APIKeyHeader(name="X-API-Key")

class PlatformData:
    """הגדרת מבנה נתונים לכל פלטפורמה"""
    WHATSAPP = {
        "message_key": "body",
        "sender_key": "from",
        "group_key": "chatId"
    }
    TELEGRAM = {
        "message_key": "text",
        "sender_key": "from.id",
        "group_key": "chat.id"
    }

def extract_message_data(platform: str, data: Dict) -> Dict:
    """חילוץ נתוני ההודעה מהפלטפורמה הספציפית"""
    platform_config = getattr(PlatformData, platform.upper(), None)
    if not platform_config:
        raise HTTPException(status_code=400, detail=f"Unsupported platform: {platform}")
    
    try:
        return {
            "content": _get_nested_value(data, platform_config["message_key"]),
            "sender_id": str(_get_nested_value(data, platform_config["sender_key"])),
            "group_id": str(_get_nested_value(data, platform_config["group_key"]))
        }
    except KeyError as e:
        raise HTTPException(status_code=400, detail=f"Invalid message format: {str(e)}")

def _get_nested_value(data: Dict, key_path: str) -> any:
    """אחזור ערך מתוך מבנה נתונים מקונן"""
    current = data
    for key in key_path.split('.'):
        current = current[key]
    return current

# Endpoints
@router.post("/webhook/{platform}")
async def webhook_handler(
    platform: str,
    data: Dict,
    background_tasks: BackgroundTasks,
    agent_manager: AgentManager = Depends(),
    api_key: str = Security(API_KEY_HEADER)
):
    """טיפול בwebhooks מפלטפורמות שונות"""
    try:
        # חילוץ נתוני ההודעה
        message_data = extract_message_data(platform, data)
        
        # יצירת אובייקט הודעה
        message = Message(
            agent_id="shimon",
            content=message_data["content"],
            platform=platform,
            user_id=message_data["sender_id"],
            context={
                "group_id": message_data["group_id"],
                "platform_data": data
            }
        )
        
        # עיבוד ההודעה ברקע
        background_tasks.add_task(process_message_and_respond, agent_manager, message, platform)
        
        return {"status": "processing"}
        
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def get_status(
    agent_manager: AgentManager = Depends(),
    api_key: str = Security(API_KEY_HEADER)
):
    """קבלת סטטוס שמעון"""
    try:
        agent = agent_manager.agents.get("shimon")
        if not agent:
            raise HTTPException(status_code=404, detail="Shimon agent not found")
            
        return {
            "status": "active" if agent.active else "inactive",
            "last_active": agent.last_active.isoformat(),
            "metrics": agent.metrics.dict(),
            "knowledge_last_updated": agent.last_knowledge_update.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/update-knowledge")
async def update_knowledge(
    background_tasks: BackgroundTasks,
    agent_manager: AgentManager = Depends(),
    api_key: str = Security(API_KEY_HEADER)
):
    """עדכון מאגר הידע של שמעון"""
    try:
        agent = agent_manager.agents.get("shimon")
        if not agent:
            raise HTTPException(status_code=404, detail="Shimon agent not found")
            
        background_tasks.add_task(agent.update_knowledge)
        return {"status": "updating"}
        
    except Exception as e:
        logger.error(f"Error updating knowledge: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Platform-specific message handlers
async def process_message_and_respond(
    agent_manager: AgentManager,
    message: Message,
    platform: str
):
    """עיבוד ההודעה ושליחת תשובה"""
    try:
        # קבלת תשובה משמעון
        response = await agent_manager.process_message(message)
        
        # שליחת התשובה בפלטפורמה המתאימה
        if platform.upper() == "WHATSAPP":
            await send_whatsapp_response(message, response)
        elif platform.upper() == "TELEGRAM":
            await send_telegram_response(message, response)
            
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
        # שליחת הודעת שגיאה למשתמש
        error_message = "מצטער, אירעה שגיאה בעיבוד הבקשה. אנא נסה שוב מאוחר יותר."
        if platform.upper() == "WHATSAPP":
            await send_whatsapp_response(message, AgentResponse(content=error_message, agent_id="shimon"))
        elif platform.upper() == "TELEGRAM":
            await send_telegram_response(message, AgentResponse(content=error_message, agent_id="shimon"))

async def send_whatsapp_response(message: Message, response: AgentResponse):
    """שליחת תשובה בWhatsApp"""
    # TODO: Implement WhatsApp API integration
    pass

async def send_telegram_response(message: Message, response: AgentResponse):
    """שליחת תשובה בTelegram"""
    # TODO: Implement Telegram API integration
    pass
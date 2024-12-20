# src/api/integrations/manager.py

from typing import Dict, Optional, Any
import logging
from datetime import datetime
import asyncio
from functools import wraps

from .whatsapp import WhatsAppClient
from .telegram import TelegramClient
from .config import (
    settings,
    WHATSAPP_CONFIG,
    TELEGRAM_CONFIG,
    RATE_LIMITS,
    ERROR_MESSAGES
)
from core.exceptions import IntegrationError
from core.schemas import Message, AgentResponse

logger = logging.getLogger(__name__)

def handle_integration_errors(func):
    """Decorator for handling integration errors"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except IntegrationError as e:
            logger.error(f"Integration error in {func.__name__}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {str(e)}")
            raise IntegrationError(f"Unexpected error: {str(e)}")
    return wrapper

class IntegrationManager:
    """Manager for handling multiple platform integrations"""
    
    def __init__(self):
        self.whatsapp_client: Optional[WhatsAppClient] = None
        self.telegram_client: Optional[TelegramClient] = None
        self.active_platforms = set()
        self._initialized = False
        self._lock = asyncio.Lock()

    async def initialize(self):
        """Initialize all platform clients"""
        if self._initialized:
            return

        async with self._lock:
            if self._initialized:  # Double-check pattern
                return
                
            try:
                # Initialize WhatsApp if configured
                if settings.WHATSAPP_ACCESS_TOKEN and settings.WHATSAPP_PHONE_NUMBER_ID:
                    self.whatsapp_client = WhatsAppClient(
                        settings.WHATSAPP_ACCESS_TOKEN,
                        settings.WHATSAPP_PHONE_NUMBER_ID
                    )
                    await self.whatsapp_client.initialize()
                    self.active_platforms.add("whatsapp")
                
                # Initialize Telegram if configured
                if settings.TELEGRAM_BOT_TOKEN:
                    self.telegram_client = TelegramClient(settings.TELEGRAM_BOT_TOKEN)
                    await self.telegram_client.initialize()
                    self.active_platforms.add("telegram")
                
                if not self.active_platforms:
                    raise IntegrationError("No platforms configured")
                    
                self._initialized = True
                logger.info(f"Integration manager initialized with platforms: {self.active_platforms}")
                
            except Exception as e:
                logger.error(f"Failed to initialize integration manager: {str(e)}")
                raise

    async def close(self):
        """Close all platform connections"""
        try:
            if self.whatsapp_client:
                await self.whatsapp_client.close()
            if self.telegram_client:
                await self.telegram_client.close()
            self._initialized = False
            logger.info("Integration manager closed successfully")
        except Exception as e:
            logger.error(f"Error closing integration manager: {str(e)}")
            raise

    @handle_integration_errors
    async def send_message(
        self,
        platform: str,
        recipient_id: str,
        response: AgentResponse,
        context: Optional[Dict] = None
    ) -> Dict:
        """Send message to specified platform"""
        if not self._initialized:
            await self.initialize()

        platform = platform.lower()
        if platform not in self.active_platforms:
            raise IntegrationError(f"Platform {platform} not configured")

        try:
            if platform == "whatsapp":
                formatted_response = WhatsAppClient.format_response(response)
                return await self.whatsapp_client.send_message(recipient_id, formatted_response)
                
            elif platform == "telegram":
                formatted_response = TelegramClient.format_response(response)
                # Send typing action first
                await self.telegram_client.send_typing_action(recipient_id)
                
                # Handle reply to message if context provides message_id
                reply_to = context.get("platform_data", {}).get("message_id") if context else None
                
                # Add keyboard if available in response metadata
                keyboard = response.metadata.get("keyboard")
                
                return await self.telegram_client.send_message(
                    recipient_id,
                    formatted_response,
                    reply_to_message_id=reply_to,
                    keyboard=keyboard
                )
                
        except Exception as e:
            logger.error(f"Error sending message on {platform}: {str(e)}")
            raise IntegrationError(f"Failed to send message on {platform}: {str(e)}")

    @handle_integration_errors
    async def process_webhook(
        self,
        platform: str,
        data: Dict[str, Any]
    ) -> Optional[Message]:
        """Process webhook data from platforms"""
        if not self._initialized:
            await self.initialize()

        platform = platform.lower()
        if platform not in self.active_platforms:
            raise IntegrationError(f"Platform {platform} not configured")

        try:
            if platform == "whatsapp":
                return await self.whatsapp_client.process_webhook(data)
            elif platform == "telegram":
                return await self.telegram_client.process_webhook(data)
                
        except Exception as e:
            logger.error(f"Error processing webhook from {platform}: {str(e)}")
            raise IntegrationError(f"Failed to process webhook from {platform}: {str(e)}")

    @handle_integration_errors
    async def setup_webhooks(self, base_url: str) -> Dict[str, bool]:
        """Setup webhooks for all active platforms"""
        if not self._initialized:
            await self.initialize()

        results = {}
        try:
            if "whatsapp" in self.active_platforms:
                # WhatsApp webhook setup is handled through Facebook's developer portal
                results["whatsapp"] = True
                
            if "telegram" in self.active_platforms:
                webhook_url = f"{base_url}/webhook/telegram"
                success = await self.telegram_client.set_webhook(
                    webhook_url,
                    settings.TELEGRAM_BOT_TOKEN
                )
                results["telegram"] = success
                
            return results
            
        except Exception as e:
            logger.error(f"Error setting up webhooks: {str(e)}")
            raise IntegrationError(f"Failed to setup webhooks: {str(e)}")

    async def send_error_message(
        self,
        platform: str,
        recipient_id: str,
        error_key: str,
        context: Optional[Dict] = None
    ):
        """Send error message to user"""
        try:
            error_message = ERROR_MESSAGES.get(error_key, ERROR_MESSAGES["processing_error"])
            response = AgentResponse(
                content=error_message,
                agent_id="system",
                processing_time=0,
                metadata={"error": True}
            )
            await self.send_message(platform, recipient_id, response, context)
        except Exception as e:
            logger.error(f"Failed to send error message: {str(e)}")
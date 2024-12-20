# src/api/integrations/telegram.py

from typing import Dict, Optional, Union, List
import aiohttp
import logging
from datetime import datetime
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential

from .config import TELEGRAM_CONFIG, RATE_LIMITS
from core.exceptions import IntegrationError
from core.schemas import Message, AgentResponse

logger = logging.getLogger(__name__)

class TelegramClient:
    """Telegram Bot API Client"""
    
    def __init__(self, bot_token: str):
        self.bot_token = bot_token
        self.base_url = TELEGRAM_CONFIG["base_url"].format(token=bot_token)
        self.rate_limiter = asyncio.Semaphore(RATE_LIMITS["telegram"]["messages_per_second"])
        self.session = None

    async def initialize(self):
        """Initialize HTTP session"""
        if not self.session:
            self.session = aiohttp.ClientSession()

    async def close(self):
        """Close HTTP session"""
        if self.session:
            await self.session.close()
            self.session = None

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def send_message(
        self,
        chat_id: Union[int, str],
        text: str,
        reply_to_message_id: Optional[int] = None,
        parse_mode: str = "HTML",
        disable_preview: bool = True,
        keyboard: Optional[Dict] = None
    ) -> Dict:
        """Send message via Telegram"""
        try:
            async with self.rate_limiter:
                # Split long messages if needed
                messages = self._split_long_message(text)
                responses = []
                
                for msg in messages:
                    payload = {
                        "chat_id": chat_id,
                        "text": msg,
                        "parse_mode": parse_mode,
                        "disable_web_page_preview": disable_preview
                    }
                    
                    if reply_to_message_id and len(responses) == 0:
                        payload["reply_to_message_id"] = reply_to_message_id

                    if keyboard and len(responses) == len(messages) - 1:
                        payload["reply_markup"] = keyboard
                    
                    url = f"{self.base_url}/sendMessage"
                    
                    async with self.session.post(url, json=payload) as response:
                        if response.status != 200:
                            error_data = await response.json()
                            raise IntegrationError(
                                f"Telegram API error: {error_data.get('description')}"
                            )
                        
                        responses.append(await response.json())
                        
                        # Rate limiting delay
                        await asyncio.sleep(0.05)
                
                return responses[-1]  # Return last response
                
        except aiohttp.ClientError as e:
            logger.error(f"Telegram API request failed: {str(e)}")
            raise IntegrationError(f"Telegram request failed: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error in Telegram integration: {str(e)}")
            raise

    async def set_webhook(self, url: str, secret_token: str) -> bool:
        """Set Telegram webhook"""
        try:
            webhook_url = f"{self.base_url}/setWebhook"
            payload = {
                "url": url,
                "secret_token": secret_token,
                "allowed_updates": ["message", "callback_query"],
                "max_connections": 100
            }
            
            async with self.session.post(webhook_url, json=payload) as response:
                if response.status != 200:
                    error_data = await response.json()
                    raise IntegrationError(
                        f"Failed to set webhook: {error_data.get('description')}"
                    )
                
                return True
                
        except Exception as e:
            logger.error(f"Error setting webhook: {str(e)}")
            return False

    async def process_webhook(self, data: Dict) -> Optional[Message]:
        """Process incoming webhook data"""
        try:
            # Handle callback queries (buttons)
            if "callback_query" in data:
                return await self._process_callback_query(data["callback_query"])

            if "message" not in data:
                return None
                
            message = data["message"]
            if "text" not in message:
                return None
                
            return Message(
                agent_id="shimon",
                content=message["text"],
                platform="telegram",
                user_id=str(message["from"]["id"]),
                context={
                    "group_id": str(message["chat"]["id"]),
                    "platform_data": {
                        "message_id": message["message_id"],
                        "chat_type": message["chat"]["type"],
                        "username": message["from"].get("username"),
                        "language": message["from"].get("language_code"),
                        "is_group": message["chat"]["type"] in ["group", "supergroup"]
                    }
                }
            )
            
        except KeyError as e:
            logger.error(f"Invalid webhook data format: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error processing webhook: {str(e)}")
            return None

    async def _process_callback_query(self, callback_query: Dict) -> Optional[Message]:
        """Process callback query from inline buttons"""
        try:
            return Message(
                agent_id="shimon",
                content=callback_query["data"],
                platform="telegram",
                user_id=str(callback_query["from"]["id"]),
                context={
                    "group_id": str(callback_query["message"]["chat"]["id"]),
                    "platform_data": {
                        "callback_query_id": callback_query["id"],
                        "message_id": callback_query["message"]["message_id"],
                        "is_callback": True
                    }
                }
            )
        except Exception as e:
            logger.error(f"Error processing callback query: {str(e)}")
            return None

    def _split_long_message(
        self,
        content: str,
        max_length: int = TELEGRAM_CONFIG["max_message_length"]
    ) -> List[str]:
        """Split long messages into smaller chunks"""
        if len(content) <= max_length:
            return [content]
            
        messages = []
        current_position = 0
        total_parts = -(-len(content) // max_length)  # Ceiling division
        
        while current_position < len(content):
            # Try to split at a natural break point
            end_position = min(current_position + max_length, len(content))
            if end_position < len(content):
                # Look for last sentence or paragraph break
                for separator in ['\n\n', '\n', '. ', ' ']:
                    last_break = content.rfind(separator, current_position, end_position)
                    if last_break != -1:
                        end_position = last_break + len(separator)
                        break
            
            part_number = len(messages) + 1
            part_suffix = f"\n[חלק {part_number}/{total_parts}]" if total_parts > 1 else ""
            
            messages.append(content[current_position:end_position].strip() + part_suffix)
            current_position = end_position
        
        return messages

    @staticmethod
    def format_response(response: AgentResponse) -> str:
        """Format agent response for Telegram"""
        # Convert to HTML format for Telegram
        formatted_content = response.content.strip()
        
        # Add formatting
        formatted_content = formatted_content.replace('*', '<b>').replace('*', '</b>')
        formatted_content = formatted_content.replace('_', '<i>').replace('_', '</i>')
        
        # Add references if available
        if response.metadata.get("references"):
            formatted_content += "\n\n<b>מקורות ואסמכתאות:</b>\n" + "\n".join(
                f"• {ref}" for ref in response.metadata["references"]
            )
            
        return formatted_content + TELEGRAM_CONFIG.get("message_footer", "")

    async def send_typing_action(self, chat_id: Union[int, str]) -> None:
        """Send typing action to indicate the bot is processing"""
        try:
            url = f"{self.base_url}/sendChatAction"
            payload = {
                "chat_id": chat_id,
                "action": "typing"
            }
            
            async with self.session.post(url, json=payload) as response:
                if response.status != 200:
                    logger.warning("Failed to send typing action")
                    
        except Exception as e:
            logger.error(f"Error sending typing action: {str(e)}")
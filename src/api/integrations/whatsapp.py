# src/api/integrations/whatsapp.py

from typing import Dict, Optional, Union
import aiohttp
import logging
import json
from datetime import datetime
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential

from .config import WHATSAPP_CONFIG, RATE_LIMITS
from core.exceptions import IntegrationError
from core.schemas import Message, AgentResponse

logger = logging.getLogger(__name__)

class WhatsAppClient:
    """WhatsApp Business API Client"""
    
    def __init__(self, access_token: str, phone_number_id: str):
        self.access_token = access_token
        self.phone_number_id = phone_number_id
        self.base_url = WHATSAPP_CONFIG["base_url"]
        self.api_version = WHATSAPP_CONFIG["api_version"]
        self.rate_limiter = asyncio.Semaphore(RATE_LIMITS["whatsapp"]["messages_per_second"])
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
    async def send_message(self, recipient: str, content: str) -> Dict:
        """Send message via WhatsApp"""
        try:
            async with self.rate_limiter:
                # Split long messages if needed
                messages = self._split_long_message(content)
                responses = []
                
                for msg in messages:
                    payload = {
                        **WHATSAPP_CONFIG["message_template"],
                        "to": recipient,
                        "text": {"body": msg}
                    }
                    
                    url = f"{self.base_url}/{self.api_version}/{self.phone_number_id}/messages"
                    
                    async with self.session.post(
                        url,
                        headers={
                            "Authorization": f"Bearer {self.access_token}",
                            "Content-Type": "application/json"
                        },
                        json=payload
                    ) as response:
                        if response.status != 200:
                            error_data = await response.json()
                            raise IntegrationError(
                                f"WhatsApp API error: {error_data.get('error', {}).get('message')}"
                            )
                        
                        responses.append(await response.json())
                        
                        # Rate limiting delay
                        await asyncio.sleep(0.1)
                
                return responses[-1]  # Return last response
                
        except aiohttp.ClientError as e:
            logger.error(f"WhatsApp API request failed: {str(e)}")
            raise IntegrationError(f"WhatsApp request failed: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error in WhatsApp integration: {str(e)}")
            raise

    async def verify_webhook(self, token: str, challenge: str) -> bool:
        """Verify WhatsApp webhook"""
        try:
            expected_token = "your_webhook_verify_token"  # Configure in environment
            if token != expected_token:
                return False
            return True
        except Exception as e:
            logger.error(f"Webhook verification failed: {str(e)}")
            return False

    async def process_webhook(self, data: Dict) -> Optional[Message]:
        """Process incoming webhook data"""
        try:
            # Extract message data
            entry = data["entry"][0]
            changes = entry["changes"][0]
            value = changes["value"]
            
            if "messages" not in value:
                return None
                
            message = value["messages"][0]
            
            return Message(
                agent_id="shimon",  # Hardcoded for now
                content=message["text"]["body"],
                platform="whatsapp",
                user_id=message["from"],
                context={
                    "group_id": value.get("conversation", {}).get("id"),
                    "platform_data": {
                        "message_id": message["id"],
                        "timestamp": message["timestamp"],
                        "type": message["type"]
                    }
                }
            )
            
        except KeyError as e:
            logger.error(f"Invalid webhook data format: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error processing webhook: {str(e)}")
            return None

    def _split_long_message(self, content: str, max_length: int = 1500) -> list:
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
                # Look for last sentence break
                last_period = content.rfind('. ', current_position, end_position)
                if last_period != -1:
                    end_position = last_period + 1
            
            part_number = len(messages) + 1
            part_suffix = f"\n[חלק {part_number}/{total_parts}]" if total_parts > 1 else ""
            
            messages.append(content[current_position:end_position].strip() + part_suffix)
            current_position = end_position
        
        return messages

    @staticmethod
    def format_response(response: AgentResponse) -> str:
        """Format agent response for WhatsApp"""
        # Add any WhatsApp-specific formatting
        formatted_content = response.content.strip()
        
        if response.metadata.get("references"):
            formatted_content += "\n\nמקורות:\n" + "\n".join(response.metadata["references"])
            
        return formatted_content + WHATSAPP_CONFIG.get("message_footer", "")
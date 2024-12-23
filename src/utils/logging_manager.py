# src/utils/logging_manager.py

from typing import Dict, Optional, Any, List
import logging
import json
from datetime import datetime, timedelta
import asyncio
import aiohttp
from pathlib import Path
import sys
from logging.handlers import RotatingFileHandler
import traceback
from azure.monitor.opentelemetry import metrics
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

class LoggingManager:
    """מנהל לוגים והתראות של המערכת"""
    
    def __init__(self):
        self.log_dir = Path("logs")
        self.log_dir.mkdir(exist_ok=True)
        
        # הגדרות ברירת מחדל
        self.default_config = {
            "console_level": logging.INFO,
            "file_level": logging.DEBUG,
            "max_file_size": 10 * 1024 * 1024,  # 10MB
            "backup_count": 5
        }
        
        # רמות חומרה להתראות
        self.alert_levels = {
            "INFO": 0,
            "WARNING": 1,
            "ERROR": 2,
            "CRITICAL": 3
        }
        
        # URLs להתראות
        self.alert_urls = {
            "teams_webhook": None,
            "slack_webhook": None,
            "email_api": None
        }
        
        self.tracer = trace.get_tracer(__name__)
        self.meter = metrics.get_meter(__name__)
        
        # יצירת מטריקות
        self.error_counter = self.meter.create_counter(
            "error_count",
            description="Number of errors by severity"
        )

    async def initialize(
        self,
        config: Optional[Dict] = None,
        alert_urls: Optional[Dict] = None
    ):
        """אתחול מנהל הלוגים"""
        try:
            # עדכון הגדרות
            if config:
                self.default_config.update(config)
            if alert_urls:
                self.alert_urls.update(alert_urls)
            
            # הגדרת לוגר ראשי
            logger = logging.getLogger()
            logger.setLevel(logging.DEBUG)
            
            # הגדרת פורמט
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            
            # הגדרת handler לקונסול
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(self.default_config["console_level"])
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
            
            # הגדרת handler לקובץ
            file_handler = RotatingFileHandler(
                self.log_dir / "app.log",
                maxBytes=self.default_config["max_file_size"],
                backupCount=self.default_config["backup_count"]
            )
            file_handler.setLevel(self.default_config["file_level"])
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
            
            # הגדרת handler לשגיאות
            error_handler = RotatingFileHandler(
                self.log_dir / "error.log",
                maxBytes=self.default_config["max_file_size"],
                backupCount=self.default_config["backup_count"]
            )
            error_handler.setLevel(logging.ERROR)
            error_handler.setFormatter(formatter)
            logger.addHandler(error_handler)
            
            logging.info("Logging manager initialized successfully")
            
        except Exception as e:
            print(f"Failed to initialize logging manager: {str(e)}")
            raise

    async def log_error(
        self,
        error: Exception,
        context: Optional[Dict] = None,
        alert: bool = True
    ):
        """תיעוד שגיאה ושליחת התראה"""
        try:
            with self.tracer.start_as_current_span("log_error") as span:
                error_data = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "error_type": type(error).__name__,
                    "error_message": str(error),
                    "traceback": traceback.format_exc(),
                    "context": context or {}
                }
                
                # תיעוד השגיאה
                logging.error(
                    f"Error occurred: {error_data['error_type']}: {error_data['error_message']}"
                )
                if context:
                    logging.error(f"Context: {json.dumps(context)}")
                logging.error(f"Traceback: {error_data['traceback']}")
                
                # עדכון מטריקות
                self.error_counter.add(1, {"error_type": error_data['error_type']})
                
                # שליחת התראה אם נדרש
                if alert:
                    await self._send_alert(error_data)
                    
                span.set_status(Status(StatusCode.ERROR))
                span.set_attribute("error.type", error_data['error_type'])
                
        except Exception as e:
            logging.error(f"Failed to log error: {str(e)}")

    async def log_security_event(
        self,
        event_type: str,
        details: Dict,
        alert_level: str = "INFO"
    ):
        """תיעוד אירוע אבטחה"""
        try:
            with self.tracer.start_as_current_span("log_security_event") as span:
                event_data = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "type": event_type,
                    "details": details,
                    "level": alert_level
                }
                
                # תיעוד האירוע
                logging.info(f"Security event: {json.dumps(event_data)}")
                
                # שליחת התראה אם האירוע חמור מספיק
                if self.alert_levels.get(alert_level, 0) >= self.alert_levels["WARNING"]:
                    await self._send_alert(
                        event_data,
                        subject="Security Alert",
                        alert_type="security"
                    )
                    
                span.set_status(Status(StatusCode.OK))
                
        except Exception as e:
            logging.error(f"Failed to log security event: {str(e)}")

    async def _send_alert(
        self,
        data: Dict,
        subject: Optional[str] = None,
        alert_type: str = "error"
    ):
        """שליחת התראה בערוצים השונים"""
        try:
            # הכנת הודעה
            message = self._format_alert_message(data, subject, alert_type)
            
            # שליחה במקביל לכל הערוצים המוגדרים
            tasks = []
            
            if self.alert_urls["teams_webhook"]:
                tasks.append(
                    self._send_teams_alert(message)
                )
            
            if self.alert_urls["slack_webhook"]:
                tasks.append(
                    self._send_slack_alert(message)
                )
            
            if self.alert_urls["email_api"]:
                tasks.append(
                    self._send_email_alert(message, subject or "System Alert")
                )
            
            await asyncio.gather(*tasks)
            
        except Exception as e:
            logging.error(f"Failed to send alert: {str(e)}")

    def _format_alert_message(
        self,
        data: Dict,
        subject: Optional[str] = None,
        alert_type: str = "error"
    ) -> Dict:
        """עיצוב הודעת ההתראה"""
        if alert_type == "error":
            return {
                "title": subject or f"Error Alert: {data['error_type']}",
                "text": (
                    f"Error: {data['error_message']}\n"
                    f"Time: {data['timestamp']}\n"
                    f"Context: {json.dumps(data.get('context', {}), indent=2)}\n"
                    f"Traceback: {data['traceback']}"
                ),
                "color": "red",
                "priority": "high"
            }
        elif alert_type == "security":
            return {
                "title": subject,
                "text": (
                    f"Security Event: {data['type']}\n"
                    f"Level: {data['level']}\n"
                    f"Time: {data['timestamp']}\n"
                    f"Details: {json.dumps(data['details'], indent=2)}"
                ),
                "color": "yellow",
                "priority": "medium"
            }
        else:
            return {
                "title": subject or "System Alert",
                "text": json.dumps(data, indent=2),
                "color": "blue",
                "priority": "low"
            }

    async def _send_teams_alert(self, message: Dict):
        """שליחת התראה ל-Microsoft Teams"""
        if not self.alert_urls["teams_webhook"]:
            return
            
        try:
            teams_message = {
                "@type": "MessageCard",
                "@context": "https://schema.org/extensions",
                "summary": message["title"],
                "themeColor": message["color"].replace("red", "ff0000").replace("yellow", "ffff00").replace("blue", "0000ff"),
                "title": message["title"],
                "sections": [{
                    "text": message["text"]
                }]
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.alert_urls["teams_webhook"],
                    json=teams_message
                ) as response:
                    if response.status != 200:
                        logging.error(f"Failed to send Teams alert: {await response.text()}")
                        
        except Exception as e:
            logging.error(f"Error sending Teams alert: {str(e)}")

    async def _send_slack_alert(self, message: Dict):
        """שליחת התראה ל-Slack"""
        if not self.alert_urls["slack_webhook"]:
            return
            
        try:
            slack_message = {
                "attachments": [{
                    "fallback": message["title"],
                    "color": message["color"],
                    "title": message["title"],
                    "text": message["text"],
                    "footer": "AI Agents Platform"
                }]
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.alert_urls["slack_webhook"],
                    json=slack_message
                ) as response:
                    if response.status != 200:
                        logging.error(f"Failed to send Slack alert: {await response.text()}")
                        
        except Exception as e:
            logging.error(f"Error sending Slack alert: {str(e)}")

    async def _send_email_alert(self, message: Dict, subject: str):
        """שליחת התראה במייל"""
        if not self.alert_urls["email_api"]:
            return
            
        try:
            email_data = {
                "subject": subject,
                "body": message["text"],
                "priority": message["priority"]
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.alert_urls["email_api"],
                    json=email_data
                ) as response:
                    if response.status != 200:
                        logging.error(f"Failed to send email alert: {await response.text()}")
                        
        except Exception as e:
            logging.error(f"Error sending email alert: {str(e)}")
# src/utils/alert_system.py

from typing import Dict, List, Optional
from datetime import datetime, timedelta
import asyncio
import logging
from dataclasses import dataclass
from enum import Enum
import aiohttp
from bs4 import BeautifulSoup

class AlertPriority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class LegalUpdate:
    source: str
    title: str
    content: str
    url: str
    date: datetime
    category: str
    priority: AlertPriority
    metadata: Optional[Dict] = None

class AlertSystem:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.sources = {
            "court_rulings": "https://supreme.court.gov.il/",
            "laws": "https://main.knesset.gov.il/",
            "execution_office": "https://www.gov.il/he/departments/execution_office"
        }
        self.update_intervals = {
            "court_rulings": 3600,  # שעה
            "laws": 86400,          # יום
            "execution_office": 3600 # שעה
        }
        self.last_check = {}
        self.subscribers = set()

    async def start(self):
        """התחלת מערכת ההתראות"""
        for source in self.sources:
            asyncio.create_task(self._monitor_source(source))
        self.logger.info("Alert system started")

    async def subscribe(self, callback, filters: Optional[Dict] = None):
        """הרשמה לקבלת התראות"""
        self.subscribers.add((callback, filters))

    async def unsubscribe(self, callback):
        """ביטול הרשמה להתראות"""
        self.subscribers = {(cb, f) for cb, f in self.subscribers if cb != callback}

    async def _monitor_source(self, source: str):
        """מעקב אחר מקור מידע"""
        while True:
            try:
                updates = await self._check_source(source)
                if updates:
                    await self._process_updates(updates)
                await asyncio.sleep(self.update_intervals[source])
            except Exception as e:
                self.logger.error(f"Error monitoring {source}: {str(e)}")
                await asyncio.sleep(60)

    async def _check_source(self, source: str) -> List[LegalUpdate]:
        """בדיקת מקור מידע לעדכונים"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.sources[source]) as response:
                    if response.status == 200:
                        content = await response.text()
                        updates = await self._parse_updates(source, content)
                        return [u for u in updates if self._is_new_update(u)]
            return []
        except Exception as e:
            self.logger.error(f"Error checking {source}: {str(e)}")
            return []

    async def _parse_updates(self, source: str, content: str) -> List[LegalUpdate]:
        """ניתוח תוכן לעדכונים"""
        try:
            soup = BeautifulSoup(content, 'html.parser')
            updates = []

            if source == "court_rulings":
                updates = await self._parse_court_rulings(soup)
            elif source == "laws":
                updates = await self._parse_laws(soup)
            elif source == "execution_office":
                updates = await self._parse_execution_office(soup)

            return updates
        except Exception as e:
            self.logger.error(f"Error parsing {source}: {str(e)}")
            return []

    async def _process_updates(self, updates: List[LegalUpdate]):
        """עיבוד והפצת עדכונים"""
        for update in updates:
            for callback, filters in self.subscribers:
                if self._should_notify(update, filters):
                    try:
                        await callback(update)
                    except Exception as e:
                        self.logger.error(f"Error notifying subscriber: {str(e)}")

    async def _parse_court_rulings(self, soup) -> List[LegalUpdate]:
        """ניתוח פסקי דין"""
        updates = []
        for ruling in soup.find_all('div', class_='ruling'):
            try:
                update = LegalUpdate(
                    source="court_rulings",
                    title=ruling.find('h2').text.strip(),
                    content=ruling.find('div', class_='content').text.strip(),
                    url=ruling.find('a')['href'],
                    date=datetime.now(),
                    category="פסיקה",
                    priority=self._determine_priority(ruling),
                    metadata={"court": "עליון"}
                )
                updates.append(update)
            except Exception as e:
                self.logger.error(f"Error parsing ruling: {str(e)}")
        return updates

    async def _parse_laws(self, soup) -> List[LegalUpdate]:
        """ניתוח חקיקה"""
        updates = []
        for law in soup.find_all('div', class_='law'):
            try:
                update = LegalUpdate(
                    source="laws",
                    title=law.find('h2').text.strip(),
                    content=law.find('div', class_='content').text.strip(),
                    url=law.find('a')['href'],
                    date=datetime.now(),
                    category="חקיקה",
                    priority=AlertPriority.HIGH,
                    metadata={"type": "חוק"}
                )
                updates.append(update)
            except Exception as e:
                self.logger.error(f"Error parsing law: {str(e)}")
        return updates

    async def _parse_execution_office(self, soup) -> List[LegalUpdate]:
        """ניתוח עדכוני הוצאה לפועל"""
        updates = []
        for update in soup.find_all('div', class_='update'):
            try:
                update = LegalUpdate(
                    source="execution_office",
                    title=update.find('h2').text.strip(),
                    content=update.find('div', class_='content').text.strip(),
                    url=update.find('a')['href'],
                    date=datetime.now(),
                    category="הוצאה לפועל",
                    priority=self._determine_priority(update),
                    metadata={"type": "הנחיה"}
                )
                updates.append(update)
            except Exception as e:
                self.logger.error(f"Error parsing update: {str(e)}")
        return updates

    def _determine_priority(self, element) -> AlertPriority:
        """קביעת עדיפות להתראה"""
        try:
            content = element.text.lower()
            
            # מילות מפתח לעדיפות גבוהה
            high_priority = [
                "דחוף", "חירום", "מיידי", "חובה",
                "שינוי מהותי", "תיקון משמעותי"
            ]
            
            # מילות מפתח לעדיפות בינונית
            medium_priority = [
                "עדכון", "שינוי", "הנחיה חדשה",
                "הבהרה", "תיקון"
            ]

            for word in high_priority:
                if word in content:
                    return AlertPriority.HIGH
                    
            for word in medium_priority:
                if word in content:
                    return AlertPriority.MEDIUM
                    
            return AlertPriority.LOW
            
        except Exception as e:
            self.logger.error(f"Error determining priority: {str(e)}")
            return AlertPriority.LOW

    def _is_new_update(self, update: LegalUpdate) -> bool:
        """בדיקה האם העדכון חדש"""
        last_check = self.last_check.get(update.source)
        if not last_check:
            return True
        return update.date > last_check

    def _should_notify(self, update: LegalUpdate, filters: Optional[Dict]) -> bool:
        """בדיקה האם יש להתריע על העדכון"""
        if not filters:
            return True
            
        # בדיקת קטגוריה
        if 'categories' in filters and update.category not in filters['categories']:
            return False
            
        # בדיקת עדיפות
        if 'min_priority' in filters:
            min_priority = AlertPriority(filters['min_priority'])
            if update.priority.value < min_priority.value:
                return False
                
        # בדיקת מקור
        if 'sources' in filters and update.source not in filters['sources']:
            return False
            
        return True

    async def get_recent_updates(
        self,
        hours: int = 24,
        filters: Optional[Dict] = None
    ) -> List[LegalUpdate]:
        """קבלת עדכונים אחרונים"""
        try:
            updates = []
            for source in self.sources:
                source_updates = await self._check_source(source)
                if filters:
                    source_updates = [
                        u for u in source_updates
                        if self._should_notify(u, filters)
                    ]
                updates.extend(source_updates)
            
            # סינון לפי זמן
            cutoff = datetime.now() - timedelta(hours=hours)
            updates = [u for u in updates if u.date > cutoff]
            
            return sorted(updates, key=lambda x: x.date, reverse=True)
            
        except Exception as e:
            self.logger.error(f"Error getting recent updates: {str(e)}")
            return []
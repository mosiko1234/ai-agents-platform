# src/utils/legal_data_fetcher.py

from typing import Dict, List, Optional, Union
import aiohttp
import asyncio
import logging
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import json
from dataclasses import dataclass
import re

@dataclass
class LegalDocument:
    """מבנה נתונים למסמך משפטי"""
    doc_id: str
    title: str
    type: str  # חקיקה, פסיקה, תקדים
    content: str
    date: datetime
    source: str
    url: Optional[str] = None
    metadata: Dict = None

class LegalDataFetcher:
    """מנהל התחברות למאגרי מידע משפטיים"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.session = None
        self.rate_limiters = {}
        
        # הגדרת מקורות מידע
        self.sources = {
            "nevo": {
                "base_url": "https://www.nevo.co.il/api/",
                "rate_limit": 60,  # requests per minute
                "credentials": None
            },
            "takdin": {
                "base_url": "https://www.takdin.co.il/api/",
                "rate_limit": 60,
                "credentials": None
            },
            "psakdin": {
                "base_url": "https://www.psakdin.co.il/api/",
                "rate_limit": 60,
                "credentials": None
            },
            "court": {
                "base_url": "https://supreme.court.gov.il/api/",
                "rate_limit": 60,
                "credentials": None
            }
        }

    async def initialize(self, credentials: Dict[str, Dict]):
        """אתחול החיבורים למאגרי המידע"""
        try:
            self.session = aiohttp.ClientSession()
            
            # הגדרת מגבלות קצב לכל מקור
            for source, config in self.sources.items():
                self.rate_limiters[source] = asyncio.Semaphore(
                    config["rate_limit"]
                )
                if source in credentials:
                    self.sources[source]["credentials"] = credentials[source]
            
            self.logger.info("Legal data fetcher initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize legal data fetcher: {str(e)}")
            raise

    async def close(self):
        """סגירת חיבורים"""
        if self.session:
            await self.session.close()

    async def search_case_law(
        self,
        query: str,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        category: Optional[str] = None,
        max_results: int = 10
    ) -> List[LegalDocument]:
        """חיפוש פסקי דין"""
        try:
            results = []
            search_tasks = []
            
            # חיפוש בכל המקורות במקביל
            for source in self.sources:
                search_tasks.append(
                    self._search_source(
                        source,
                        "case_law",
                        query,
                        date_from,
                        date_to,
                        category
                    )
                )
            
            # איסוף תוצאות מכל המקורות
            all_results = await asyncio.gather(*search_tasks)
            
            # מיזוג ומיון התוצאות
            for source_results in all_results:
                results.extend(source_results)
            
            # מיון לפי תאריך
            results.sort(key=lambda x: x.date, reverse=True)
            
            return results[:max_results]
            
        except Exception as e:
            self.logger.error(f"Error searching case law: {str(e)}")
            raise

    async def get_legislation(
        self,
        law_name: str,
        section: Optional[str] = None
    ) -> Optional[LegalDocument]:
        """אחזור חקיקה"""
        try:
            for source, config in self.sources.items():
                async with self.rate_limiters[source]:
                    try:
                        url = f"{config['base_url']}legislation/search"
                        params = {"name": law_name}
                        if section:
                            params["section"] = section
                        
                        headers = self._get_auth_headers(source)
                        
                        async with self.session.get(
                            url,
                            params=params,
                            headers=headers
                        ) as response:
                            if response.status == 200:
                                data = await response.json()
                                return self._parse_legislation(data, source)
                                
                    except Exception as e:
                        self.logger.error(
                            f"Error fetching legislation from {source}: {str(e)}"
                        )
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting legislation: {str(e)}")
            raise

    async def get_precedents(
        self,
        category: str,
        limit: int = 5
    ) -> List[LegalDocument]:
        """אחזור תקדימים משפטיים"""
        try:
            results = []
            for source, config in self.sources.items():
                async with self.rate_limiters[source]:
                    try:
                        url = f"{config['base_url']}precedents/{category}"
                        headers = self._get_auth_headers(source)
                        
                        async with self.session.get(
                            url,
                            params={"limit": limit},
                            headers=headers
                        ) as response:
                            if response.status == 200:
                                data = await response.json()
                                results.extend(
                                    self._parse_precedents(data, source)
                                )
                                
                    except Exception as e:
                        self.logger.error(
                            f"Error fetching precedents from {source}: {str(e)}"
                        )
            
            return sorted(results, key=lambda x: x.date, reverse=True)[:limit]
            
        except Exception as e:
            self.logger.error(f"Error getting precedents: {str(e)}")
            raise

    async def get_recent_updates(
        self,
        hours: int = 24
    ) -> Dict[str, List[LegalDocument]]:
        """אחזור עדכונים אחרונים"""
        try:
            since = datetime.utcnow() - timedelta(hours=hours)
            updates = {
                "legislation": [],
                "case_law": [],
                "precedents": []
            }
            
            # איסוף עדכונים מכל המקורות
            for source, config in self.sources.items():
                async with self.rate_limiters[source]:
                    try:
                        url = f"{config['base_url']}updates"
                        headers = self._get_auth_headers(source)
                        
                        async with self.session.get(
                            url,
                            params={"since": since.isoformat()},
                            headers=headers
                        ) as response:
                            if response.status == 200:
                                data = await response.json()
                                for doc_type, docs in data.items():
                                    if doc_type in updates:
                                        updates[doc_type].extend(
                                            self._parse_updates(docs, source)
                                        )
                                
                    except Exception as e:
                        self.logger.error(
                            f"Error fetching updates from {source}: {str(e)}"
                        )
            
            # מיון לפי תאריך
            for doc_type in updates:
                updates[doc_type].sort(key=lambda x: x.date, reverse=True)
            
            return updates
            
        except Exception as e:
            self.logger.error(f"Error getting updates: {str(e)}")
            raise

    async def _search_source(
        self,
        source: str,
        doc_type: str,
        query: str,
        date_from: Optional[datetime],
        date_to: Optional[datetime],
        category: Optional[str]
    ) -> List[LegalDocument]:
        """חיפוש במקור מידע ספציפי"""
        async with self.rate_limiters[source]:
            try:
                url = f"{self.sources[source]['base_url']}{doc_type}/search"
                params = {"q": query}
                
                if date_from:
                    params["from"] = date_from.isoformat()
                if date_to:
                    params["to"] = date_to.isoformat()
                if category:
                    params["category"] = category
                
                headers = self._get_auth_headers(source)
                
                async with self.session.get(
                    url,
                    params=params,
                    headers=headers
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_search_results(data, source)
                    return []
                    
            except Exception as e:
                self.logger.error(
                    f"Error searching {source}: {str(e)}"
                )
                return []

    def _get_auth_headers(self, source: str) -> Dict[str, str]:
        """יצירת headers לאימות"""
        credentials = self.sources[source]["credentials"]
        if not credentials:
            return {}
            
        return {
            "Authorization": f"Bearer {credentials.get('api_key')}",
            "User-Agent": "LegalBot/1.0"
        }

    def _parse_search_results(
        self,
        data: Dict,
        source: str
    ) -> List[LegalDocument]:
        """עיבוד תוצאות חיפוש"""
        results = []
        for item in data.get("results", []):
            try:
                doc = LegalDocument(
                    doc_id=item.get("id"),
                    title=item.get("title"),
                    type=item.get("type"),
                    content=item.get("content"),
                    date=datetime.fromisoformat(item.get("date")),
                    source=source,
                    url=item.get("url"),
                    metadata=item.get("metadata")
                )
                results.append(doc)
            except Exception as e:
                self.logger.error(f"Error parsing document: {str(e)}")
                continue
        
        return results

    def _parse_legislation(self, data: Dict, source: str) -> Optional[LegalDocument]:
        """עיבוד נתוני חקיקה"""
        try:
            return LegalDocument(
                doc_id=data.get("id"),
                title=data.get("name"),
                type="legislation",
                content=data.get("content"),
                date=datetime.fromisoformat(data.get("last_updated")),
                source=source,
                url=data.get("url"),
                metadata=data.get("metadata")
            )
        except Exception as e:
            self.logger.error(f"Error parsing legislation: {str(e)}")
            return None

    def _parse_precedents(
        self,
        data: List[Dict],
        source: str
    ) -> List[LegalDocument]:
        """עיבוד נתוני תקדימים"""
        results = []
        for item in data:
            try:
                doc = LegalDocument(
                    doc_id=item.get("id"),
                    title=item.get("title"),
                    type="precedent",
                    content=item.get("content"),
                    date=datetime.fromisoformat(item.get("date")),
                    source=source,
                    url=item.get("url"),
                    metadata=item.get("metadata")
                )
                results.append(doc)
            except Exception as e:
                self.logger.error(f"Error parsing precedent: {str(e)}")
                continue
        
        return results
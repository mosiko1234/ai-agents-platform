# src/agents/shimon/knowledge.py

from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging
import aiohttp
import asyncio
from bs4 import BeautifulSoup
import json
from core.exceptions import KnowledgeBaseError

class LegalKnowledgeManager:
    """Manage legal knowledge for Shimon agent"""
    
    def __init__(self, cosmos_client):
        self.cosmos_client = cosmos_client
        self.logger = logging.getLogger("shimon.knowledge")
        self.last_update = datetime.utcnow()
        
        # מקורות מידע משפטיים
        self.sources = {
            "court_rulings": [
                "https://supreme.court.gov.il/",
                "https://www.nevo.co.il/",
                "https://www.takdin.co.il/",
                "https://www.psakdin.co.il/"
            ],
            "legal_updates": [
                "https://www.gov.il/he/departments/execution_office",
                "https://www.justice.gov.il/Units/ExecutionOffice/",
                "https://www.judiciary.gov.il/"
            ],
            "bankruptcy": [
                "https://www.gov.il/he/departments/official-receiver",
                "https://www.justice.gov.il/Units/ApotroposKlali/"
            ]
        }
        
        # טבלאות במסד הנתונים
        self.collections = {
            "knowledge": "legal_knowledge",
            "rulings": "case_law",
            "guidelines": "legal_guidelines",
            "templates": "legal_templates"
        }

    async def update_all_knowledge(self) -> None:
        """עדכון כל מקורות הידע"""
        try:
            update_tasks = [
                self._update_court_rulings(),
                self._update_legal_guidelines(),
                self._update_bankruptcy_info(),
                self._update_execution_procedures()
            ]
            
            await asyncio.gather(*update_tasks)
            self.last_update = datetime.utcnow()
            self.logger.info("Successfully updated all legal knowledge")
            
        except Exception as e:
            self.logger.error(f"Failed to update knowledge: {str(e)}")
            raise KnowledgeBaseError(str(e))

    async def _update_court_rulings(self) -> None:
        """עדכון פסקי דין חדשים"""
        async with aiohttp.ClientSession() as session:
            for source in self.sources["court_rulings"]:
                try:
                    async with session.get(source) as response:
                        if response.status == 200:
                            html = await response.text()
                            rulings = await self._parse_rulings(html, source)
                            await self._store_rulings(rulings)
                except Exception as e:
                    self.logger.error(f"Error fetching rulings from {source}: {str(e)}")

    async def _parse_rulings(self, html: str, source: str) -> List[Dict]:
        """ניתוח פסקי דין מתוך HTML"""
        rulings = []
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # התאמה לפי מקור המידע
            if "supreme.court" in source:
                rulings = self._parse_supreme_court(soup)
            elif "nevo" in source:
                rulings = self._parse_nevo(soup)
            elif "takdin" in source:
                rulings = self._parse_takdin(soup)
            elif "psakdin" in source:
                rulings = self._parse_psakdin(soup)
            
            return rulings
            
        except Exception as e:
            self.logger.error(f"Error parsing rulings from {source}: {str(e)}")
            return []

    def _parse_supreme_court(self, soup: BeautifulSoup) -> List[Dict]:
        """ניתוח פסקי דין מאתר בית המשפט העליון"""
        rulings = []
        for ruling in soup.find_all('div', class_='ruling-item'):
            try:
                ruling_data = {
                    'id': ruling.get('data-id', str(datetime.utcnow().timestamp())),
                    'title': ruling.find('h2').text.strip(),
                    'date': ruling.find('span', class_='date').text.strip(),
                    'content': ruling.find('div', class_='content').text.strip(),
                    'judges': [j.text.strip() for j in ruling.find_all('span', class_='judge')],
                    'categories': [c.text.strip() for c in ruling.find_all('span', class_='category')],
                    'source': 'supreme_court',
                    'url': ruling.find('a')['href'],
                    'timestamp': datetime.utcnow().isoformat()
                }
                rulings.append(ruling_data)
            except Exception as e:
                self.logger.error(f"Error parsing supreme court ruling: {str(e)}")
                continue
        return rulings

    async def _store_rulings(self, rulings: List[Dict]) -> None:
        """שמירת פסקי דין במסד הנתונים"""
        try:
            database = self.cosmos_client.get_database_client("ai_agents")
            container = database.get_container_client(self.collections["rulings"])
            
            for ruling in rulings:
                # בדיקה האם פסק הדין כבר קיים
                query = f"SELECT * FROM c WHERE c.source_id = '{ruling['id']}'"
                existing = list(container.query_items(
                    query=query,
                    enable_cross_partition_query=True
                ))
                
                if not existing:
                    document = {
                        'id': str(datetime.utcnow().timestamp()),
                        'source_id': ruling['id'],
                        'type': 'ruling',
                        'agent_id': 'shimon',
                        'content': ruling,
                        'timestamp': datetime.utcnow().isoformat(),
                        'categories': ruling.get('categories', []),
                        'relevance_score': await self._calculate_ruling_relevance(ruling)
                    }
                    await container.create_item(body=document)
                    
        except Exception as e:
            self.logger.error(f"Error storing rulings: {str(e)}")
            raise

    async def _calculate_ruling_relevance(self, ruling: Dict) -> float:
        """חישוב רלוונטיות של פסק דין"""
        try:
            relevance = 0.5  # ציון בסיסי
            
            # בדיקת תאריך - פסקי דין חדשים יותר מקבלים ציון גבוה יותר
            ruling_date = datetime.fromisoformat(ruling['date'])
            days_old = (datetime.utcnow() - ruling_date).days
            if days_old < 30:  # חודש אחרון
                relevance += 0.3
            elif days_old < 90:  # 3 חודשים אחרונים
                relevance += 0.2
            elif days_old < 365:  # שנה אחרונה
                relevance += 0.1
            
            # בדיקת קטגוריות רלוונטיות
            relevant_categories = ['הוצאה לפועל', 'עיקולים', 'פשיטת רגל', 'חדלות פירעון']
            for category in ruling.get('categories', []):
                if any(rc.lower() in category.lower() for rc in relevant_categories):
                    relevance += 0.1
            
            # בדיקת תוכן
            relevant_terms = ['הוצאה לפועל', 'עיקול', 'חוב', 'נושה', 'חייב', 'פשיטת רגל']
            content = ruling.get('content', '').lower()
            for term in relevant_terms:
                if term in content:
                    relevance += 0.05
            
            return min(relevance, 1.0)
            
        except Exception as e:
            self.logger.error(f"Error calculating ruling relevance: {str(e)}")
            return 0.5

    async def _update_legal_guidelines(self) -> None:
        """עדכון הנחיות משפטיות"""
        try:
            database = self.cosmos_client.get_database_client("ai_agents")
            container = database.get_container_client(self.collections["guidelines"])
            
            async with aiohttp.ClientSession() as session:
                for source in self.sources["legal_updates"]:
                    try:
                        async with session.get(source) as response:
                            if response.status == 200:
                                html = await response.text()
                                guidelines = await self._parse_guidelines(html)
                                await self._store_guidelines(guidelines, container)
                    except Exception as e:
                        self.logger.error(f"Error updating guidelines from {source}: {str(e)}")
                        continue
                        
        except Exception as e:
            self.logger.error(f"Error updating legal guidelines: {str(e)}")
            raise

    async def get_relevant_knowledge(self, query: str, category: str) -> Dict:
        """אחזור ידע רלוונטי לשאלה"""
        try:
            database = self.cosmos_client.get_database_client("ai_agents")
            
            # אחזור פסקי דין רלוונטיים
            rulings_container = database.get_container_client(self.collections["rulings"])
            rulings_query = f"""
            SELECT * FROM c
            WHERE c.type = 'ruling'
            AND c.categories ARRAY_CONTAINS '{category}'
            ORDER BY c.relevance_score DESC
            OFFSET 0 LIMIT 5
            """
            
            rulings = []
            async for item in rulings_container.query_items(
                query=rulings_query,
                enable_cross_partition_query=True
            ):
                rulings.append(item)
            
            # אחזור הנחיות רלוונטיות
            guidelines_container = database.get_container_client(self.collections["guidelines"])
            guidelines_query = f"""
            SELECT * FROM c
            WHERE c.type = 'guideline'
            AND c.category = '{category}'
            ORDER BY c._ts DESC
            OFFSET 0 LIMIT 3
            """
            
            guidelines = []
            async for item in guidelines_container.query_items(
                query=guidelines_query,
                enable_cross_partition_query=True
            ):
                guidelines.append(item)
            
            return {
                "rulings": rulings,
                "guidelines": guidelines,
                "last_update": self.last_update.isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting relevant knowledge: {str(e)}")
            raise KnowledgeBaseError(str(e))
# tests/test_legal_system.py

import pytest
import asyncio
from datetime import datetime
import json
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, List

from src.utils.legal_analyzer import LegalTextAnalyzer
from src.utils.legal_data_fetcher import LegalDataFetcher, LegalDocument
from src.utils.gpt_manager import GPTManager
from src.utils.storage import StorageManager
from src.core.exceptions import (
    GPTError, IntegrationError, KnowledgeBaseError
)

@pytest.fixture
async def legal_analyzer():
    """Fixture for LegalTextAnalyzer"""
    analyzer = LegalTextAnalyzer()
    return analyzer

@pytest.fixture
async def gpt_manager():
    """Fixture for GPTManager"""
    manager = GPTManager()
    await manager.initialize(
        api_key="test_key",
        api_base="test_base",
        api_version="test_version"
    )
    return manager

@pytest.fixture
async def storage_manager():
    """Fixture for StorageManager"""
    manager = StorageManager()
    await manager.initialize(
        cosmos_connection_string="test_connection",
        redis_url="redis://localhost"
    )
    return manager

@pytest.fixture
async def legal_data_fetcher():
    """Fixture for LegalDataFetcher"""
    fetcher = LegalDataFetcher()
    credentials = {
        "nevo": {"api_key": "test_key"},
        "takdin": {"api_key": "test_key"}
    }
    await fetcher.initialize(credentials)
    return fetcher

# Tests for LegalTextAnalyzer
class TestLegalAnalyzer:
    """בדיקות למנתח הטקסט המשפטי"""

    @pytest.mark.asyncio
    async def test_identify_category(self, legal_analyzer):
        """בדיקת זיהוי קטגוריה"""
        # Test execution office category
        text = "האם ניתן לבצע עיקול על חשבון הבנק במסגרת תיק הוצאה לפועל?"
        category, confidence = await legal_analyzer._identify_category(text)
        assert category == "execution"
        assert confidence > 0.7

        # Test debt collection category
        text = "מה הם ההליכים האפשריים לגביית חוב מחייב שמסרב לשלם?"
        category, confidence = await legal_analyzer._identify_category(text)
        assert category == "debt_collection"
        assert confidence > 0.7

    @pytest.mark.asyncio
    async def test_extract_entities(self, legal_analyzer):
        """בדיקת חילוץ ישויות"""
        text = """
        בתיק מספר 1234/21 הוגשה בקשה לעיקול בסך 50,000 ₪.
        התיק נפתח בתאריך 01/01/2024 בהתאם לסעיף 7(א) לחוק.
        """
        entities = await legal_analyzer._extract_entities(text)
        
        assert any("1234/21" in e for e in entities)  # מספר תיק
        assert any("50,000" in e for e in entities)   # סכום
        assert any("01/01/2024" in e for e in entities)  # תאריך
        assert any("7(א)" in e for e in entities)     # סעיף חוק

    @pytest.mark.asyncio
    async def test_analyze_sentiment(self, legal_analyzer):
        """בדיקת ניתוח סנטימנט"""
        # Positive text
        text = "הבקשה התקבלה והעיקול אושר לביצוע."
        sentiment = legal_analyzer._analyze_sentiment(text)
        assert sentiment > 0

        # Negative text
        text = "הבקשה נדחתה עקב פגמים מהותיים."
        sentiment = legal_analyzer._analyze_sentiment(text)
        assert sentiment < 0

# Tests for GPTManager
class TestGPTManager:
    """בדיקות למנהל ה-GPT"""

    @pytest.mark.asyncio
    async def test_get_response(self, gpt_manager):
        """בדיקת קבלת תשובה"""
        query = "מהם התנאים להגשת בקשת עיקול?"
        context = {"laws": ["חוק ההוצאה לפועל"]}
        
        with patch('openai.AsyncAzureOpenAI.chat.completions.create', new_callable=AsyncMock) as mock_create:
            mock_create.return_value.choices = [
                Mock(message=Mock(content="תשובה לדוגמה"))
            ]
            
            response = await gpt_manager.get_response(query, context)
            assert "content" in response
            assert "references" in response
            assert "confidence" in response

    @pytest.mark.asyncio
    async def test_analyze_legal_document(self, gpt_manager):
        """בדיקת ניתוח מסמך משפטי"""
        document = """
        פסק דין בתיק 1234/21
        בהתאם לסעיף 7 לחוק, הוחלט לאשר את הבקשה...
        """
        
        with patch('openai.AsyncAzureOpenAI.chat.completions.create', new_callable=AsyncMock) as mock_create:
            mock_create.return_value.choices = [
                Mock(message=Mock(content="ניתוח לדוגמה"))
            ]
            
            analysis = await gpt_manager.analyze_legal_document(document)
            assert "summary" in analysis
            assert "key_points" in analysis
            assert "references" in analysis

# Tests for LegalDataFetcher
class TestLegalDataFetcher:
    """בדיקות למנהל אחזור המידע המשפטי"""

    @pytest.mark.asyncio
    async def test_search_case_law(self, legal_data_fetcher):
        """בדיקת חיפוש פסקי דין"""
        with patch('aiohttp.ClientSession.get', new_callable=AsyncMock) as mock_get:
            mock_get.return_value.__aenter__.return_value.status = 200
            mock_get.return_value.__aenter__.return_value.json = AsyncMock(
                return_value={"results": [
                    {
                        "id": "123",
                        "title": "פסק דין לדוגמה",
                        "content": "תוכן לדוגמה",
                        "date": "2024-01-01T00:00:00"
                    }
                ]}
            )
            
            results = await legal_data_fetcher.search_case_law(
                "עיקול",
                max_results=1
            )
            assert len(results) == 1
            assert results[0].title == "פסק דין לדוגמה"

    @pytest.mark.asyncio
    async def test_get_legislation(self, legal_data_fetcher):
        """בדיקת אחזור חקיקה"""
        with patch('aiohttp.ClientSession.get', new_callable=AsyncMock) as mock_get:
            mock_get.return_value.__aenter__.return_value.status = 200
            mock_get.return_value.__aenter__.return_value.json = AsyncMock(
                return_value={
                    "id": "123",
                    "name": "חוק ההוצאה לפועל",
                    "content": "תוכן החוק",
                    "last_updated": "2024-01-01T00:00:00"
                }
            )
            
            doc = await legal_data_fetcher.get_legislation(
                "חוק ההוצאה לפועל",
                section="7"
            )
            assert doc.title == "חוק ההוצאה לפועל"
            assert doc.type == "legislation"

# Tests for StorageManager
class TestStorageManager:
    """בדיקות למנהל האחסון"""

    @pytest.mark.asyncio
    async def test_store_agent_knowledge(self, storage_manager):
        """בדיקת שמירת ידע"""
        knowledge = {
            "type": "legal_precedent",
            "content": "תוכן לדוגמה"
        }
        
        with patch('azure.cosmos.aio.ContainerProxy.upsert_item', new_callable=AsyncMock) as mock_upsert:
            mock_upsert.return_value = {"id": "123"}
            
            await storage_manager.store_agent_knowledge(
                "shimon",
                "precedents",
                knowledge
            )
            mock_upsert.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_agent_knowledge(self, storage_manager):
        """בדיקת אחזור ידע"""
        with patch('azure.cosmos.aio.ContainerProxy.query_items', new_callable=AsyncMock) as mock_query:
            mock_query.return_value = AsyncMock()
            mock_query.return_value.__aiter__.return_value = [
                {"data": {"content": "תוכן לדוגמה"}}
            ]
            
            knowledge = await storage_manager.get_agent_knowledge(
                "shimon",
                "precedents"
            )
            assert knowledge is not None
            assert "content" in knowledge

if __name__ == "__main__":
    pytest.main(["-v", "test_legal_system.py"])
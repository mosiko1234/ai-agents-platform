# src/utils/gpt_manager.py

from typing import Dict, List, Optional
import logging
from datetime import datetime
import json
import asyncio
from openai import AsyncAzureOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from core.exceptions import GPTError
from .legal_analyzer import LegalTextAnalyzer

class GPTManager:
    """מנהל תקשורת והגדרות GPT"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.client = None
        self.legal_analyzer = LegalTextAnalyzer()
        
        # הגדרת פרומפטים בסיסיים
        self.base_prompts = {
            "system": """אתה עוזר משפטי מומחה בתחום ההוצאה לפועל ואכיפת פסקי דין בישראל. 
            עליך לספק ייעוץ מקצועי, מדויק ומעודכן, תוך הסתמכות על החוק, פסיקה ותקדימים משפטיים.
            התשובות שלך צריכות להיות:
            1. מבוססות על חוק ופסיקה עדכניים
            2. מפורטות ומנומקות
            3. בשפה ברורה ומקצועית
            4. כוללות אסמכתאות והפניות
            5. מציינות הסתייגויות כשנדרש""",
            
            "execution": """בנושא הוצאה לפועל, עליך לציין:
            1. המסגרת החוקית הרלוונטית
            2. הליכים אפשריים ודרכי פעולה
            3. לוחות זמנים ומועדים חשובים
            4. עלויות ואגרות רלוונטיות
            5. טפסים ומסמכים נדרשים""",
            
            "debt_collection": """בנושא גביית חובות, התייחס ל:
            1. סוגי הליכי גבייה אפשריים
            2. זכויות וחובות הצדדים
            3. מגבלות על הליכי גבייה
            4. אפשרויות הסדר והליכים חלופיים
            5. השלכות והמלצות מעשיות""",
            
            "foreclosure": """בנושא עיקולים, פרט:
            1. סוגי העיקולים האפשריים
            2. תנאים להטלת עיקול
            3. הגנות וזכויות החייב
            4. הליכי מימוש עיקול
            5. עלויות ולוחות זמנים"""
        }
        
        # הגדרות מודל
        self.model_settings = {
            "default": {
                "model": "gpt-4",
                "temperature": 0.3,
                "max_tokens": 2000,
                "top_p": 0.9
            },
            "analysis": {
                "model": "gpt-4",
                "temperature": 0.1,
                "max_tokens": 500,
                "top_p": 0.95
            },
            "summary": {
                "model": "gpt-3.5-turbo",
                "temperature": 0.5,
                "max_tokens": 300,
                "top_p": 0.8
            }
        }

    async def initialize(self, api_key: str, api_base: str, api_version: str):
        """אתחול המנהל וחיבור ל-OpenAI"""
        try:
            self.client = AsyncAzureOpenAI(
                api_key=api_key,
                api_version=api_version,
                azure_endpoint=api_base
            )
            self.logger.info("GPT manager initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize GPT manager: {str(e)}")
            raise GPTError("Failed to initialize GPT connection")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def get_response(
        self,
        query: str,
        context: Dict,
        category: Optional[str] = None
    ) -> Dict:
        """קבלת תשובה מ-GPT"""
        try:
            # ניתוח השאלה
            if not category:
                category, _ = self.legal_analyzer._identify_category(query)
            
            # בניית הפרומפט
            messages = await self._build_prompt(query, category, context)
            
            # שליחה ל-GPT
            response = await self.client.chat.completions.create(
                messages=messages,
                **self.model_settings["default"]
            )
            
            # עיבוד התשובה
            processed_response = await self._process_response(
                response.choices[0].message.content,
                category
            )
            
            return {
                "content": processed_response["content"],
                "references": processed_response["references"],
                "category": category,
                "confidence": processed_response["confidence"],
                "metadata": {
                    "model": self.model_settings["default"]["model"],
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error getting GPT response: {str(e)}")
            raise GPTError(f"Failed to get response: {str(e)}")

    async def analyze_legal_document(self, text: str) -> Dict:
        """ניתוח מסמך משפטי"""
        try:
            messages = [
                {
                    "role": "system",
                    "content": """נתח את המסמך המשפטי וספק:
                    1. סיכום תמציתי
                    2. נקודות משפטיות מרכזיות
                    3. אסמכתאות ותקדימים
                    4. השלכות מעשיות"""
                },
                {"role": "user", "content": text}
            ]
            
            response = await self.client.chat.completions.create(
                messages=messages,
                **self.model_settings["analysis"]
            )
            
            return await self._process_analysis(response.choices[0].message.content)
            
        except Exception as e:
            self.logger.error(f"Error analyzing document: {str(e)}")
            raise GPTError(f"Failed to analyze document: {str(e)}")

    async def get_summary(self, text: str, context: Optional[Dict] = None) -> str:
        """קבלת תקציר משפטי"""
        try:
            messages = [
                {
                    "role": "system",
                    "content": "ספק תקציר תמציתי ומדויק של המסמך המשפטי"
                },
                {"role": "user", "content": text}
            ]
            
            if context:
                messages.append({
                    "role": "system",
                    "content": f"התייחס להקשר: {json.dumps(context, ensure_ascii=False)}"
                })
            
            response = await self.client.chat.completions.create(
                messages=messages,
                **self.model_settings["summary"]
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            self.logger.error(f"Error getting summary: {str(e)}")
            raise GPTError(f"Failed to get summary: {str(e)}")

    async def _build_prompt(
        self,
        query: str,
        category: str,
        context: Dict
    ) -> List[Dict]:
        """בניית פרומפט מותאם"""
        messages = [
            {"role": "system", "content": self.base_prompts["system"]}
        ]
        
        # הוספת פרומפט ספציפי לקטגוריה
        if category in self.base_prompts:
            messages.append({
                "role": "system",
                "content": self.base_prompts[category]
            })
        
        # הוספת הקשר
        if context:
            context_prompt = self._format_context(context)
            messages.append({
                "role": "system",
                "content": context_prompt
            })
        
        # הוספת השאלה
        messages.append({"role": "user", "content": query})
        
        return messages

    def _format_context(self, context: Dict) -> str:
        """עיצוב ההקשר לפרומפט"""
        context_parts = []
        
        if "laws" in context:
            context_parts.append(
                f"חוקים רלוונטיים:\n{json.dumps(context['laws'], ensure_ascii=False)}"
            )
        
        if "precedents" in context:
            context_parts.append(
                f"תקדימים רלוונטיים:\n{json.dumps(context['precedents'], ensure_ascii=False)}"
            )
        
        if "previous_cases" in context:
            context_parts.append(
                f"תיקים קודמים:\n{json.dumps(context['previous_cases'], ensure_ascii=False)}"
            )
        
        return "\n\n".join(context_parts)

    async def _process_response(self, response: str, category: str) -> Dict:
        """עיבוד תשובת GPT"""
        # חילוץ אסמכתאות
        references = self.legal_analyzer._extract_references(response)
        
        # חישוב ציון ביטחון
        confidence = await self._calculate_confidence(response, category)
        
        return {
            "content": response,
            "references": references,
            "confidence": confidence
        }

    async def _process_analysis(self, analysis: str) -> Dict:
        """עיבוד ניתוח משפטי"""
        try:
            # חלוקה לחלקים
            sections = analysis.split("\n\n")
            
            return {
                "summary": sections[0] if len(sections) > 0 else "",
                "key_points": sections[1] if len(sections) > 1 else "",
                "references": self.legal_analyzer._extract_references(analysis),
                "implications": sections[-1] if len(sections) > 2 else ""
            }
        except Exception as e:
            self.logger.error(f"Error processing analysis: {str(e)}")
            return {"error": str(e)}

    async def _calculate_confidence(self, response: str, category: str) -> float:
        """חישוב ציון ביטחון לתשובה"""
        try:
            score = 0.5  # ציון בסיסי
            
            # בדיקת אסמכתאות
            references = self.legal_analyzer._extract_references(response)
            if references:
                score += 0.2
            
            # בדיקת מונחים משפטיים
            legal_terms = self.legal_analyzer._identify_legal_terms(response)
            if len(legal_terms) > 5:
                score += 0.1
            
            # בדיקת מבנה התשובה
            if all(marker in response for marker in ["חוק", "פסיקה", "המלצה"]):
                score += 0.1
            
            # בדיקת התאמה לקטגוריה
            if category in self.base_prompts:
                category_terms = set(self.base_prompts[category].lower().split())
                response_terms = set(response.lower().split())
                overlap = len(category_terms.intersection(response_terms))
                if overlap > 5:
                    score += 0.1
            
            return min(score, 1.0)
            
        except Exception as e:
            self.logger.error(f"Error calculating confidence: {str(e)}")
            return 0.5
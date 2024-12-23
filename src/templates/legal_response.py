# src/templates/legal_response.py

from typing import Dict, List, Optional
import json
from datetime import datetime
from dataclasses import dataclass
import re

@dataclass
class LegalReference:
    """מבנה נתונים לאסמכתא משפטית"""
    type: str  # חוק, פסיקה, תקנה
    name: str  # שם האסמכתא
    reference: str  # הפניה מדויקת (סעיף, עמוד וכו')
    year: Optional[int] = None
    url: Optional[str] = None
    relevance_score: float = 1.0

class LegalResponseFormatter:
    """מעצב תשובות משפטיות"""
    
    def __init__(self):
        self.templates = self._load_templates()
        self.response_structure = {
            "פתיחה": self._format_introduction,
            "תשובה משפטית": self._format_legal_answer,
            "אסמכתאות": self._format_references,
            "המלצות מעשיות": self._format_recommendations,
            "הסתייגויות": self._format_disclaimers
        }

    def format_response(
        self,
        query: str,
        answer: str,
        references: List[LegalReference],
        category: str,
        recommendations: Optional[List[str]] = None,
        disclaimers: Optional[List[str]] = None
    ) -> str:
        """עיצוב תשובה מלאה"""
        try:
            response_parts = []
            
            # פתיחה
            response_parts.append(
                self._format_introduction(query, category)
            )
            
            # תשובה משפטית
            response_parts.append(
                self._format_legal_answer(answer)
            )
            
            # אסמכתאות
            if references:
                response_parts.append(
                    self._format_references(references)
                )
            
            # המלצות מעשיות
            if recommendations:
                response_parts.append(
                    self._format_recommendations(recommendations)
                )
            
            # הסתייגויות
            if disclaimers:
                response_parts.append(
                    self._format_disclaimers(disclaimers)
                )
            
            return "\n\n".join(response_parts)
            
        except Exception as e:
            return f"אירעה שגיאה בעיצוב התשובה: {str(e)}"

    def _load_templates(self) -> Dict:
        """טעינת תבניות תשובה"""
        return {
            "execution": {
                "intro": "בנוגע לשאלתך בנושא {category}, להלן התייחסות משפטית:",
                "legal_answer": "מבחינה משפטית, המצב הוא כדלקמן:\n{answer}",
                "references": "להלן האסמכתאות הרלוונטיות:",
                "recommendations": "המלצות לפעולה:",
                "disclaimers": "חשוב לציין:",
            },
            "debt_collection": {
                "intro": "בעניין גביית החוב שציינת, להלן הניתוח המשפטי:",
                "legal_answer": "הניתוח המשפטי מעלה כי:\n{answer}",
                "references": "הניתוח מתבסס על האסמכתאות הבאות:",
                "recommendations": "צעדים מומלצים להמשך:",
                "disclaimers": "הערות חשובות:",
            },
            "foreclosure": {
                "intro": "לגבי שאלתך בנושא העיקול, להלן חוות הדעת המשפטית:",
                "legal_answer": "עמדת החוק בנושא היא:\n{answer}",
                "references": "האסמכתאות התומכות בעמדה זו:",
                "recommendations": "הצעדים המומלצים במקרה זה:",
                "disclaimers": "חשוב להדגיש:",
            }
        }

    def _format_introduction(self, query: str, category: str) -> str:
        """עיצוב פתיחת התשובה"""
        template = self.templates.get(category, self.templates["execution"])
        return template["intro"].format(category=category)

    def _format_legal_answer(self, answer: str) -> str:
        """עיצוב התשובה המשפטית"""
        # הוספת סימוני פיסקאות
        paragraphs = answer.split("\n\n")
        formatted_paragraphs = []
        
        for i, para in enumerate(paragraphs, 1):
            if len(paragraphs) > 1:
                formatted_paragraphs.append(f"{i}. {para}")
            else:
                formatted_paragraphs.append(para)
        
        return "\n\n".join(formatted_paragraphs)

    def _format_references(self, references: List[LegalReference]) -> str:
        """עיצוב האסמכתאות"""
        formatted_refs = []
        
        for ref in sorted(references, key=lambda x: x.relevance_score, reverse=True):
            if ref.type == "חוק":
                formatted_refs.append(
                    f"• {ref.name}, {ref.reference}"
                )
            elif ref.type == "פסיקה":
                formatted_refs.append(
                    f"• {ref.name} ({ref.year}), {ref.reference}"
                )
            elif ref.type == "תקנה":
                formatted_refs.append(
                    f"• {ref.name}, {ref.reference}"
                )
        
        return "אסמכתאות משפטיות:\n" + "\n".join(formatted_refs)

    def _format_recommendations(self, recommendations: List[str]) -> str:
        """עיצוב ההמלצות המעשיות"""
        formatted_recs = []
        
        for i, rec in enumerate(recommendations, 1):
            formatted_recs.append(f"{i}. {rec}")
        
        return "המלצות לפעולה:\n" + "\n".join(formatted_recs)

    def _format_disclaimers(self, disclaimers: List[str]) -> str:
        """עיצוב ההסתייגויות"""
        formatted_disclaimers = []
        
        for disclaimer in disclaimers:
            formatted_disclaimers.append(f"* {disclaimer}")
        
        return "הערות חשובות:\n" + "\n".join(formatted_disclaimers)

    def format_legal_citation(self, ref: LegalReference) -> str:
        """עיצוב ציטוט משפטי"""
        if ref.type == "חוק":
            return f"סעיף {ref.reference} ל{ref.name}"
        elif ref.type == "פסיקה":
            return f"{ref.name}, {ref.reference} ({ref.year})"
        elif ref.type == "תקנה":
            return f"תקנה {ref.reference} לתקנות {ref.name}"
        return f"{ref.name}, {ref.reference}"

    def clean_text(self, text: str) -> str:
        """ניקוי וסידור טקסט"""
        # הסרת רווחים מיותרים
        text = re.sub(r'\s+', ' ', text)
        # הסרת שורות ריקות כפולות
        text = re.sub(r'\n\s*\n', '\n\n', text)
        # סידור סימני פיסוק
        text = re.sub(r'\s*([.,!?])', r'\1', text)
        return text.strip()

class LegalResponseValidator:
    """מוודא תקינות תשובות משפטיות"""
    
    @staticmethod
    def validate_response(
        answer: str,
        references: List[LegalReference],
        recommendations: Optional[List[str]] = None
    ) -> bool:
        """בדיקת תקינות התשובה"""
        try:
            # בדיקת אורך מינימלי
            if len(answer) < 50:
                return False
            
            # וידוא קיום אסמכתאות
            if not references:
                return False
            
            # בדיקת תקינות האסמכתאות
            for ref in references:
                if not all([ref.type, ref.name, ref.reference]):
                    return False
                
            # בדיקת המלצות (אם יש)
            if recommendations:
                if len(recommendations) == 0:
                    return False
                if any(len(rec) < 10 for rec in recommendations):
                    return False
            
            return True
            
        except Exception:
            return False

    @staticmethod
    def validate_legal_reference(ref: LegalReference) -> bool:
        """בדיקת תקינות אסמכתא"""
        try:
            # בדיקת שדות חובה
            if not all([ref.type, ref.name, ref.reference]):
                return False
            
            # בדיקת סוג האסמכתא
            if ref.type not in ["חוק", "פסיקה", "תקנה"]:
                return False
            
            # בדיקות ספציפיות לפי סוג
            if ref.type == "פסיקה" and not ref.year:
                return False
            
            return True
            
        except Exception:
            return False
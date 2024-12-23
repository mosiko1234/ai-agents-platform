# src/utils/legal_analyzer.py

from typing import Dict, List, Set, Tuple, Optional
import re
from collections import Counter
import logging
from dataclasses import dataclass
import json

@dataclass
class LegalTerm:
    """מבנה נתונים למונח משפטי"""
    term: str
    category: str
    weight: float = 1.0
    synonyms: List[str] = None
    context: Optional[str] = None

@dataclass
class AnalysisResult:
    """תוצאות ניתוח טקסט משפטי"""
    category: str
    confidence: float
    terms: List[LegalTerm]
    entities: List[str]
    references: List[str]
    sentiment: float

class LegalTextAnalyzer:
    """מנתח טקסטים משפטיים"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # טעינת מונחים משפטיים
        self.legal_terms = self._load_legal_terms()
        
        # רשימות מילות מפתח לפי קטגוריה
        self.category_keywords = {
            "execution": {
                "primary": {
                    "הוצאה לפועל", "פסק דין", "אכיפה", "ביצוע", "תיק הוצלפ",
                    "חייב", "זוכה", "אזהרה", "גביה", "חוב פסוק"
                },
                "secondary": {
                    "בקשה", "תשלומים", "הסדר", "פריסה", "הליך",
                    "רשם", "לשכה", "תובענה", "צו", "מימוש"
                }
            },
            "debt_collection": {
                "primary": {
                    "חוב", "גביה", "נושה", "חייב", "תשלום",
                    "הסדר חוב", "פריסת חוב", "ריבית", "הצמדה", "פיגורים"
                },
                "secondary": {
                    "דרישה", "התראה", "הודעה", "תזכורת", "הסכם",
                    "ערבות", "בטוחה", "משכון", "שעבוד", "המחאה"
                }
            },
            "foreclosure": {
                "primary": {
                    "עיקול", "צו עיקול", "מעוקל", "תפיסה", "מימוש",
                    "כונס נכסים", "נכס", "רכוש", "מיטלטלין", "זכויות"
                },
                "secondary": {
                    "בנק", "חשבון", "משכורת", "קצבה", "רכב",
                    "דירה", "מקרקעין", "צד שלישי", "הגנה", "ביטול"
                }
            },
            "bankruptcy": {
                "primary": {
                    "פשיטת רגל", "חדלות פירעון", "כינוס נכסים", "נאמן",
                    "הפטר", "הסדר נושים", "צו כינוס", "פושט רגל"
                },
                "secondary": {
                    "בקשה", "חקירה", "דוח", "תכנית", "הסדר",
                    "נושים", "אסיפה", "תביעת חוב", "דיבידנד", "הפניה"
                }
            }
        }
        
        # ביטויים רגולריים לזיהוי ישויות
        self.regex_patterns = {
            "case_number": r'תיק\s*(?:מספר|מס[\'"]?)?\s*(\d+/\d+)',
            "money_amount": r'(?:₪|ש"ח|שקלים?)\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            "date": r'(\d{1,2}/\d{1,2}/\d{4}|\d{1,2}\.\d{1,2}\.\d{4})',
            "legal_ref": r'(?:סעיף|תקנה)\s*(\d+(?:[א-ת])?(?:\([1-9]\))?)'
        }

    def analyze_text(self, text: str) -> AnalysisResult:
        """ניתוח טקסט משפטי"""
        try:
            # זיהוי קטגוריה וביטחון
            category, confidence = self._identify_category(text)
            
            # זיהוי מונחים משפטיים
            terms = self._identify_legal_terms(text)
            
            # זיהוי ישויות
            entities = self._extract_entities(text)
            
            # זיהוי אסמכתאות
            references = self._extract_references(text)
            
            # ניתוח סנטימנט
            sentiment = self._analyze_sentiment(text)
            
            return AnalysisResult(
                category=category,
                confidence=confidence,
                terms=terms,
                entities=entities,
                references=references,
                sentiment=sentiment
            )
            
        except Exception as e:
            self.logger.error(f"Error analyzing text: {str(e)}")
            raise

    def _identify_category(self, text: str) -> Tuple[str, float]:
        """זיהוי קטגוריה משפטית וביטחון"""
        scores = {}
        words = set(re.findall(r'\b\w+\b', text.lower()))
        
        for category, keywords in self.category_keywords.items():
            score = 0.0
            
            # בדיקת מילות מפתח ראשיות
            primary_matches = words.intersection(keywords["primary"])
            score += len(primary_matches) * 2.0
            
            # בדיקת מילות מפתח משניות
            secondary_matches = words.intersection(keywords["secondary"])
            score += len(secondary_matches)
            
            # נרמול הציון
            total_keywords = len(keywords["primary"]) * 2 + len(keywords["secondary"])
            scores[category] = score / total_keywords
        
        # בחירת הקטגוריה עם הציון הגבוה ביותר
        if not scores:
            return "general", 0.0
            
        best_category = max(scores.items(), key=lambda x: x[1])
        return best_category[0], best_category[1]

    def _identify_legal_terms(self, text: str) -> List[LegalTerm]:
        """זיהוי מונחים משפטיים בטקסט"""
        found_terms = []
        words = re.findall(r'\b\w+(?:\s+\w+)*\b', text)
        
        for term in self.legal_terms:
            # חיפוש המונח העיקרי
            if term.term in text:
                found_terms.append(term)
                continue
                
            # חיפוש מילים נרדפות
            if term.synonyms:
                for synonym in term.synonyms:
                    if synonym in text:
                        found_terms.append(term)
                        break
        
        return sorted(found_terms, key=lambda x: x.weight, reverse=True)

    def _extract_entities(self, text: str) -> List[str]:
        """חילוץ ישויות מהטקסט"""
        entities = []
        
        for entity_type, pattern in self.regex_patterns.items():
            matches = re.finditer(pattern, text)
            for match in matches:
                entities.append(f"{entity_type}: {match.group(1)}")
        
        return entities

    def _extract_references(self, text: str) -> List[str]:
        """חילוץ אסמכתאות משפטיות"""
        references = []
        
        # חיפוש אזכורי חוקים
        law_matches = re.finditer(
            r'חוק\s+([א-ת\s,]+?)(?:,\s*התש[״"]\w+[-–]\d{4}|\d{4})',
            text
        )
        references.extend([m.group(0) for m in law_matches])
        
        # חיפוש אזכורי פסקי דין
        case_matches = re.finditer(
            r'(?:ע"א|ע״א|בג"ץ|בג״ץ|ת"א|ת״א)\s+\d+/\d+',
            text
        )
        references.extend([m.group(0) for m in case_matches])
        
        # חיפוש אזכורי תקנות
        regulation_matches = re.finditer(
            r'תקנ(?:ה|ות)\s+([א-ת\s,]+?)(?:,\s*התש[״"]\w+[-–]\d{4}|\d{4})',
            text
        )
        references.extend([m.group(0) for m in regulation_matches])
        
        return references

    def _analyze_sentiment(self, text: str) -> float:
        """ניתוח סנטימנט בסיסי"""
        positive_words = {
            "מאושר", "מקבל", "מסכים", "מתקבל", "זכאי",
            "לטובת", "בעד", "חיובי", "תקין", "מומלץ"
        }
        
        negative_words = {
            "נדחה", "דוחה", "מסרב", "נדחית", "שולל",
            "נגד", "שלילי", "פסול", "אסור", "בעייתי"
        }
        
        words = set(re.findall(r'\b\w+\b', text.lower()))
        
        positive_count = len(words.intersection(positive_words))
        negative_count = len(words.intersection(negative_words))
        
        if positive_count == 0 and negative_count == 0:
            return 0.0
            
        return (positive_count - negative_count) / (positive_count + negative_count)

    def _load_legal_terms(self) -> List[LegalTerm]:
        """טעינת מונחים משפטיים"""
        # כאן יש להוסיף טעינה ממסד נתונים או קובץ
        return [
            LegalTerm(
                term="הוצאה לפועל",
                category="execution",
                synonyms=["הוצל\"פ", "לשכת ההוצאה לפועל"],
                weight=1.0
            ),
            LegalTerm(
                term="עיקול",
                category="foreclosure",
                synonyms=["צו עיקול", "מעוקל"],
                weight=0.8
            ),
            # יש להוסיף עוד מונחים
        ]

    def classify_question(self, text: str) -> Tuple[str, float]:
        """סיווג שאלה משפטית"""
        # זיהוי סוג השאלה
        question_types = {
            "procedural": r'(?:כיצד|איך|מה הדרך|מהו ההליך)',
            "deadline": r'(?:מתי|עד מתי|באיזה מועד|כמה זמן)',
            "cost": r'(?:כמה|מה העלות|כמה עולה|מה המחיר)',
            "rights": r'(?:האם מותר|האם אפשר|מה הזכויות|האם ניתן)',
            "status": r'(?:מה המצב|מה הסטטוס|איפה עומד|מה קורה)',
        }
        
        # זיהוי סוג השאלה לפי ביטויים רגולריים
        for q_type, pattern in question_types.items():
            if re.search(pattern, text, re.IGNORECASE):
                return q_type, 0.8
        
        return "general", 0.5
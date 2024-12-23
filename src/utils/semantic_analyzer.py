# src/utils/semantic_analyzer.py

from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass
import logging
from collections import defaultdict
import spacy
import networkx as nx
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np
from datetime import datetime

@dataclass
class LegalTerm:
    """מונח משפטי"""
    term: str
    category: str
    variants: List[str]
    hebrew_explanation: str
    english_term: Optional[str] = None
    importance: float = 1.0
    relations: List[str] = None

@dataclass
class SemanticAnalysis:
    """תוצאות ניתוח סמנטי"""
    terms: List[LegalTerm]
    keywords: List[str]
    relations: List[Tuple[str, str, str]]  # (term1, relation, term2)
    context_score: float
    sentiment: float
    complexity: float

class LegalSemanticAnalyzer:
    """מנתח סמנטי למונחים משפטיים"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        # טעינת מודל spacy לעברית
        self.nlp = spacy.load("he_core_news_lg")
        self.vectorizer = TfidfVectorizer()
        
        # טעינת מונחים משפטיים
        self.legal_terms = self._load_legal_terms()
        
        # גרף יחסים סמנטיים
        self.semantic_graph = nx.DiGraph()
        self._build_semantic_graph()

    async def analyze_text(self, text: str) -> SemanticAnalysis:
        """ניתוח סמנטי של טקסט משפטי"""
        try:
            # עיבוד הטקסט
            doc = self.nlp(text)
            
            # זיהוי מונחים משפטיים
            terms = await self._identify_legal_terms(doc)
            
            # חילוץ מילות מפתח
            keywords = await self._extract_keywords(doc)
            
            # זיהוי יחסים
            relations = await self._identify_relations(doc)
            
            # חישוב מדדים
            context_score = await self._calculate_context_score(doc, terms)
            sentiment = await self._analyze_sentiment(doc)
            complexity = await self._calculate_complexity(doc)
            
            return SemanticAnalysis(
                terms=terms,
                keywords=keywords,
                relations=relations,
                context_score=context_score,
                sentiment=sentiment,
                complexity=complexity
            )
            
        except Exception as e:
            self.logger.error(f"Error analyzing text: {str(e)}")
            raise

    async def find_related_terms(
        self,
        term: str,
        max_distance: int = 2
    ) -> List[LegalTerm]:
        """מציאת מונחים קשורים"""
        try:
            related_terms = []
            if term in self.semantic_graph:
                # חיפוש מונחים במרחק מוגדר בגרף
                neighbors = nx.single_source_shortest_path_length(
                    self.semantic_graph,
                    term,
                    cutoff=max_distance
                )
                
                for related_term, distance in neighbors.items():
                    if related_term in self.legal_terms:
                        term_obj = self.legal_terms[related_term]
                        term_obj.importance = 1.0 / (distance + 1)  # משקל לפי מרחק
                        related_terms.append(term_obj)
            
            return sorted(
                related_terms,
                key=lambda x: x.importance,
                reverse=True
            )
            
        except Exception as e:
            self.logger.error(f"Error finding related terms: {str(e)}")
            return []

    async def compare_texts(
        self,
        text1: str,
        text2: str
    ) -> Tuple[float, List[str]]:
        """השוואה סמנטית בין שני טקסטים"""
        try:
            # ניתוח שני הטקסטים
            doc1 = self.nlp(text1)
            doc2 = self.nlp(text2)
            
            # חישוב דמיון וקטורי
            similarity = doc1.similarity(doc2)
            
            # זיהוי מונחים משותפים
            terms1 = set(await self._identify_legal_terms(doc1))
            terms2 = set(await self._identify_legal_terms(doc2))
            common_terms = list(terms1.intersection(terms2))
            
            return similarity, common_terms
            
        except Exception as e:
            self.logger.error(f"Error comparing texts: {str(e)}")
            return 0.0, []

    async def _identify_legal_terms(self, doc) -> List[LegalTerm]:
        """זיהוי מונחים משפטיים בטקסט"""
        terms = []
        for term in self.legal_terms.values():
            # חיפוש המונח והווריאציות שלו
            term_patterns = [term.term] + term.variants
            for pattern in term_patterns:
                if pattern.lower() in doc.text.lower():
                    terms.append(term)
                    break
        return terms

    async def _extract_keywords(self, doc) -> List[str]:
        """חילוץ מילות מפתח"""
        keywords = []
        for token in doc:
            # בחירת מילים משמעותיות
            if (token.pos_ in ["NOUN", "PROPN", "ADJ"] and 
                not token.is_stop and 
                len(token.text) > 1):
                keywords.append(token.text)
        return keywords

    async def _identify_relations(
        self,
        doc
    ) -> List[Tuple[str, str, str]]:
        """זיהוי יחסים בין מונחים"""
        relations = []
        for sent in doc.sents:
            for token in sent:
                if token.dep_ in ["nsubj", "dobj", "pobj"]:
                    head = token.head.text
                    dep = token.text
                    rel = token.dep_
                    relations.append((head, rel, dep))
        return relations

    async def _calculate_context_score(
        self,
        doc,
        terms: List[LegalTerm]
    ) -> float:
        """חישוב ציון הקשר משפטי"""
        try:
            if not terms:
                return 0.0
                
            # חישוב לפי מספר וחשיבות המונחים
            weighted_sum = sum(term.importance for term in terms)
            max_possible = len(terms)
            
            # נרמול הציון
            score = weighted_sum / max_possible
            return min(max(score, 0.0), 1.0)
            
        except Exception as e:
            self.logger.error(f"Error calculating context score: {str(e)}")
            return 0.0

    async def _analyze_sentiment(self, doc) -> float:
        """ניתוח סנטימנט"""
        try:
            # מילים חיוביות ושליליות בהקשר משפטי
            positive_terms = {
                "מאשר", "מקבל", "מאשרת", "חיובי", "זכאי",
                "מומלץ", "מותר", "רשאי", "בעד"
            }
            negative_terms = {
                "דוחה", "שולל", "אוסר", "מסרב", "שלילי",
                "נדחה", "אסור", "מתנגד", "נגד"
            }
            
            score = 0
            total = 0
            
            for token in doc:
                if token.text in positive_terms:
                    score += 1
                    total += 1
                elif token.text in negative_terms:
                    score -= 1
                    total += 1
                    
            return score / total if total > 0 else 0
            
        except Exception as e:
            self.logger.error(f"Error analyzing sentiment: {str(e)}")
            return 0.0

    async def _calculate_complexity(self, doc) -> float:
        """חישוב מורכבות הטקסט"""
        try:
            # מדדי מורכבות
            sentence_lengths = [len(sent) for sent in doc.sents]
            avg_sentence_length = np.mean(sentence_lengths)
            
            # אחוז המונחים המשפטיים
            legal_terms_count = len(await self._identify_legal_terms(doc))
            total_words = len(doc)
            legal_terms_ratio = legal_terms_count / total_words if total_words > 0 else 0
            
            # חישוב ציון מורכבות משוקלל
            complexity = (
                0.5 * min(avg_sentence_length / 20, 1) +  # נרמול לפי אורך משפט ממוצע
                0.5 * legal_terms_ratio
            )
            
            return min(max(complexity, 0.0), 1.0)
            
        except Exception as e:
            self.logger.error(f"Error calculating complexity: {str(e)}")
            return 0.0

    def _load_legal_terms(self) -> Dict[str, LegalTerm]:
        """טעינת מונחים משפטיים"""
        # כאן יש להוסיף טעינה ממסד נתונים
        return {
            "עיקול": LegalTerm(
                term="עיקול",
                category="הוצאה לפועל",
                variants=["לעקל", "עיקולים", "מעוקל"],
                hebrew_explanation="הגבלת השימוש ברכוש לצורך הבטחת חוב",
                english_term="attachment",
                importance=1.0,
                relations=["חוב", "נכס", "זוכה"]
            ),
            "פסק דין": LegalTerm(
                term="פסק דין",
                category="משפט",
                variants=["פסה״ד", "פס״ד", "פסקי דין"],
                hebrew_explanation="החלטה סופית של בית משפט",
                english_term="judgment",
                importance=1.0,
                relations=["בית משפט", "שופט", "החלטה"]
            )
            # יש להוסיף עוד מונחים
        }

    def _build_semantic_graph(self):
        """בניית גרף יחסים סמנטיים"""
        try:
            # הוספת צמתים למונחים
            for term in self.legal_terms.values():
                self.semantic_graph.add_node(term.term)
                
                # הוספת קשרים
                if term.relations:
                    for related_term in term.relations:
                        self.semantic_graph.add_edge(term.term, related_term)
                        
        except Exception as e:
            self.logger.error(f"Error building semantic graph: {str(e)}")
# src/core/learning.py

from typing import Dict, List, Optional, Tuple
import logging
from datetime import datetime, timedelta
import json
from dataclasses import dataclass
import asyncio
from collections import defaultdict
import numpy as np
from azure.cosmos import CosmosClient
from openai import AsyncAzureOpenAI

@dataclass
class Interaction:
    """מידע על אינטראקציה עם משתמש"""
    interaction_id: str
    user_id: str
    query: str
    response: str
    feedback: Optional[str] = None
    feedback_score: Optional[float] = None
    timestamp: datetime = datetime.utcnow()
    context: Optional[Dict] = None

class LearningManager:
    """מנהל למידה והתאמה אישית של סוכנים"""
    
    def __init__(self, cosmos_client: CosmosClient, openai_client: AsyncAzureOpenAI):
        self.logger = logging.getLogger(__name__)
        self.cosmos_client = cosmos_client
        self.openai_client = openai_client
        self.database = self.cosmos_client.get_database_client("ai_agents")
        self.interactions_container = self.database.get_container_client("interactions")
        self.patterns_container = self.database.get_container_client("learning_patterns")
        
        # מטריקות למידה
        self.metrics = defaultdict(float)
        
        # סף לזיהוי דפוסים
        self.pattern_threshold = 0.8
        self.min_interactions = 10

    async def record_interaction(self, interaction: Interaction):
        """תיעוד אינטראקציה חדשה"""
        try:
            document = {
                'id': interaction.interaction_id,
                'user_id': interaction.user_id,
                'query': interaction.query,
                'response': interaction.response,
                'feedback': interaction.feedback,
                'feedback_score': interaction.feedback_score,
                'timestamp': interaction.timestamp.isoformat(),
                'context': interaction.context
            }
            
            await self.interactions_container.create_item(body=document)
            
            # אם יש משוב, נעדכן מטריקות
            if interaction.feedback_score is not None:
                await self._update_metrics(interaction)
            
            # ניתוח דפוסים
            await self._analyze_patterns(interaction)
            
        except Exception as e:
            self.logger.error(f"Error recording interaction: {str(e)}")

    async def get_personalized_context(
        self,
        user_id: str,
        query: str
    ) -> Dict:
        """קבלת הקשר מותאם אישית למשתמש"""
        try:
            # קבלת היסטוריית אינטראקציות
            history = await self._get_user_history(user_id)
            
            # זיהוי דפוסים רלוונטיים
            patterns = await self._get_relevant_patterns(query, history)
            
            # בניית הקשר מותאם
            context = {
                'user_history': history[-5:],  # 5 אינטראקציות אחרונות
                'patterns': patterns,
                'preferences': await self._get_user_preferences(user_id)
            }
            
            return context
            
        except Exception as e:
            self.logger.error(f"Error getting personalized context: {str(e)}")
            return {}

    async def analyze_feedback(self, timeframe: timedelta = timedelta(days=7)):
        """ניתוח משוב משתמשים"""
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timeframe
            
            query = f"""
            SELECT * FROM c 
            WHERE c.timestamp >= '{start_time.isoformat()}'
            AND c.feedback_score IS NOT NULL
            """
            
            feedback_items = []
            async for item in self.interactions_container.query_items(
                query=query,
                enable_cross_partition_query=True
            ):
                feedback_items.append(item)
            
            if not feedback_items:
                return {}
            
            # ניתוח סטטיסטי
            scores = [item['feedback_score'] for item in feedback_items]
            analysis = {
                'total_feedback': len(scores),
                'average_score': np.mean(scores),
                'score_std': np.std(scores),
                'positive_ratio': len([s for s in scores if s > 0.7]) / len(scores),
                'negative_ratio': len([s for s in scores if s < 0.3]) / len(scores)
            }
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error analyzing feedback: {str(e)}")
            return {}

    async def improve_responses(self, agent_id: str):
        """שיפור תשובות על בסיס למידה"""
        try:
            # ניתוח תשובות מוצלחות
            successful_patterns = await self._analyze_successful_responses(agent_id)
            
            # עדכון תבניות תשובה
            await self._update_response_patterns(agent_id, successful_patterns)
            
            # שיפור פרומפטים
            await self._improve_prompts(agent_id, successful_patterns)
            
            self.logger.info(f"Improved responses for agent {agent_id}")
            
        except Exception as e:
            self.logger.error(f"Error improving responses: {str(e)}")

    async def _update_metrics(self, interaction: Interaction):
        """עדכון מטריקות למידה"""
        try:
            # חישוב משקל המשוב
            weight = 1.0
            if interaction.context and 'importance' in interaction.context:
                weight = interaction.context['importance']
            
            # עדכון מטריקות
            self.metrics['total_feedback'] += 1
            self.metrics['weighted_score'] += interaction.feedback_score * weight
            self.metrics['average_score'] = (
                self.metrics['weighted_score'] / self.metrics['total_feedback']
            )
            
            # שמירת מטריקות
            await self._store_metrics()
            
        except Exception as e:
            self.logger.error(f"Error updating metrics: {str(e)}")

    async def _analyze_patterns(self, interaction: Interaction):
        """זיהוי דפוסים באינטראקציות"""
        try:
            # בדיקה אם יש מספיק אינטראקציות לניתוח
            similar_interactions = await self._find_similar_interactions(interaction)
            
            if len(similar_interactions) >= self.min_interactions:
                # זיהוי דפוסים
                patterns = await self._identify_patterns(similar_interactions)
                
                # שמירת דפוסים משמעותיים
                for pattern in patterns:
                    if pattern['confidence'] >= self.pattern_threshold:
                        await self._store_pattern(pattern)
                        
        except Exception as e:
            self.logger.error(f"Error analyzing patterns: {str(e)}")

    async def _find_similar_interactions(
        self,
        interaction: Interaction
    ) -> List[Dict]:
        """מציאת אינטראקציות דומות"""
        try:
            # שימוש ב-GPT להשוואת שאלות
            similar = []
            
            query = f"""
            SELECT * FROM c 
            WHERE c.feedback_score IS NOT NULL
            ORDER BY c.timestamp DESC
            LIMIT 100
            """
            
            async for item in self.interactions_container.query_items(
                query=query,
                enable_cross_partition_query=True
            ):
                similarity = await self._calculate_similarity(
                    interaction.query,
                    item['query']
                )
                if similarity > 0.7:
                    similar.append(item)
            
            return similar
            
        except Exception as e:
            self.logger.error(f"Error finding similar interactions: {str(e)}")
            return []

    async def _calculate_similarity(self, query1: str, query2: str) -> float:
        """חישוב דמיון בין שאלות באמצעות GPT"""
        try:
            messages = [
                {
                    "role": "system",
                    "content": "דרג את מידת הדמיון בין שתי השאלות בסולם 0-1"
                },
                {
                    "role": "user",
                    "content": f"שאלה 1: {query1}\nשאלה 2: {query2}"
                }
            ]
            
            response = await self.openai_client.chat.completions.create(
                messages=messages,
                model="gpt-4",
                temperature=0.2,
                max_tokens=50
            )
            
            # חילוץ הציון מהתשובה
            score_text = response.choices[0].message.content
            try:
                score = float(score_text)
                return min(max(score, 0), 1)  # ודא שהציון בין 0 ל-1
            except ValueError:
                return 0
                
        except Exception as e:
            self.logger.error(f"Error calculating similarity: {str(e)}")
            return 0

    async def _store_pattern(self, pattern: Dict):
        """שמירת דפוס שזוהה"""
        try:
            await self.patterns_container.upsert_item(
                body={
                    'id': pattern['id'],
                    'type': pattern['type'],
                    'pattern': pattern['pattern'],
                    'confidence': pattern['confidence'],
                    'examples': pattern['examples'],
                    'timestamp': datetime.utcnow().isoformat()
                }
            )
        except Exception as e:
            self.logger.error(f"Error storing pattern: {str(e)}")

    async def _store_metrics(self):
        """שמירת מטריקות למידה"""
        try:
            metrics_doc = {
                'id': 'learning_metrics',
                'metrics': dict(self.metrics),
                'timestamp': datetime.utcnow().isoformat()
            }
            
            container = self.database.get_container_client("metrics")
            await container.upsert_item(body=metrics_doc)
            
        except Exception as e:
            self.logger.error(f"Error storing metrics: {str(e)}")
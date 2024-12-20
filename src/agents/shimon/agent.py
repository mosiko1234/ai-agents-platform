# src/agents/shimon/agent.py

from typing import Dict, List, Optional
from datetime import datetime
import logging
import json

from core.base_agent import BaseAgent
from core.schemas import Message, AgentResponse
from core.exceptions import AgentError, KnowledgeBaseError

class ShimonAgent(BaseAgent):
    """Legal expert agent specialized in execution office procedures"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.legal_categories = {
            "execution": "הוצאה לפועל",
            "debt_collection": "גביית חובות",
            "foreclosure": "עיקולים",
            "bankruptcy": "פשיטת רגל",
            "legal_proceedings": "הליכים משפטיים"
        }
        self.knowledge_update_interval = 24  # hours
        self.last_knowledge_update = datetime.utcnow()

    async def initialize(self) -> None:
        """Initialize Shimon-specific resources"""
        await super().initialize()
        try:
            # Load legal knowledge base
            await self._load_legal_knowledge()
            # Load case law and precedents
            await self._load_case_law()
            # Initialize legal templates
            await self._load_legal_templates()
            
            self.logger.info("Shimon agent initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize Shimon agent: {str(e)}")
            raise AgentError(f"Shimon initialization failed: {str(e)}", self.agent_id)

    async def process_message(self, message: Message) -> AgentResponse:
        """Process incoming legal query"""
        start_time = datetime.utcnow()
        try:
            # Categorize the legal query
            category = await self._categorize_query(message.content)
            
            # Prepare context with relevant legal knowledge
            context = await self._prepare_legal_context(category, message.content)
            
            # Generate response using OpenAI
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": await self._format_legal_query(message.content, context)}
            ]
            
            response_content = await self._get_completion(
                messages,
                temperature=0.3  # Lower temperature for more precise legal responses
            )
            
            # Create response with citations
            response = AgentResponse(
                content=response_content,
                agent_id=self.agent_id,
                processing_time=(datetime.utcnow() - start_time).total_seconds(),
                metadata={
                    "category": category,
                    "references": context.get("references", []),
                    "confidence_score": await self._calculate_confidence(response_content)
                }
            )
            
            # Store interaction
            await self._store_interaction(message, response)
            
            # Update metrics
            self._update_metrics(True, response.processing_time)
            
            return response
            
        except Exception as e:
            self._update_metrics(False, (datetime.utcnow() - start_time).total_seconds())
            raise AgentError(f"Failed to process message: {str(e)}", self.agent_id)

    async def update_knowledge(self) -> None:
        """Update legal knowledge base"""
        try:
            # Update case law
            await self._update_case_law()
            # Update legal guidelines
            await self._update_legal_guidelines()
            # Update templates
            await self._update_templates()
            
            self.last_knowledge_update = datetime.utcnow()
            self.logger.info("Successfully updated legal knowledge base")
            
        except Exception as e:
            self.logger.error(f"Failed to update knowledge: {str(e)}")
            raise KnowledgeBaseError(f"Knowledge update failed: {str(e)}", self.agent_id)

    async def _load_legal_knowledge(self) -> None:
        """Load legal knowledge base from Cosmos DB"""
        try:
            database = self.cosmos_client.get_database_client("ai_agents")
            container = database.get_container_client("legal_knowledge")
            
            query = f"""
            SELECT * FROM c 
            WHERE c.agent_id = '{self.agent_id}'
            AND c.type = 'legal_knowledge'
            """
            
            async for item in container.query_items(
                query=query,
                enable_cross_partition_query=True
            ):
                self.knowledge_base[item['category']] = item['content']
                
        except Exception as e:
            raise KnowledgeBaseError(f"Failed to load legal knowledge: {str(e)}", self.agent_id)

    async def _load_case_law(self) -> None:
        """Load case law and legal precedents"""
        try:
            database = self.cosmos_client.get_database_client("ai_agents")
            container = database.get_container_client("case_law")
            
            query = f"""
            SELECT * FROM c 
            WHERE c.agent_id = '{self.agent_id}'
            ORDER BY c.date DESC
            """
            
            self.knowledge_base["case_law"] = {}
            async for item in container.query_items(
                query=query,
                enable_cross_partition_query=True
            ):
                category = item['category']
                if category not in self.knowledge_base["case_law"]:
                    self.knowledge_base["case_law"][category] = []
                self.knowledge_base["case_law"][category].append(item)
                
        except Exception as e:
            self.logger.error(f"Failed to load case law: {str(e)}")

    async def _load_legal_templates(self) -> None:
        """Load legal document templates"""
        try:
            database = self.cosmos_client.get_database_client("ai_agents")
            container = database.get_container_client("templates")
            
            query = f"""
            SELECT * FROM c 
            WHERE c.agent_id = '{self.agent_id}'
            """
            
            self.knowledge_base["templates"] = {}
            async for item in container.query_items(
                query=query,
                enable_cross_partition_query=True
            ):
                category = item['category']
                if category not in self.knowledge_base["templates"]:
                    self.knowledge_base["templates"][category] = []
                self.knowledge_base["templates"][category].append(item)
                
        except Exception as e:
            self.logger.error(f"Failed to load templates: {str(e)}")

    async def _categorize_query(self, query: str) -> str:
        """Categorize the legal query"""
        try:
            messages = [
                {"role": "system", "content": """
                אתה מסווג שאלות משפטיות. סווג את השאלה הבאה לאחת מהקטגוריות הבאות:
                - הוצאה לפועל
                - גביית חובות
                - עיקולים
                - פשיטת רגל
                - הליכים משפטיים
                השב בקטגוריה בלבד.
                """},
                {"role": "user", "content": query}
            ]
            
            category_response = await self._get_completion(
                messages,
                temperature=0.3,
                max_tokens=100
            )
            
            # Map response to category
            for key, value in self.legal_categories.items():
                if value in category_response:
                    return key
                    
            return "general"  # Default category
            
        except Exception as e:
            self.logger.error(f"Failed to categorize query: {str(e)}")
            return "general"

    async def _format_legal_query(self, query: str, context: Dict) -> str:
        """Format the legal query with context"""
        references = "\n".join(context.get("references", []))
        relevant_knowledge = json.dumps(context.get("knowledge", {}), ensure_ascii=False)
        
        return f"""שאלה משפטית: {query}

מידע רלוונטי:
{relevant_knowledge}

אסמכתאות משפטיות:
{references}

אנא ספק תשובה מקיפה הכוללת:
1. התייחסות לחוק ולתקנות הרלוונטיות
2. אזכור פסיקה רלוונטית מהאסמכתאות
3. המלצות מעשיות לפעולה
4. הסתייגויות או נקודות חשובות לתשומת לב"""

    async def _calculate_confidence(self, response: str) -> float:
        """Calculate confidence score for the response"""
        try:
            # Check for key elements in the response
            confidence = 0.5  # Base confidence
            
            # Check for legal citations
            if "סעיף" in response or "תקנה" in response:
                confidence += 0.1
                
            # Check for case law references
            if "פסק דין" in response or "ע\"א" in response:
                confidence += 0.1
                
            # Check for practical recommendations
            if "מומלץ" in response or "יש לפעול" in response:
                confidence += 0.1
                
            # Check for caveats or important notes
            if "יש לשים לב" in response or "חשוב לציין" in response:
                confidence += 0.1
                
            # Check response length and structure
            if len(response.split()) > 50:
                confidence += 0.1
                
            return min(confidence, 1.0)
            
        except Exception as e:
            self.logger.error(f"Failed to calculate confidence: {str(e)}")
            return 0.5
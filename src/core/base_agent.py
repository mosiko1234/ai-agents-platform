# src/core/base_agent.py

from typing import Dict, Any, Optional, List
import logging
from datetime import datetime
import asyncio
from abc import ABC, abstractmethod

from openai import AsyncAzureOpenAI
from azure.cosmos import CosmosClient

from core.exceptions import AgentError, KnowledgeBaseError
from core.schemas import Message, AgentResponse, AgentMetrics
from core.config import settings

class BaseAgent(ABC):
    """Base class for all AI agents"""
    
    def __init__(
        self,
        agent_id: str,
        name: str,
        description: str,
        openai_client: AsyncAzureOpenAI,
        cosmos_client: CosmosClient
    ):
        self.agent_id = agent_id
        self.name = name
        self.description = description
        self.openai_client = openai_client
        self.cosmos_client = cosmos_client
        self.logger = logging.getLogger(f"agent.{agent_id}")
        self.metrics: AgentMetrics = AgentMetrics(agent_id=agent_id)
        self.knowledge_base: Dict[str, Any] = {}
        self.system_prompt: str = ""
        self.last_active = datetime.utcnow()
        self.active = True

    async def initialize(self) -> None:
        """Initialize agent resources and load knowledge base"""
        try:
            await self._load_knowledge_base()
            await self._load_system_prompt()
            self.logger.info(f"Agent {self.agent_id} initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize agent {self.agent_id}: {str(e)}")
            raise AgentError(f"Initialization failed: {str(e)}", self.agent_id)

    @abstractmethod
    async def process_message(self, message: Message) -> AgentResponse:
        """Process incoming message - must be implemented by specific agents"""
        pass

    @abstractmethod
    async def update_knowledge(self) -> None:
        """Update agent's knowledge base - must be implemented by specific agents"""
        pass

    async def _load_knowledge_base(self) -> None:
        """Load agent's knowledge base from Cosmos DB"""
        try:
            database = self.cosmos_client.get_database_client("ai_agents")
            container = database.get_container_client("knowledge_base")
            
            query = f"SELECT * FROM c WHERE c.agent_id = '{self.agent_id}'"
            items = container.query_items(query=query, enable_cross_partition_query=True)
            
            async for item in items:
                self.knowledge_base[item['key']] = item['value']
                
        except Exception as e:
            raise KnowledgeBaseError(f"Failed to load knowledge base: {str(e)}", self.agent_id)

    async def _load_system_prompt(self) -> None:
        """Load agent's system prompt from Cosmos DB"""
        try:
            database = self.cosmos_client.get_database_client("ai_agents")
            container = database.get_container_client("system_prompts")
            
            query = f"SELECT * FROM c WHERE c.agent_id = '{self.agent_id}'"
            items = container.query_items(query=query, enable_cross_partition_query=True)
            
            async for item in items:
                self.system_prompt = item['prompt']
                break  # Take the first prompt
                
        except Exception as e:
            self.logger.warning(f"Failed to load system prompt: {str(e)}")
            self.system_prompt = f"You are {self.name}, {self.description}"

    async def _get_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 800
    ) -> str:
        """Get completion from OpenAI"""
        try:
            # Add system prompt if not present
            if not any(msg.get("role") == "system" for msg in messages):
                messages.insert(0, {"role": "system", "content": self.system_prompt})
            
            response = await self.openai_client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            self.logger.error(f"OpenAI API error: {str(e)}")
            raise AgentError(f"Failed to get completion: {str(e)}", self.agent_id)

    async def _store_interaction(
        self,
        message: Message,
        response: AgentResponse
    ) -> None:
        """Store interaction in Cosmos DB"""
        try:
            database = self.cosmos_client.get_database_client("ai_agents")
            container = database.get_container_client("interactions")
            
            document = {
                'id': str(datetime.utcnow().timestamp()),
                'agent_id': self.agent_id,
                'message': message.dict(),
                'response': response.dict(),
                'timestamp': datetime.utcnow().isoformat()
            }
            
            await container.create_item(body=document)
            
        except Exception as e:
            self.logger.error(f"Failed to store interaction: {str(e)}")

    def _update_metrics(self, success: bool, processing_time: float) -> None:
        """Update agent metrics"""
        self.metrics.total_requests += 1
        if success:
            self.metrics.successful_requests += 1
        else:
            self.metrics.failed_requests += 1
            
        self.metrics.average_response_time = (
            (self.metrics.average_response_time * (self.metrics.total_requests - 1) + processing_time)
            / self.metrics.total_requests
        )
        
        self.metrics.error_rate = (
            self.metrics.failed_requests / self.metrics.total_requests
            if self.metrics.total_requests > 0 else 0
        )
        
        self.metrics.last_active = datetime.utcnow()
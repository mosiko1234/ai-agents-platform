# src/core/agent_manager.py

from typing import Dict, List, Type, Optional
import logging
import asyncio
from datetime import datetime
import importlib

from azure.cosmos import CosmosClient
from azure.identity import DefaultAzureCredential
from openai import AsyncAzureOpenAI

from core.base_agent import BaseAgent
from core.exceptions import AgentNotFoundError, AgentInitializationError
from core.schemas import Message, AgentResponse, AgentConfig, SystemStatus
from core.config import settings

class AgentManager:
    """Central management system for all AI agents"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.agents: Dict[str, BaseAgent] = {}
        self.credential = DefaultAzureCredential()
        self.cosmos_client = None
        self.openai_client = None
        self._initialize_lock = asyncio.Lock()
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the manager and required connections"""
        if self._initialized:
            return

        async with self._initialize_lock:
            if self._initialized:  # Double-check pattern
                return
                
            try:
                # Initialize OpenAI client
                self.openai_client = AsyncAzureOpenAI(
                    api_key=settings.OPENAI_API_KEY,
                    api_version="2024-02-15-preview",
                    azure_endpoint="https://YOUR_RESOURCE_NAME.openai.azure.com"
                )
                
                # Initialize Cosmos DB client
                connection_str = "YOUR_COSMOS_CONNECTION_STRING"  # Get from Key Vault in production
                self.cosmos_client = CosmosClient.from_connection_string(connection_str)
                
                # Load and initialize registered agents
                await self._load_registered_agents()
                
                self._initialized = True
                self.logger.info("Agent Manager initialized successfully")
                
            except Exception as e:
                self.logger.error(f"Failed to initialize Agent Manager: {str(e)}")
                raise

    async def register_agent(
        self,
        agent_class: Type[BaseAgent],
        config: AgentConfig
    ) -> None:
        """Register a new AI agent"""
        try:
            # Initialize agent
            agent = agent_class(
                agent_id=config.id,
                name=config.name,
                description=config.description,
                openai_client=self.openai_client,
                cosmos_client=self.cosmos_client
            )
            
            await agent.initialize()
            self.agents[config.id] = agent
            
            # Store agent configuration
            database = self.cosmos_client.get_database_client("ai_agents")
            container = database.get_container_client("agent_configs")
            
            await container.upsert_item(body=config.dict())
            
            self.logger.info(f"Successfully registered agent: {config.id}")
            
        except Exception as e:
            self.logger.error(f"Failed to register agent {config.id}: {str(e)}")
            raise AgentInitializationError(f"Failed to register agent: {str(e)}", config.id)

    async def process_message(self, message: Message) -> AgentResponse:
        """Process message using specified agent"""
        if not self._initialized:
            await self.initialize()

        try:
            agent = self.agents.get(message.agent_id)
            if not agent:
                raise AgentNotFoundError(f"Agent {message.agent_id} not found")
                
            if not agent.active:
                raise AgentNotFoundError(f"Agent {message.agent_id} is not active")
                
            response = await agent.process_message(message)
            return response
            
        except Exception as e:
            self.logger.error(f"Error processing message for agent {message.agent_id}: {str(e)}")
            raise

    async def update_all_knowledge(self) -> None:
        """Update knowledge base for all active agents"""
        if not self._initialized:
            await self.initialize()

        update_tasks = []
        for agent in self.agents.values():
            if agent.active:
                update_tasks.append(agent.update_knowledge())
        
        if update_tasks:
            await asyncio.gather(*update_tasks)
            self.logger.info("Successfully updated knowledge for all active agents")

    async def get_agent_configs(self) -> List[AgentConfig]:
        """Get configurations for all registered agents"""
        if not self._initialized:
            await self.initialize()

        try:
            database = self.cosmos_client.get_database_client("ai_agents")
            container = database.get_container_client("agent_configs")
            
            configs = []
            async for item in container.query_items(
                query="SELECT * FROM c",
                enable_cross_partition_query=True
            ):
                configs.append(AgentConfig(**item))
            
            return configs
            
        except Exception as e:
            self.logger.error(f"Failed to get agent configurations: {str(e)}")
            raise

    async def get_system_status(self) -> SystemStatus:
        """Get current system status"""
        if not self._initialized:
            await self.initialize()

        try:
            agents_status = {
                agent_id: agent.metrics
                for agent_id, agent in self.agents.items()
            }
            
            total_requests = sum(
                metrics.total_requests
                for metrics in agents_status.values()
            )
            
            return SystemStatus(
                version="1.0.0",
                environment=settings.ENVIRONMENT,
                active_agents=len([a for a in self.agents.values() if a.active]),
                total_requests_24h=total_requests,
                system_uptime=0.0,  # Implement uptime tracking
                agents_status=agents_status
            )
            
        except Exception as e:
            self.logger.error(f"Failed to get system status: {str(e)}")
            raise

    async def _load_registered_agents(self) -> None:
        """Load and initialize registered agents from database"""
        try:
            configs = await self.get_agent_configs()
            
            for config in configs:
                # Dynamically import agent class
                module_name = f"agents.{config.id}.agent"
                try:
                    module = importlib.import_module(module_name)
                    agent_class = getattr(module, f"{config.id.capitalize()}Agent")
                    await self.register_agent(agent_class, config)
                except (ImportError, AttributeError) as e:
                    self.logger.error(f"Failed to load agent {config.id}: {str(e)}")
                    continue
                    
        except Exception as e:
            self.logger.error(f"Failed to load registered agents: {str(e)}")
            raise
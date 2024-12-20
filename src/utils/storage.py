# src/utils/storage.py

from typing import Dict, Optional, Any, List
import logging
import asyncio
from datetime import datetime, timedelta
import json
from azure.cosmos import CosmosClient
from azure.cosmos.aio import CosmosClient as AsyncCosmosClient
from azure.cosmos.exceptions import CosmosHttpResponseError
import redis.asyncio as redis
from functools import wraps

logger = logging.getLogger(__name__)

def handle_db_errors(func):
    """Decorator for handling database errors"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except CosmosHttpResponseError as e:
            logger.error(f"Cosmos DB error in {func.__name__}: {str(e)}")
            raise
        except redis.RedisError as e:
            logger.error(f"Redis error in {func.__name__}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {str(e)}")
            raise
    return wrapper

class StorageManager:
    """Manager for database and cache connections"""
    
    def __init__(self):
        self.cosmos_client = None
        self.redis_client = None
        self._initialized = False
        self._lock = asyncio.Lock()
        
        # Default cache settings
        self.default_cache_ttl = 3600  # 1 hour
        self.cache_prefixes = {
            "agent_knowledge": "knowledge:",
            "legal_data": "legal:",
            "user_context": "user:",
            "metrics": "metrics:"
        }

    async def initialize(
        self,
        cosmos_connection_string: str,
        redis_url: str,
        database_name: str = "ai_agents"
    ):
        """Initialize database connections"""
        if self._initialized:
            return

        async with self._lock:
            if self._initialized:
                return
                
            try:
                # Initialize Cosmos DB
                self.cosmos_client = AsyncCosmosClient.from_connection_string(
                    cosmos_connection_string
                )
                self.database = self.cosmos_client.get_database_client(database_name)
                
                # Ensure required containers exist
                await self._ensure_containers()
                
                # Initialize Redis
                self.redis_client = await redis.from_url(
                    redis_url,
                    encoding="utf-8",
                    decode_responses=True
                )
                
                self._initialized = True
                logger.info("Storage manager initialized successfully")
                
            except Exception as e:
                logger.error(f"Failed to initialize storage manager: {str(e)}")
                raise

    async def close(self):
        """Close all database connections"""
        if self.cosmos_client:
            await self.cosmos_client.close()
        if self.redis_client:
            await self.redis_client.close()
        self._initialized = False

    @handle_db_errors
    async def store_agent_knowledge(
        self,
        agent_id: str,
        knowledge_type: str,
        data: Dict,
        ttl: Optional[int] = None
    ):
        """Store agent knowledge in both DB and cache"""
        container = self.database.get_container_client("knowledge_base")
        
        # Store in Cosmos DB
        document = {
            "id": f"{agent_id}_{knowledge_type}_{datetime.utcnow().timestamp()}",
            "agent_id": agent_id,
            "type": knowledge_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await container.upsert_item(document)
        
        # Store in Redis cache
        cache_key = f"{self.cache_prefixes['agent_knowledge']}{agent_id}:{knowledge_type}"
        await self.redis_client.set(
            cache_key,
            json.dumps(data),
            ex=ttl or self.default_cache_ttl
        )

    @handle_db_errors
    async def get_agent_knowledge(
        self,
        agent_id: str,
        knowledge_type: str
    ) -> Optional[Dict]:
        """Get agent knowledge from cache or DB"""
        # Try cache first
        cache_key = f"{self.cache_prefixes['agent_knowledge']}{agent_id}:{knowledge_type}"
        cached_data = await self.redis_client.get(cache_key)
        
        if cached_data:
            return json.loads(cached_data)
            
        # Fallback to DB
        container = self.database.get_container_client("knowledge_base")
        query = f"""
        SELECT TOP 1 c.data
        FROM c
        WHERE c.agent_id = @agent_id
        AND c.type = @type
        ORDER BY c.timestamp DESC
        """
        
        parameters = [
            {"name": "@agent_id", "value": agent_id},
            {"name": "@type", "value": knowledge_type}
        ]
        
        async for item in container.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=True
        ):
            # Update cache
            await self.redis_client.set(
                cache_key,
                json.dumps(item["data"]),
                ex=self.default_cache_ttl
            )
            return item["data"]
            
        return None

    @handle_db_errors
    async def store_metrics(self, metrics_data: Dict):
        """Store system metrics"""
        container = self.database.get_container_client("metrics")
        
        document = {
            "id": str(datetime.utcnow().timestamp()),
            "data": metrics_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await container.create_item(document)
        
        # Update cache with latest metrics
        cache_key = f"{self.cache_prefixes['metrics']}latest"
        await self.redis_client.set(
            cache_key,
            json.dumps(metrics_data),
            ex=300  # Cache metrics for 5 minutes
        )

    @handle_db_errors
    async def get_user_context(self, user_id: str) -> Optional[Dict]:
        """Get user context from cache or DB"""
        cache_key = f"{self.cache_prefixes['user_context']}{user_id}"
        
        # Try cache first
        cached_data = await self.redis_client.get(cache_key)
        if cached_data:
            return json.loads(cached_data)
            
        # Fallback to DB
        container = self.database.get_container_client("user_context")
        query = "SELECT * FROM c WHERE c.user_id = @user_id"
        
        async for item in container.query_items(
            query=query,
            parameters=[{"name": "@user_id", "value": user_id}],
            enable_cross_partition_query=True
        ):
            # Update cache
            await self.redis_client.set(
                cache_key,
                json.dumps(item),
                ex=3600  # Cache user context for 1 hour
            )
            return item
            
        return None

    @handle_db_errors
    async def cleanup_old_data(self, days: int = 30):
        """Clean up old data from the database"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        containers = ["metrics", "knowledge_base", "interactions"]
        for container_name in containers:
            container = self.database.get_container_client(container_name)
            query = f"""
            SELECT c.id
            FROM c
            WHERE c.timestamp < @cutoff_date
            """
            
            try:
                async for item in container.query_items(
                    query=query,
                    parameters=[{"name": "@cutoff_date", "value": cutoff_date.isoformat()}],
                    enable_cross_partition_query=True
                ):
                    await container.delete_item(item["id"], partition_key=item["id"])
                    
            except Exception as e:
                logger.error(f"Error cleaning up {container_name}: {str(e)}")

    async def _ensure_containers(self):
        """Ensure all required containers exist"""
        required_containers = {
            "knowledge_base": "/id",
            "metrics": "/id",
            "interactions": "/id",
            "user_context": "/user_id",
            "legal_data": "/id"
        }
        
        existing_containers = [
            container["id"] async for container in self.database.list_containers()
        ]
        
        for container_name, partition_key in required_containers.items():
            if container_name not in existing_containers:
                await self.database.create_container(
                    id=container_name,
                    partition_key=partition_key
                )
                logger.info(f"Created container: {container_name}")
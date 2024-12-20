# src/core/schemas.py

from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

class Message(BaseModel):
    """Schema for incoming messages"""
    agent_id: str
    content: str
    platform: str = Field(..., description="Platform source (e.g., 'whatsapp', 'telegram')")
    user_id: str
    context: Dict = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class AgentResponse(BaseModel):
    """Schema for agent responses"""
    content: str
    agent_id: str
    processing_time: float
    confidence_score: Optional[float] = None
    metadata: Dict = Field(default_factory=dict)

class AgentConfig(BaseModel):
    """Schema for agent configuration"""
    id: str
    name: str
    description: str
    model: str = "gpt-4"
    capabilities: List[str] = []
    active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        schema_extra = {
            "example": {
                "id": "shimon",
                "name": "שמעון",
                "description": "מומחה להוצאה לפועל",
                "model": "gpt-4",
                "capabilities": ["legal_advice", "document_analysis"],
                "active": True
            }
        }

class AgentMetrics(BaseModel):
    """Schema for agent metrics"""
    agent_id: str
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    average_response_time: float = 0.0
    last_active: datetime = Field(default_factory=datetime.utcnow)
    uptime_percentage: float = 100.0
    error_rate: float = 0.0

class SystemStatus(BaseModel):
    """Schema for system status"""
    version: str
    environment: str
    active_agents: int
    total_requests_24h: int
    system_uptime: float
    agents_status: Dict[str, AgentMetrics]
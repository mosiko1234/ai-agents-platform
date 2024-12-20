# src/utils/monitoring.py

from typing import Dict, List, Optional, Union
import logging
from datetime import datetime, timedelta
import asyncio
from dataclasses import dataclass, asdict
import json
from azure.monitor.opentelemetry import metrics
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

logger = logging.getLogger(__name__)

@dataclass
class SystemMetrics:
    """מטריקות מערכת בסיסיות"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    average_response_time: float = 0.0
    errors_last_hour: int = 0
    active_agents: int = 0
    uptime: float = 0.0
    cpu_usage: float = 0.0
    memory_usage: float = 0.0

@dataclass
class AgentMetrics:
    """מטריקות ספציפיות לסוכן"""
    agent_id: str
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    average_response_time: float = 0.0
    last_active: Optional[datetime] = None
    knowledge_update_time: Optional[datetime] = None
    error_rate: float = 0.0
    confidence_score: float = 0.0

class MetricsCollector:
    """אוסף ומנהל מטריקות מערכת"""
    
    def __init__(self):
        self.system_metrics = SystemMetrics()
        self.agent_metrics: Dict[str, AgentMetrics] = {}
        self.start_time = datetime.utcnow()
        
        # OpenTelemetry setup
        self.tracer = trace.get_tracer(__name__)
        self.meter = metrics.get_meter(__name__)
        
        # Create metrics
        self.request_counter = self.meter.create_counter(
            name="requests_total",
            description="Total number of requests processed"
        )
        
        self.response_time = self.meter.create_histogram(
            name="response_time_seconds",
            description="Response time in seconds"
        )
        
        self.error_counter = self.meter.create_counter(
            name="errors_total",
            description="Total number of errors"
        )

    async def initialize(self):
        """Initialize metrics collector"""
        try:
            # Start background tasks
            asyncio.create_task(self._periodic_cleanup())
            asyncio.create_task(self._export_metrics())
            logger.info("Metrics collector initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize metrics collector: {str(e)}")
            raise

    async def record_request(
        self,
        agent_id: str,
        success: bool,
        response_time: float,
        error: Optional[str] = None
    ):
        """Record request metrics"""
        try:
            with self.tracer.start_as_current_span("record_request") as span:
                # Update system metrics
                self.system_metrics.total_requests += 1
                if success:
                    self.system_metrics.successful_requests += 1
                else:
                    self.system_metrics.failed_requests += 1
                    if error:
                        span.set_attribute("error", error)
                
                # Update running average response time
                current_total = (
                    self.system_metrics.average_response_time *
                    (self.system_metrics.total_requests - 1)
                )
                self.system_metrics.average_response_time = (
                    (current_total + response_time) /
                    self.system_metrics.total_requests
                )
                
                # Update agent metrics
                if agent_id not in self.agent_metrics:
                    self.agent_metrics[agent_id] = AgentMetrics(agent_id=agent_id)
                
                agent = self.agent_metrics[agent_id]
                agent.total_requests += 1
                if success:
                    agent.successful_requests += 1
                else:
                    agent.failed_requests += 1
                
                agent.last_active = datetime.utcnow()
                agent.error_rate = agent.failed_requests / agent.total_requests
                
                # Calculate running average response time for agent
                agent_total = agent.average_response_time * (agent.total_requests - 1)
                agent.average_response_time = (agent_total + response_time) / agent.total_requests
                
                # Record OpenTelemetry metrics
                self.request_counter.add(1, {"agent_id": agent_id, "success": str(success)})
                self.response_time.record(response_time, {"agent_id": agent_id})
                if not success:
                    self.error_counter.add(1, {"agent_id": agent_id, "error_type": error or "unknown"})
                
                span.set_status(Status(StatusCode.OK))
                
        except Exception as e:
            logger.error(f"Error recording metrics: {str(e)}")
            if 'span' in locals():
                span.set_status(Status(StatusCode.ERROR))
                span.record_exception(e)

    async def record_agent_update(
        self,
        agent_id: str,
        confidence_score: float,
        knowledge_update_time: datetime
    ):
        """Record agent knowledge update metrics"""
        try:
            if agent_id not in self.agent_metrics:
                self.agent_metrics[agent_id] = AgentMetrics(agent_id=agent_id)
            
            agent = self.agent_metrics[agent_id]
            agent.knowledge_update_time = knowledge_update_time
            agent.confidence_score = confidence_score
            
        except Exception as e:
            logger.error(f"Error recording agent update: {str(e)}")

    async def get_system_health(self) -> Dict:
        """Get current system health status"""
        try:
            # Calculate uptime
            uptime = (datetime.utcnow() - self.start_time).total_seconds()
            error_rate = (
                self.system_metrics.failed_requests / self.system_metrics.total_requests
                if self.system_metrics.total_requests > 0 else 0
            )
            
            return {
                "status": "healthy" if error_rate < 0.1 else "degraded",
                "uptime": uptime,
                "error_rate": error_rate,
                "average_response_time": self.system_metrics.average_response_time,
                "active_agents": len(self.agent_metrics),
                "total_requests": self.system_metrics.total_requests,
                "last_updated": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting system health: {str(e)}")
            return {"status": "error", "error": str(e)}

    async def get_agent_stats(self, agent_id: str) -> Optional[Dict]:
        """Get statistics for specific agent"""
        try:
            if agent_id not in self.agent_metrics:
                return None
                
            agent = self.agent_metrics[agent_id]
            return asdict(agent)
            
        except Exception as e:
            logger.error(f"Error getting agent stats: {str(e)}")
            return None

    async def _periodic_cleanup(self):
        """Periodic cleanup of old metrics"""
        while True:
            try:
                # Clean up metrics older than 24 hours
                cutoff_time = datetime.utcnow() - timedelta(hours=24)
                
                # Reset hourly error count
                self.system_metrics.errors_last_hour = 0
                
                # Clean up inactive agents
                inactive_agents = [
                    agent_id for agent_id, metrics in self.agent_metrics.items()
                    if metrics.last_active and metrics.last_active < cutoff_time
                ]
                
                for agent_id in inactive_agents:
                    del self.agent_metrics[agent_id]
                
                await asyncio.sleep(3600)  # Run every hour
                
            except Exception as e:
                logger.error(f"Error in metrics cleanup: {str(e)}")
                await asyncio.sleep(60)  # Retry in a minute

    async def _export_metrics(self):
        """Export metrics to external monitoring system"""
        while True:
            try:
                # Prepare metrics for export
                metrics_data = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "system": asdict(self.system_metrics),
                    "agents": {
                        agent_id: asdict(metrics)
                        for agent_id, metrics in self.agent_metrics.items()
                    }
                }
                
                # Save metrics to file (for development)
                if logger.getEffectiveLevel() == logging.DEBUG:
                    with open("metrics.json", "w") as f:
                        json.dump(metrics_data, f, indent=2)
                
                await asyncio.sleep(300)  # Export every 5 minutes
                
            except Exception as e:
                logger.error(f"Error exporting metrics: {str(e)}")
                await asyncio.sleep(60)  # Retry in a minute
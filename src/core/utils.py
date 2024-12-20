from datetime import datetime
import hashlib
import json
from typing import Any, Dict

def generate_request_id(content: str, timestamp: datetime = None) -> str:
    """Generate unique request ID"""
    if timestamp is None:
        timestamp = datetime.utcnow()
    
    data = f"{content}{timestamp.isoformat()}"
    return hashlib.sha256(data.encode()).hexdigest()[:16]

def sanitize_input(content: str) -> str:
    """Sanitize user input"""
    # Add your input sanitization logic here
    return content.strip()

def format_error_message(error: Exception) -> Dict[str, Any]:
    """Format error message for API response"""
    return {
        "error": type(error).__name__,
        "message": str(error),
        "timestamp": datetime.utcnow().isoformat()
    }

def validate_agent_id(agent_id: str) -> bool:
    """Validate agent ID format"""
    return bool(agent_id and agent_id.isalnum() and len(agent_id) <= 32)

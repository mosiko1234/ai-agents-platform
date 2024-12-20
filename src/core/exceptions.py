# src/core/exceptions.py

class AgentError(Exception):
    """Base exception for agent-related errors"""
    def __init__(self, message: str, agent_id: str = None):
        self.message = message
        self.agent_id = agent_id
        super().__init__(self.message)

class AgentNotFoundError(AgentError):
    """Raised when an agent is not found"""
    pass

class AgentInitializationError(AgentError):
    """Raised when an agent fails to initialize"""
    pass

class KnowledgeBaseError(AgentError):
    """Raised when there's an error with the knowledge base"""
    pass

class OpenAIError(Exception):
    """Raised when there's an error with OpenAI API"""
    pass

class RateLimitError(Exception):
    """Raised when rate limit is exceeded"""
    pass

class AuthenticationError(Exception):
    """Raised when authentication fails"""
    pass
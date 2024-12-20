from typing import TypeVar, Dict, Any, Callable, Awaitable

AgentType = TypeVar("AgentType", bound="BaseAgent")
MessageHandler = Callable[[str, Dict[str, Any]], Awaitable[str]]

from .models import Handler, Response
from beartype import beartype
from beartype.typing import List



class HandlerSearchFailedError:
    """Класс для представления ошибки, когда handler не нашел подходящего response"""
    
    @beartype
    def __init__(self, handler: 'Handler', url: str, rejected_responses: List['Response'], duration: float = 0.0):
        self.handler = handler
        self.url = url
        self.rejected_responses = rejected_responses
        self.duration = duration
    
    def __str__(self):
        return f"HandlerSearchFailedError: Handler {self.handler.handler_type} not found suitable response for {self.url}. Rejected {len(self.rejected_responses)} responses."
    
    def __repr__(self):
        return f"HandlerSearchFailedError(handler={self.handler.handler_type}, url='{self.url}', rejected_count={len(self.rejected_responses)})"

class NetworkError:
    """Класс для представления сетевых ошибок"""
    
    @beartype
    def __init__(self, name: str, message: str, details: dict, timestamp: str, duration: float = 0.0):
        self.name = name
        self.message = message
        self.details = details
        self.timestamp = timestamp
        self.duration = duration
    
    def __str__(self):
        return f"NetworkError({self.name}: {self.message})"
    
    def __repr__(self):
        return f"NetworkError(name='{self.name}', message='{self.message}', timestamp='{self.timestamp}')"

from beartype import beartype


class NetworkError:
    """Класс для представления сетевых ошибок инъекций"""
    
    @beartype
    def __init__(self, name: str, message: str, details: dict, timestamp: str, duration: float = 0.0):
        self.name = name
        self.message = message
        self.details = details
        self.timestamp = timestamp
        self.duration = duration
    
    @beartype
    def __str__(self):
        return f"NetworkError({self.name}: {self.message})"
    
    @beartype
    def __repr__(self):
        return f"NetworkError(name='{self.name}', message='{self.message}', timestamp='{self.timestamp}')"

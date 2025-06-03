from beartype import beartype
from dataclasses import dataclass


@beartype
@dataclass(frozen=True)
class NetworkError:
    """Класс для представления сетевых ошибок инъекций"""
    
    name: str
    message: str
    details: dict
    timestamp: str
    duration: float

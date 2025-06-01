"""
Standard Open Inflation Package

Модульная библиотека для автоматизации веб-скрапинга и взаимодействия с API 
через управляемый браузер. Поддерживает прокси, инъекцию заголовков, 
обработку cookie и множественные методы получения данных.
"""

# Импорт утилит
from .tools import get_env_proxy, parse_proxy
from .parsers import parse_content_type, parse_response_data

# Импорт основных классов из модульной структуры
from .models import HttpMethod, Response, NetworkError, Handler, Request, HandlerSearchFailedError
from .browser import BaseAPI  
from .page import Page

# Версия пакета
__version__ = "0.1.2"

# Публичный API
__all__ = [
    # Утилиты
    'get_env_proxy', 
    'parse_proxy',
    'parse_content_type',
    'parse_response_data',
    
    # Основные классы
    'BaseAPI',
    'Page', 
    'Handler',
    
    # Модели данных
    'Request',
    'Response', 
    'NetworkError',
    'HandlerSearchFailedError',
    'HttpMethod'
]

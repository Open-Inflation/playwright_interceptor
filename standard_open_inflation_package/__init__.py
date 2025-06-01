"""
Standard Open Inflation Package

Модульная библиотека для автоматизации веб-скрапинга и взаимодействия с API 
через управляемый браузер. Поддерживает прокси, инъекцию заголовков, 
обработку cookie и множественные методы получения данных.
"""
# Импорт основных классов из модульной структуры
from .models import HttpMethod, Response, Handler, Request
from .browser import BaseAPI  
from .page import Page

# Версия пакета
__version__ = "0.1.2"

# Публичный API
__all__ = [
    # Основные классы
    'BaseAPI',
    'Page', 
    'Handler',
    
    # Модели данных
    'Request',
    'Response',
    'HttpMethod'
]

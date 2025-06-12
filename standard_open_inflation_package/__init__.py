"""
Standard Open Inflation Package

Модульная библиотека для автоматизации веб-скрапинга и взаимодействия с API 
через управляемый браузер. Поддерживает прокси, инъекцию заголовков, 
обработку cookie и множественные методы получения данных.
"""
# Импорт основных классов из модульной структуры
from .models import HttpMethod, Response, Request, Cookie
from .browser import BaseAPI
from .browser_engines import (
    BrowserEngine,
    BaseBrowserConfig,
    CamoufoxConfig,
    PlaywrightConfig,
)
from .page import Page

# Версия пакета
__version__ = "0.1.6"

# Публичный API
__all__ = [
    # Основные классы
    'BaseAPI',
    'BrowserEngine',
    'BaseBrowserConfig',
    'CamoufoxConfig',
    'PlaywrightConfig',
    'Page',
    
    # Модели данных
    'Request',
    'Response',
    'HttpMethod',
    'Cookie'
]

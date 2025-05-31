# Standard Open Inflation Package

[![GitHub Actions](https://github.com/Open-Inflation/standard_open_inflation_package/workflows/API%20Tests/badge.svg)](https://github.com/Open-Inflation/standard_open_inflation_package/actions/workflows/check_tests.yml?query=branch%3Amain)
![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)
![PyPI - Package Version](https://img.shields.io/pypi/v/standard_open_inflation_package?color=blue)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/standard_open_inflation_package?label=PyPi%20downloads)](https://pypi.org/project/standard_open_inflation_package/)
![License](https://img.shields.io/badge/license-MIT-green)
[![Discord](https://img.shields.io/discord/792572437292253224?label=Discord&labelColor=%232c2f33&color=%237289da)](https://discord.gg/UnJnGHNbBp)
[![Telegram](https://img.shields.io/badge/Telegram-24A1DE)](https://t.me/miskler_dev)

Библиотека для автоматизации веб-скрапинга и взаимодействия с API через управляемый браузер.

Основное назначение - обход антибот систем и работа с современными веб-приложениями, которые требуют выполнения JavaScript, установки сессионных cookie или специфичной логики авторизации.

## Ключевые возможности

- Автоматизированный браузер на основе Camoufox (Firefox) 
- Поддержка прокси с автоматическим определением из переменных окружения
- Инъекция заголовков и управление cookie
- Перехват сетевых запросов 
- Два метода получения данных: direct fetch и inject fetch
- Модульная архитектура
- Типизация с beartype
- Асинхронная архитектура

## Установка

```bash
pip install standard-open-inflation-package
```

## Быстрый старт

### Базовое использование

```python
import asyncio
from standard_open_inflation_package import BaseAPI, Handler

async def main():
    # Инициализация API с настройками
    api = BaseAPI(
        debug=True,               # Показывать браузер для отладки
        timeout=30.0,             # Таймаут запросов
        proxy="http://proxy:8080" # Опциональный прокси
    )
    
    # Создание сессии браузера
    await api.new_session(include_browser=True)
    
    try:
        # Простой запрос через direct fetch
        response = await api.new_direct_fetch(
            url="https://api.example.com/data",
            handler=Handler.JSON()  # Обработчик для JSON
        )
        
        print(f"Статус: {response.status}")
        print(f"Данные: {response.response}")
        print(f"Время выполнения: {response.duration:.3f}с")
    finally:
        await api.close(include_browser=True)

asyncio.run(main())
```

### Работа с сессионными токенами и авторизацией

Многие современные сайты требуют выполнения определенной логики для получения сессионных токенов перед API запросами.

```python
import asyncio
import json
from standard_open_inflation_package import BaseAPI, Handler, Request, NetworkError

class SessionBasedScraper:
    def __init__(self):
        self._page = None
        self.api = BaseAPI(
            debug=False,
            timeout=60.0,
            start_func=self.initialize_session,  # Инициализация сессии
            request_modifier_func=self.modify_request  # Модификация запросов inject_fetch
        )
        
    async def __aenter__(self):
        """
        Асинхронный контекстный менеджер для автоматического создания сессии.
        """
        self.api.new_session()
        return self
    
    async def __aexit__(self, exc_type, exc_value, traceback):
        """
        Асинхронный контекстный менеджер для автоматического закрытия сессии.
        """
        await self.api.close(include_browser=True)

    async def initialize_session(self, api: BaseAPI):
        """
        Выполняется после создания сессии браузера.
        Здесь мы загружаем главную страницу для получения сессионных токенов, либо инициализировать страницу для своих функций.
        """
        self._page = await api.new_page()
    
    async def modify_request(self, request: Request) -> Request:
        """
        Модифицирует объект Request перед каждым inject_fetch запросом.
        Получает объект Request и возвращает его модифицированную версию.
        """
        # Например логика сайта требует наличия токена в заголовке
        cookies = self.api.get_cookies()
        token = json.loads(cookies["session"])["access_token"]
        request.add_header("Authorization", f"Bearer {token}")

        # Можем добавить дополнительные параметры
        request.add_param("client", "web")
        
        return request
    
    async def get_api_data(self):
        """Получение данных через API с правильными заголовками"""
        # API запрос с автоматической подстановкой токена
        result = await page.inject_fetch("https://example.com/api/products")
        
        if isinstance(result, NetworkError):
            print(f"Ошибка сети: {result.name} - {result.message}")
            return None
        else:
            if result.status == 200:
                return result.response
            else:
                ...

# Использование
async def main():
    scraper = SessionBasedScraper()
    data = await scraper.get_api_data()
    
    if data:
        print(f"Получено {len(data.get('products', []))} товаров")
    else:
        print("Не удалось получить данные")

asyncio.run(main())
```

### Утилиты для работы с прокси

```python
from standard_open_inflation_package import get_env_proxy, parse_proxy
import logging

# Получение прокси из переменных окружения
proxy = get_env_proxy()
print(f"Прокси из env: {proxy}")

# Парсинг прокси-строки для Camoufox
logger = logging.getLogger(__name__)
parsed = parse_proxy("user:pass@proxy.example.com:8080", trust_env=True, logger=logger)
print(f"Парсед прокси: {parsed}")
```

### Генерация документации

```python
from standard_open_inflation_package.utils.docs_generator import generate_docs_index

# Генерация индексной страницы
success = generate_docs_index("docs")
```

Или через командную строку:
```bash
soip-generate-docs-index docs
```

## API Reference

### Основные классы

#### `BaseAPI`
Главный класс для управления браузером и сессиями.

**Параметры конструктора:**
- `debug: bool = False` - показывать браузер для отладки
- `proxy: str | None = None` - прокси-сервер
- `autoclose_browser: bool = False` - автоматически закрывать браузер
- `trust_env: bool = False` - доверять переменным окружения для прокси
- `timeout: float = 10.0` - таймаут операций в секундах
- `start_func: Callable | None = None` - **функция инициализации сессии**
- `request_modifier_func: Callable | None = None` - **функция модификации объекта Request**

**О start_func:**
Функция, которая выполняется один раз при создании новой сессии браузера. Используется для:
- Загрузки главной страницы для получения сессионных cookie
- Выполнения авторизации
- Инициализации токенов доступа
- Настройки состояния приложения

**О request_modifier_func:**
Функция, которая вызывается перед каждым `inject_fetch` запросом для модификации объекта Request. Используется для:
- Подстановки токенов авторизации из cookie
- Динамической генерации заголовков на основе состояния сессии
- Добавления/удаления параметров запроса
- Обхода защиты сайтов, требующих специфичные заголовки

**Основные методы:**
- `new_session(include_browser=False)` - создать новую сессию
- `new_page()` - создать новую страницу
- `new_direct_fetch(url, handler, wait_selector)` - быстрый запрос
- `get_cookies()` - получить текущие cookie
- `close(include_browser=False)` - закрыть соединения

#### `Page`
Класс для взаимодействия со страницами браузера.

**Основные методы:**
- `direct_fetch(url, handler, wait_selector)` - **прямой переход браузера на URL**
- `inject_fetch(url, method, body)` - **JavaScript-инъекция запроса без перехода**
- `close()` - закрыть страницу

**Разница между методами:**

`direct_fetch` - имитирует переход пользователя на страницу:
- Браузер реально переходит на указанный URL
- Выполняется весь JavaScript страницы
- Устанавливаются все cookie и состояние страницы
- Подходит для получения HTML контента и инициализации сессий

`inject_fetch` - выполняет API запрос через JavaScript:
- Браузер остается на текущей странице  
- Запрос выполняется в контексте текущей страницы
- Используются cookie и состояние текущей страницы
- Подходит для API запросов с сохранением контекста сессии

#### `Handler`
Указывает direct_fetch какой контент требуется получить.
Перехватывает и возвращает первый подходящий элемент.

**Статические методы:**
- `Handler.MAIN()` - основная страница (HTML/JSON/изображения)
- `Handler.JSON()` - JSON API
- `Handler.JS()` - JavaScript файлы
- `Handler.CSS()` - CSS файлы
- `Handler.IMAGE()` - изображения
- `Handler.CAPTURE()` - любой контент (в том числе MAIN)

Каждый из перечисленных принимает `target_url` (str) и `type` (HttpMethod).

#### `HttpMethod`
Enum перечисление HTTP методов: GET, POST, PUT, DELETE, PATCH, HEAD, OPTIONS.

#### `Response`
Объект ответа с данными запроса.

**Атрибуты:**
- `status: int` - HTTP статус
- `request_headers: dict` - заголовки запроса
- `response_headers: dict` - заголовки ответа  
- `response: Union[dict, list, str, BytesIO]` - данные ответа
- `duration: float` - время выполнения в секундах

#### `NetworkError`
Объект ошибки сети.

**Атрибуты:**
- `name: str` - имя ошибки
- `message: str` - сообщение об ошибке
- `details: dict` - детали ошибки
- `timestamp: str` - время возникновения
- `duration: float` - время выполнения в секундах

### Утилиты

#### `get_env_proxy() -> Union[str, None]`
Получает прокси из переменных окружения (HTTP_PROXY, HTTPS_PROXY, http_proxy, https_proxy).

#### `parse_proxy(proxy_str, trust_env, logger) -> Union[Dict[str, str], None]`
Парсит строку прокси в словарь для Camoufox. Поддерживает форматы:
- `host:port`
- `user:pass@host:port`
- `http://user:pass@host:port`

#### `generate_docs_index(docs_dir: str = "docs") -> bool`
Генерирует HTML индексную страницу для директории с документацией.

## Примеры использования

### Мониторинг API с обработкой ошибок

```python
import asyncio
from standard_open_inflation_package import BaseAPI, Handler, NetworkError

async def monitor_api():
    api = BaseAPI(timeout=30.0)
    await api.new_session(include_browser=True)
    
    page = await api.new_page()
    
    try:
        # Попытка API запроса
        result = await page.inject_fetch(
            url="https://api.example.com/status",
            method="GET"
        )
        
        if isinstance(result, NetworkError):
            print(f"Ошибка API: {result.name} - {result.message}")
            print(f"Детали: {result.details}")
        else:
            print(f"API работает: {result.response}")
            
    finally:
        await page.close()
        await api.close(include_browser=True)

asyncio.run(monitor_api())
```

### Скрапинг с ожиданием динамического контента

```python
import asyncio
from standard_open_inflation_package import BaseAPI, Handler

async def scrape_dynamic_content():
    api = BaseAPI(debug=True)
    await api.new_session(include_browser=True)
    
    try:
        # Получаем данные с ожиданием загрузки
        response = await api.new_direct_fetch(
            url="https://example.com/dynamic-page",
            handler=Handler.MAIN(),
            wait_selector=".dynamic-content"  # Ждем появления элемента
        )
        
        print(f"Контент загружен за {response.duration:.2f}с")
        print(f"Размер: {len(response.response)} символов")
        
    finally:
        await api.close(include_browser=True)

asyncio.run(scrape_dynamic_content())
```

## Разработка и тестирование

```bash
# Клонирование репозитория
git clone https://github.com/Open-Inflation/standard_open_inflation_package.git
cd standard_open_inflation_package

# Установка в режиме разработки
pip install -e .

# Запуск тестов
pytest
```

## Конфигурация

Все константы и настройки централизованы в модуле `config.py`:

- Таймауты и лимиты
- Content-Type константы  
- Сообщения об ошибках и логирования
- Пути к файлам и расширения
- Значения по умолчанию

## Архитектура

Библиотека построена на модульной архитектуре:

- **`browser.py`** - управление браузером и сессиями
- **`page.py`** - взаимодействие со страницами и выполнение запросов
- **`models.py`** - модели данных (Request, Response, NetworkError, Handler, HttpMethod)
- **`tools.py`** - утилиты для работы с прокси и парсинга данных
- **`config.py`** - централизованная конфигурация констант
- **`utils/`** - дополнительные утилиты (генератор index страницы документации scheme for humans)

# NetworkInterceptor

[![GitHub Actions](https://github.com/Open-Inflation/standard_open_inflation_package/workflows/API%20Tests/badge.svg)](https://github.com/Open-Inflation/standard_open_inflation_package/actions/workflows/check_tests.yml?query=branch%3Amain)
![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)
![PyPI - Package Version](https://img.shields.io/pypi/v/standard_open_inflation_package?color=blue)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/standard_open_inflation_package?label=PyPi%20downloads)](https://pypi.org/project/standard_open_inflation_package/)
![License](https://img.shields.io/badge/license-MIT-green)
[![Discord](https://img.shields.io/discord/792572437292253224?label=Discord&labelColor=%232c2f33&color=%237289da)](https://discord.gg/UnJnGHNbBp)
[![Telegram](https://img.shields.io/badge/Telegram-24A1DE)](https://t.me/miskler_dev)

**Мощный addon для Playwright, предоставляющий продвинутые возможности перехвата и модификации HTTP-запросов и ответов.**

## ✨ Возможности

- 🔧 **Модификация запросов** - Изменяйте HTTP-запросы перед отправкой на сервер
- 🔄 **Модификация ответов** - Изменяйте ответы сервера перед передачей в браузер  
- 🎯 **Гибкая фильтрация** - Захватывайте только нужные запросы по URL, методу и типу контента
- 🚀 **Асинхронная поддержка** - Работа с sync и async функциями модификации
- 🔗 **Множественные хендлеры** - Последовательная обработка запросов несколькими хендлерами
- 📊 **Детальная аналитика** - Получайте подробную информацию о перехваченных запросах
- 🛡️ **Типобезопасность** - Полная поддержка типов с beartype
- ⚡ **Новый API** - Прямой доступ к свойствам для максимальной производительности

## 🆕 Что нового в версии 2.0

- **Обновленный Request API**: Прямой доступ к свойствам (`request.headers["key"] = "value"`)
- **Новый Response API**: `content` поле с bytes + `content_parse()` метод для парсинга
- **Улучшенная производительность**: Меньше вызовов методов, более быстрая модификация
- **Лучшая типобезопасность**: Полное покрытие типов с beartype

> 📖 **Миграция с версии 1.x**: См. [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md) для подробностей обновления

## 📦 Установка

```bash
pip install standard-open-inflation-package
```

## 🚀 Быстрый старт

```python
from playwright.async_api import async_playwright
from standard_open_inflation_package import NetworkInterceptor, Handler, Execute, Request, Response
import asyncio

async def main():
    async with async_playwright() as pw:
        browser = await pw.firefox.launch()
        page = await browser.new_page()

        interceptor = NetworkInterceptor(page)
        
        # Перехватываем и модифицируем запросы и ответы
        handler = Handler.ALL(execute=Execute.ALL(
            request_modify=modify_request,
            response_modify=modify_response,
            max_modifications=5,
            max_responses=2
        ))
        
        # Запускаем перехват
        results, _ = await asyncio.gather(
            interceptor.execute(handler),
            page.goto("https://httpbin.org/get")
        )
        
        print(f"Результаты: {results}")
        await browser.close()

def modify_request(request: Request) -> Request:
    """Модифицирует запрос перед отправкой"""
    # Новый API v2.0 - прямой доступ к свойствам
    request.headers["X-Custom-Header"] = "ModifiedByInterceptor"
    request.params["intercepted"] = "true"
    return request

def modify_response(response: Response) -> Response:
    """Модифицирует ответ после получения"""
    response.response_headers["X-Response-Modified"] = "true"
    
    # Парсим содержимое и модифицируем JSON
    parsed_content = response.content_parse()
    if isinstance(parsed_content, dict):
        parsed_content["_intercepted"] = True
        # Обновляем содержимое
        import json
        response.content = json.dumps(parsed_content).encode('utf-8')
    
    return response

if __name__ == "__main__":
    asyncio.run(main())
```

## 📚 Основные компоненты

### 🎛️ NetworkInterceptor

Главный класс для перехвата HTTP-трафика на странице Playwright.

```python
from standard_open_inflation_package import NetworkInterceptor

# Создание перехватчика
interceptor = NetworkInterceptor(page, logger=custom_logger)

# Выполнение перехвата
results = await interceptor.execute(handlers, timeout=30.0)
```

**Параметры:**
- `page` - Страница Playwright для перехвата
- `logger` - Опциональный логгер (по умолчанию создается автоматически)

**Методы:**
- `execute(handlers, timeout=10.0)` - Запускает перехват с указанными хендлерами

### 🎯 Handler

Определяет правила захвата и обработки запросов.

```python
from standard_open_inflation_package import Handler, Execute, ExpectedContentType, HttpMethod

# Различные типы хендлеров
handler_return = Handler.RETURN(
    expected_content=ExpectedContentType.JSON,
    startswith_url="https://api.example.com",
    method=HttpMethod.GET,
    execute=Execute.RETURN(max_responses=3)
)

handler_modify = Handler.MODIFY(
    expected_content=ExpectedContentType.ANY,
    execute=Execute.MODIFY(
        request_modify=my_request_modifier,
        response_modify=my_response_modifier,
        max_modifications=5
    )
)

handler_all = Handler.ALL(
    slug="my_handler",
    expected_content=ExpectedContentType.JSON,
    startswith_url="https://api.example.com",
    method=HttpMethod.POST,
    execute=Execute.ALL(
        request_modify=my_request_modifier,
        response_modify=my_response_modifier,
        max_modifications=3,
        max_responses=2
    )
)
```

**Параметры:**
- `expected_content` - Тип ожидаемого контента (JSON, JS, CSS, IMAGE, etc.)
- `startswith_url` - Фильтр по началу URL
- `method` - HTTP-метод для фильтрации
- `execute` - Конфигурация выполнения
- `slug` - Уникальный идентификатор хендлера

**Фабричные методы:**
- `Handler.RETURN()` - Только перехват без модификации
- `Handler.MODIFY()` - Только модификация без возврата данных
- `Handler.ALL()` - Перехват и модификация
- `Handler.NONE()` - Пустой хендлер

### ⚙️ Execute

Конфигурирует поведение хендлера.

```python
from standard_open_inflation_package import Execute

# Только перехват
execute_return = Execute.RETURN(max_responses=5)

# Только модификация
execute_modify = Execute.MODIFY(
    request_modify=modify_request,
    max_modifications=3
)

execute_modify_response = Execute.MODIFY(
    response_modify=modify_response,
    max_modifications=2
)

# Перехват и модификация
execute_all = Execute.ALL(
    request_modify=modify_request,
    response_modify=modify_response,
    max_modifications=5,
    max_responses=3
)
```

**Режимы работы:**
- `RETURN` - Перехватывает запросы и возвращает данные
- `MODIFY` - Модифицирует запросы/ответы (требуется хотя бы один из модификаторов)
- `ALL` - Комбинирует перехват и модификацию

**Параметры:**
- `request_modify` - Функция для модификации запросов
- `response_modify` - Функция для модификации ответов
- `max_modifications` - Максимальное количество модификаций
- `max_responses` - Максимальное количество перехваченных ответов

### 📨 Request

Представляет HTTP-запрос с возможностью модификации.

```python
from standard_open_inflation_package import Request, HttpMethod

# Создание запроса
request = Request(
    url="https://api.example.com/users",
    headers={"Authorization": "Bearer token"},
    params={"page": "1", "limit": "10"},
    body={"name": "John"},
    method=HttpMethod.POST
)

# Модификация запроса
request.add_header("X-Custom", "value")
request.add_param("filter", "active")
request.set_method(HttpMethod.PUT)
request.set_body({"updated": "data"})

# Получение финального URL
final_url = request.real_url  # URL с параметрами
```

**Свойства:**
- `url` - Базовый URL без параметров
- `real_url` - Финальный URL с параметрами
- `headers` - Словарь заголовков
- `params` - Словарь параметров запроса
- `body` - Тело запроса (dict или str)
- `method` - HTTP-метод

**Методы модификации:**
- `add_header(name, value)` - Добавить заголовок
- `add_headers(headers_dict)` - Добавить множественные заголовки
- `add_param(name, value)` - Добавить параметр
- `add_params(params_dict)` - Добавить множественные параметры
- `remove_header(name)` - Удалить заголовок
- `remove_param(name)` - Удалить параметр
- `set_body(body)` - Установить тело запроса
- `set_method(method)` - Установить HTTP-метод

### 📨 Response

Представляет HTTP-ответ с возможностью модификации.

```python
from standard_open_inflation_package import Response

# Response создается автоматически перехватчиком
def modify_response(response: Response) -> Response:
    # Модификация заголовков
    response.response_headers["X-Modified"] = "true"
    response.response_headers["Cache-Control"] = "no-cache"
    
    # Модификация JSON-контента
    parsed_content = response.content_parse()
    if isinstance(parsed_content, dict):
        parsed_content["_intercepted"] = True
        parsed_content["_timestamp"] = "2025-06-15"
        # Обновляем содержимое
        import json
        response.content = json.dumps(parsed_content).encode('utf-8')
    
    return response
```

**Свойства:**
- `status` - HTTP-статус код
- `url` - URL запроса
- `request_headers` - Заголовки запроса
- `response_headers` - Заголовки ответа (можно модифицировать)
- `content` - Содержимое ответа в виде bytes
- `duration` - Время выполнения запроса в секундах

**Методы:**
- `content_parse()` - Парсит содержимое в Python-объекты (dict, list, str, BytesIO)

### 🏷️ Enum классы

#### ExpectedContentType
```python
from standard_open_inflation_package import ExpectedContentType

ExpectedContentType.JSON        # application/json
ExpectedContentType.JS          # application/javascript
ExpectedContentType.CSS         # text/css
ExpectedContentType.IMAGE       # image/*
ExpectedContentType.VIDEO       # video/*
ExpectedContentType.AUDIO       # audio/*
ExpectedContentType.FONT        # font/*
ExpectedContentType.APPLICATION # application/*
ExpectedContentType.ARCHIVE     # archive formats
ExpectedContentType.TEXT        # text/*
ExpectedContentType.ANY         # любой тип
```

#### HttpMethod
```python
from standard_open_inflation_package import HttpMethod

HttpMethod.GET
HttpMethod.POST  
HttpMethod.PUT
HttpMethod.DELETE
HttpMethod.PATCH
HttpMethod.HEAD
HttpMethod.OPTIONS
HttpMethod.ANY      # любой метод
```

### 📊 Результаты

Перехватчик возвращает список результатов для каждого хендлера:

```python
# HandlerSearchSuccess - успешный перехват
class HandlerSearchSuccess:
    responses: List[Response]  # Перехваченные ответы
    duration: float           # Время работы хендлера
    handler_slug: str        # Идентификатор хендлера

# HandlerSearchFailed - неудачный перехват  
class HandlerSearchFailed:
    rejected_responses: List[Response]  # Отклоненные ответы
    duration: float                    # Время работы хендлера
    handler_slug: str                 # Идентификатор хендлера
```

## 💡 Примеры использования

### 🔐 Добавление аутентификации к запросам

```python
def add_auth(request: Request) -> Request:
    """Добавляет токен аутентификации ко всем API запросам"""
    if "/api/" in request.url:
        request.add_header("Authorization", "Bearer your-token")
    return request

handler = Handler.ALL(
    startswith_url="https://api.example.com",
    execute=Execute.MODIFY(request_modify=add_auth, max_modifications=10)
)
```

### 📊 Добавление аналитики к ответам

```python
async def add_analytics(response: Response) -> Response:
    """Добавляет аналитические данные к JSON ответам"""
    parsed_content = response.content_parse()
    if isinstance(parsed_content, dict):
        parsed_content["_analytics"] = {
            "intercepted_at": datetime.now().isoformat(),
            "response_time_ms": response.duration * 1000,
            "status_code": response.status
        }
        # Обновляем содержимое
        import json
        response.content = json.dumps(parsed_content).encode('utf-8')
    return response

handler = Handler.ALL(
    expected_content=ExpectedContentType.JSON,
    execute=Execute.ALL(
        response_modify=add_analytics,
        max_modifications=5,
        max_responses=3
    )
)
```

### 🛡️ Добавление заголовков безопасности

```python
def add_security_headers(response: Response) -> Response:
    """Добавляет заголовки безопасности ко всем ответам"""
    security_headers = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY", 
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains"
    }
    response.response_headers.update(security_headers)
    return response

handler = Handler.ALL(
    execute=Execute.MODIFY(response_modify=add_security_headers, max_modifications=20)
)
```

### 🔍 Перехват и анализ API вызовов

```python
captured_api_calls = []

def capture_api_response(response: Response) -> Response:
    """Сохраняет информацию о всех API вызовах"""
    if "/api/" in response.url:
        captured_api_calls.append({
            "url": response.url,
            "status": response.status,
            "duration": response.duration,
            "response_size": len(response.content) if response.content else 0
        })
    return response

handler = Handler.ALL(
    startswith_url="https://api.example.com",
    execute=Execute.ALL(
        response_modify=capture_api_response,
        max_modifications=50,
        max_responses=10
    )
)

# После выполнения
print(f"Перехвачено {len(captured_api_calls)} API вызовов")
```

### 🚀 Множественные хендлеры

```python
async def run_multiple_handlers():
    """Демонстрация работы с несколькими хендлерами"""
    
    # Хендлер для модификации запросов
    request_handler = Handler.MODIFY(
        slug="request_modifier",
        execute=Execute.MODIFY(
            request_modify=add_tracking,
            max_modifications=10
        )
    )
    
    # Хендлер для модификации ответов
    response_handler = Handler.MODIFY(
        slug="response_modifier", 
        expected_content=ExpectedContentType.JSON,
        execute=Execute.MODIFY(
            response_modify=add_metadata,
            max_modifications=10
        )
    )
    
    # Хендлер для сбора данных
    collector_handler = Handler.ALL(
        slug="data_collector",
        startswith_url="https://api.example.com",
        execute=Execute.ALL(
            response_modify=collect_data,
            max_modifications=5,
            max_responses=5
        )
    )
    
    # Запуск всех хендлеров
    results = await interceptor.execute([
        request_handler,
        response_handler, 
        collector_handler
    ])
    
    for result in results:
        print(f"Хендлер {result.handler_slug}: {len(result.responses)} ответов за {result.duration:.2f}с")
```

## 🔧 Расширенные возможности

### ⚡ Асинхронные модификаторы

```python
async def async_request_modifier(request: Request) -> Request:
    """Асинхронная модификация запроса"""
    # Можно выполнять асинхронные операции
    await asyncio.sleep(0.01)  # Имитация async операции
    
    request.add_header("X-Async-Modified", "true")
    return request

async def async_response_modifier(response: Response) -> Response:
    """Асинхронная модификация ответа"""
    # Асинхронная обработка данных
    parsed_content = response.content_parse()
    if isinstance(parsed_content, dict):
        # Например, валидация или обогащение данных
        parsed_content["_processed_async"] = True
        # Обновляем содержимое
        import json
        response.content = json.dumps(parsed_content).encode('utf-8')
    
    return response

handler = Handler.ALL(
    execute=Execute.ALL(
        request_modify=async_request_modifier,
        response_modify=async_response_modifier,
        max_modifications=5,
        max_responses=3
    )
)
```

### 🎯 Сложная фильтрация

```python
# Перехват только POST запросов к API аутентификации
auth_handler = Handler.ALL(
    method=HttpMethod.POST,
    startswith_url="https://api.example.com/auth",
    expected_content=ExpectedContentType.JSON,
    execute=Execute.ALL(
        request_modify=log_auth_requests,
        response_modify=process_auth_response,
        max_modifications=3,
        max_responses=1
    )
)

# Перехват всех изображений
image_handler = Handler.RETURN(
    expected_content=ExpectedContentType.IMAGE,
    execute=Execute.RETURN(max_responses=10)
)

# Модификация всех CSS файлов
css_handler = Handler.MODIFY(
    expected_content=ExpectedContentType.CSS,
    execute=Execute.MODIFY(
        response_modify=optimize_css,
        max_modifications=5
    )
)
```

## 🐛 Обработка ошибок

```python
def safe_request_modifier(request: Request) -> Request:
    """Безопасная модификация запроса с обработкой ошибок"""
    try:
        # Ваша логика модификации
        request.add_header("X-Safe-Modified", "true")
        return request
    except Exception as e:
        print(f"Ошибка модификации запроса: {e}")
        return request  # Возвращаем немодифицированный запрос

def safe_response_modifier(response: Response) -> Response:
    """Безопасная модификация ответа с обработкой ошибок"""
    try:
        parsed_content = response.content_parse()
        if isinstance(parsed_content, dict):
            parsed_content["_safe_modified"] = True
            # Обновляем содержимое
            import json
            response.content = json.dumps(parsed_content).encode('utf-8')
        return response
    except Exception as e:
        print(f"Ошибка модификации ответа: {e}")
        return response  # Возвращаем немодифицированный ответ
```

## 📝 Логирование

```python
import logging

# Настройка кастомного логгера
logger = logging.getLogger("my_interceptor")
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# Использование с кастомным логгером
interceptor = NetworkInterceptor(page, logger=logger)
```

## ⚠️ Важные замечания

1. **Последовательность модификаций**: При использовании множественных хендлеров модификации применяются последовательно в порядке следования хендлеров.

2. **Валидация Execute**: Для режимов `MODIFY` и `ALL` требуется указать хотя бы один из модификаторов (`request_modify` или `response_modify`).

3. **Уникальные slug**: При использовании множественных хендлеров убедитесь, что у каждого уникальный `slug`.

4. **Производительность**: Модификации происходят синхронно с обработкой запросов, поэтому избегайте тяжелых операций в модификаторах.

5. **Типобезопасность**: Все функции модификации должны возвращать объекты соответствующих типов (`Request` или `Response`).

## 📄 Лицензия

MIT License - подробности в файле [LICENSE](LICENSE).

## 🤝 Поддержка

- 💬 [Discord сообщество](https://discord.gg/UnJnGHNbBp)
- 📱 [Telegram канал](https://t.me/miskler_dev)
- 🐛 [Сообщить об ошибке](https://github.com/Open-Inflation/standard_open_inflation_package/issues)

## 🏆 Благодарности

Спасибо всем участникам проекта за вклад в развитие библиотеки! 🙏

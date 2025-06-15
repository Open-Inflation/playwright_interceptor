# Playwright Interceptor

[![GitHub Actions](https://github.com/Open-Inflation/playwright_interceptor/workflows/Tests/badge.svg)](https://github.com/Open-Inflation/playwright_interceptor/actions/workflows/check_tests.yml?query=branch%3Amain)
![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)
![PyPI - Package Version](https://img.shields.io/pypi/v/playwright_interceptor?color=blue)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/playwright_interceptor?label=PyPi%20downloads)](https://pypi.org/project/playwright_interceptor/)
![License](https://img.shields.io/badge/license-MIT-green)
[![Discord](https://img.shields.io/discord/792572437292253224?label=Discord&labelColor=%232c2f33&color=%237289da)](https://discord.gg/UnJnGHNbBp)
[![Telegram](https://img.shields.io/badge/Telegram-24A1DE)](https://t.me/miskler_dev)

**Addon for Playwright for intercepting and modifying HTTP requests and responses.**

## Features

- Request modification before sending to the server
- Server response modification before passing to the browser
- Request filtering by URL, method, and content type
- Support for synchronous and asynchronous modification functions
- Processing requests with multiple handlers
- Obtaining information about intercepted requests
- Type safety with beartype
- Direct access to request and response properties

## Installation

```bash
pip install playwright_interceptor
```

## Usage

```python
from playwright.async_api import async_playwright
from playwright_interceptor import NetworkInterceptor, Handler, Execute, Request, Response
import asyncio

async def main():
    async with async_playwright() as pw:
        browser = await pw.firefox.launch()
        page = await browser.new_page()

        interceptor = NetworkInterceptor(page)
        
        # Intercepting and modifying requests and responses
        handler = Handler.ALL(execute=Execute.ALL(
            request_modify=modify_request,
            response_modify=modify_response,
            max_modifications=5,
            max_responses=2
        ))
        
        # Starting interception
        results, _ = await asyncio.gather(
            interceptor.execute([handler]),
            page.goto("https://httpbin.org/get")
        )
        
        print(f"Results: {results}")
        await browser.close()

def modify_request(request: Request) -> Request:
    """Modifies request before sending"""
    request.headers["X-Custom-Header"] = "ModifiedByInterceptor"
    request.params["intercepted"] = "true"
    return request

def modify_response(response: Response) -> Response:
    """Modifies response after receiving"""
    response.response_headers["X-Response-Modified"] = "true"
    
    # Parsing and modifying JSON
    parsed_content = response.content_parse()
    if isinstance(parsed_content, dict):
        parsed_content["_intercepted"] = True
        # Updating content
        import json
        response.content = json.dumps(parsed_content).encode('utf-8')
    
    return response

if __name__ == "__main__":
    asyncio.run(main())
```

## Components

### NetworkInterceptor

Class for intercepting HTTP traffic:

```python
from playwright_interceptor import NetworkInterceptor

interceptor = NetworkInterceptor(page, logger=custom_logger)
results = await interceptor.execute(handlers, timeout=10.0)
```

**Parameters:**
- `page` - Playwright page
- `logger` - Optional logger

**Methods:**
- `execute(handlers, timeout=10.0)` - Start interception with specified handlers

### Handler

Rules for capturing and processing requests:

```python
from playwright_interceptor import Handler, Execute, ExpectedContentType, HttpMethod

handler_all = Handler.ALL(
    expected_content=ExpectedContentType.JSON,
    startswith_url="https://api.example.com",
    method=HttpMethod.GET,
    execute=Execute.RETURN(max_responses=3)
)

handler_modify = Handler.ALL(
    expected_content=ExpectedContentType.ANY,
    execute=Execute.MODIFY(
        request_modify=my_request_modifier,
        response_modify=my_response_modifier,
        max_modifications=5
    )
)

handler_combined = Handler.ALL(
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

**Parameters:**
- `expected_content` - Expected content type
- `startswith_url` - Filter by URL beginning
- `method` - HTTP method for filtering
- `execute` - Execution configuration
- `slug` - Handler identifier

**Factory methods:**
- `Handler.ALL()` - Universal handler for all types of requests
- `Handler.MAIN()` - Handler for main page requests
- `Handler.SIDE()` - Handler for side resource requests  
- `Handler.NONE()` - Empty handler

### Execute

Handler behavior configuration:

```python
from playwright_interceptor import Execute

execute_return = Execute.RETURN(max_responses=5)

execute_modify = Execute.MODIFY(
    request_modify=modify_request,
    max_modifications=3
)

execute_all = Execute.ALL(
    request_modify=modify_request,
    response_modify=modify_response,
    max_modifications=5,
    max_responses=3
)
```

**Modes:**
- `RETURN` - Request interception
- `MODIFY` - Request/response modification
- `ALL` - Combination of interception and modification

**Parameters:**
- `request_modify` - Request modification function
- `response_modify` - Response modification function
- `max_modifications` - Maximum number of modifications
- `max_responses` - Maximum number of intercepted responses

### Request

HTTP request representation:

```python
from playwright_interceptor import Request, HttpMethod

request = Request(
    url="https://api.example.com/users",
    headers={"Authorization": "Bearer token"},
    params={"page": "1", "limit": "10"},
    body={"name": "John"},
    method=HttpMethod.POST
)

# Modification (direct field access)
request.headers["X-Custom"] = "value"
request.params["filter"] = "active"
request.method = HttpMethod.PUT
request.body = {"updated": "data"}

# URL with parameters
final_url = request.real_url
```

**Properties:**
- `url` - Base URL
- `real_url` - URL with parameters (read-only property)
- `base_url` - URL without parameters (read-only property)
- `headers` - Headers dictionary
- `params` - Request parameters dictionary
- `body` - Request body
- `method` - HTTP method

### Response

HTTP response representation:

```python
from playwright_interceptor import Response

def modify_response(response: Response) -> Response:
    response.response_headers["X-Modified"] = "true"
    
    parsed_content = response.content_parse()
    if isinstance(parsed_content, dict):
        parsed_content["_intercepted"] = True
        import json
        response.content = json.dumps(parsed_content).encode('utf-8')
    
    return response
```

**Properties:**
- `status` - HTTP status code
- `url` - Request URL
- `request_headers` - Request headers
- `response_headers` - Response headers
- `content` - Response content (bytes)
- `duration` - Request execution time

**Methods:**
- `content_parse()` - Parse content into objects

### Enum Classes

```python
from standard_open_inflation_package import ExpectedContentType, HttpMethod

# Content types
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
ExpectedContentType.ANY         # any type

# HTTP methods
HttpMethod.GET
HttpMethod.POST  
HttpMethod.PUT
HttpMethod.DELETE
HttpMethod.PATCH
HttpMethod.HEAD
HttpMethod.OPTIONS
HttpMethod.ANY
```

## Examples

### Adding Authentication

```python
def add_auth(request: Request) -> Request:
    if "/api/" in request.url:
        request.headers["Authorization"] = "Bearer your-token"
    return request

handler = Handler.ALL(
    startswith_url="https://api.example.com",
    execute=Execute.MODIFY(request_modify=add_auth, max_modifications=10)
)
```

### Adding Analytics

```python
from datetime import datetime

async def add_analytics(response: Response) -> Response:
    parsed_content = response.content_parse()
    if isinstance(parsed_content, dict):
        parsed_content["_analytics"] = {
            "intercepted_at": datetime.now().isoformat(),
            "response_time_ms": response.duration * 1000,
            "status_code": response.status
        }
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

### Multiple Handlers

```python
async def run_multiple_handlers():
    request_handler = Handler.ALL(
        slug="request_modifier",
        execute=Execute.MODIFY(
            request_modify=add_tracking,
            max_modifications=10
        )
    )
    
    response_handler = Handler.ALL(
        slug="response_modifier", 
        expected_content=ExpectedContentType.JSON,
        execute=Execute.MODIFY(
            response_modify=add_metadata,
            max_modifications=10
        )
    )
    
    collector_handler = Handler.ALL(
        slug="data_collector",
        startswith_url="https://api.example.com",
        execute=Execute.ALL(
            response_modify=collect_data,
            max_modifications=5,
            max_responses=5
        )
    )
    
    results = await interceptor.execute([
        request_handler,
        response_handler, 
        collector_handler
    ])
```

### Asynchronous Modifiers

```python
async def async_request_modifier(request: Request) -> Request:
    await asyncio.sleep(0.01)
    request.headers["X-Async-Modified"] = "true"
    return request

async def async_response_modifier(response: Response) -> Response:
    parsed_content = response.content_parse()
    if isinstance(parsed_content, dict):
        parsed_content["_processed_async"] = True
        import json
        response.content = json.dumps(parsed_content).encode('utf-8')
    return response
```

### Error Handling

```python
def safe_modifier(response: Response) -> Response:
    try:
        parsed_content = response.content_parse()
        if isinstance(parsed_content, dict):
            parsed_content["_modified"] = True
            import json
            response.content = json.dumps(parsed_content).encode('utf-8')
        return response
    except Exception as e:
        print(f"Modification error: {e}")
        return response
```

## Important Notes

1. When using multiple handlers, modifications are applied sequentially
2. For `MODIFY` and `ALL` modes, at least one of the modifiers is required
3. With multiple handlers, unique `slug` values are required
4. Avoid heavy operations in modifiers

## License

MIT License

## Support

- [Discord](https://discord.gg/UnJnGHNbBp)
- [Telegram](https://t.me/miskler_dev)
- [GitHub Issues](https://github.com/Open-Inflation/playwright_interceptor/issues)

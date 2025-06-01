import pytest
from standard_open_inflation_package import BaseAPI, Handler, Response
from standard_open_inflation_package.exceptions import NetworkError


CHECK_HTML = "https://httpbin.org/headers"


@pytest.mark.asyncio
async def test_html_new_direct_getter():
    api = BaseAPI()
    await api.new_session()
    
    result = await api.new_direct_fetch(CHECK_HTML, handler=Handler.MAIN())
    await check_json(result)
    await check_headers(result)

    await api.close()

@pytest.mark.asyncio
async def test_html_page_direct_getter():
    api = BaseAPI()
    await api.new_session()

    page = await api.new_page()
    result = await page.direct_fetch(
        url=CHECK_HTML,
        handler=Handler.MAIN(),
    )
    await check_json(result)
    await check_headers(result)

    await page.close()

@pytest.mark.asyncio
async def test_html_inject_getter():
    api = BaseAPI()
    await api.new_session()

    page = await api.new_page()
    result = await page.inject_fetch(CHECK_HTML)
    await check_json(result)
    await check_headers(result)

    await page.close()


async def check_json(result: Response | NetworkError):
    assert isinstance(result, Response), "Result should be an instance of Response"
    assert result.status == 200, f"Expected status 200, got {result.status}"
    assert isinstance(result.response, dict), "Response should be a dictionary"

async def check_headers(result: Response | NetworkError):
    # Проверяем, что response содержит словарь с заголовками
    assert isinstance(result, Response), "Result should be an instance of Response"
    assert isinstance(result.response, dict), "Response should be a dictionary"
    assert "headers" in result.response, "Response should contain 'headers' key"
    
    # Заголовки, которые получил сервер (httpbin.org/headers показывает реальные заголовки)
    server_received_headers = {k.lower(): v for k, v in result.response["headers"].items()}
    
    # Заголовки, которые браузер думает что отправил
    browser_captured_headers = {k.lower(): v for k, v in result.request_headers.items()}
    
    # Исключаем заголовки, которые могут добавляться/удаляться промежуточными серверами
    # AWS добавляет x-amzn-trace-id, браузер может добавлять priority, прокси может добавлять connection
    excluded_headers = {
        'x-amzn-trace-id',  # Добавляется AWS/CloudFront
        'priority',         # Может добавляться браузером в новых версиях
        'connection',       # Может управляться прокси/CDN
        'x-forwarded-for',  # Добавляется прокси
        'x-real-ip',        # Добавляется прокси
        'cf-ray',           # Добавляется CloudFlare
        'cf-connecting-ip', # Добавляется CloudFlare
    }
    
    # Фильтруем заголовки для сравнения
    filtered_server_headers = {k: v for k, v in server_received_headers.items() 
                              if k not in excluded_headers}
    filtered_browser_headers = {k: v for k, v in browser_captured_headers.items() 
                               if k not in excluded_headers}
    
    # Проверяем, что основные заголовки совпадают
    # Все заголовки которые отправил браузер должны присутствовать в заголовках сервера
    for header_name, header_value in filtered_browser_headers.items():
        assert header_name in filtered_server_headers, f"Header '{header_name}' missing in server headers"
        assert filtered_server_headers[header_name] == header_value, \
            f"Header '{header_name}' mismatch: browser='{header_value}', server='{filtered_server_headers[header_name]}'"
    
    # Проверяем что есть базовые заголовки, которые должны быть в любом HTTP запросе
    required_headers = {'host', 'user-agent'}
    for required_header in required_headers:
        assert required_header in filtered_server_headers, f"Required header '{required_header}' missing"
        
    print(f"✓ Headers validation passed. Server received {len(filtered_server_headers)} headers, browser captured {len(filtered_browser_headers)} headers")

import pytest
from standard_open_inflation_package import Response
from standard_open_inflation_package.handler import Handler, ExpectedContentType

# Импортируем утилиты для тестирования
from . import (
    run_direct_fetch_test, 
    run_page_direct_fetch_test,
    run_inject_fetch_test,
    assert_json_content,
    DEFAULT_URLS
)

CHECK_HTML = DEFAULT_URLS['headers']


@pytest.mark.asyncio
async def test_html_new_direct_getter():
    def check_json_and_headers(response):
        # Проверяем JSON содержимое
        assert_json_content(response, expected_structure={'headers': dict})
        
        # Проверяем заголовки
        _check_headers_consistency(response)
    
    await run_direct_fetch_test(
        CHECK_HTML, 
        Handler.MAIN(expected_content=ExpectedContentType.JSON),
        expected_type=dict,
        additional_checks=check_json_and_headers
    )

@pytest.mark.asyncio
async def test_html_page_direct_getter():
    def check_json_and_headers(response):
        # Проверяем JSON содержимое
        assert_json_content(response, expected_structure={'headers': dict})
        
        # Проверяем заголовки
        _check_headers_consistency(response)
    
    await run_page_direct_fetch_test(
        CHECK_HTML,
        Handler.MAIN(expected_content=ExpectedContentType.JSON),
        expected_type=dict,
        additional_checks=check_json_and_headers
    )

@pytest.mark.asyncio
async def test_html_inject_getter():
    def check_json_and_headers(response):
        # Проверяем JSON содержимое
        assert_json_content(response, expected_structure={'headers': dict})
        
        # Проверяем заголовки
        _check_headers_consistency(response)
    
    await run_inject_fetch_test(
        CHECK_HTML,
        expected_type=dict,
        additional_checks=check_json_and_headers
    )


def _check_headers_consistency(result: Response):
    """Проверяет соответствие заголовков между запросом и ответом"""
    # Проверяем, что response содержит словарь с заголовками
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

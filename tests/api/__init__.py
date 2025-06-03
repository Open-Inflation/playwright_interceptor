"""
Общие утилиты для тестирования API
"""
import logging
from contextlib import asynccontextmanager
from typing import Type, Union, Tuple, Any, Optional, Callable
from io import BytesIO

from standard_open_inflation_package import BaseAPI, Response
from standard_open_inflation_package.handler import HandlerSearchFailed, HandlerSearchSuccess, Handler
from standard_open_inflation_package.exceptions import NetworkError


# Константы для тестирования
DEFAULT_TIMEOUT = 15.0
DEFAULT_URLS = {
    'html': "https://httpbin.org/",
    'json': "https://httpbin.org/json", 
    'headers': "https://httpbin.org/headers",
    'image': "https://httpbin.org/image/png",  # Более стабильный URL для изображений
    'css': "https://cdnjs.cloudflare.com/ajax/libs/normalize/8.0.1/normalize.min.css",
    'js': "https://cdnjs.cloudflare.com/ajax/libs/jquery/3.6.0/jquery.min.js",
    'text': "https://httpbin.org/robots.txt",
}


@asynccontextmanager
async def api_session(timeout: float = DEFAULT_TIMEOUT, **kwargs):
    """
    Async context manager для управления API сессией.
    
    Args:
        timeout: Таймаут для запросов
        **kwargs: Дополнительные параметры для BaseAPI
    """
    api = BaseAPI(timeout=timeout, **kwargs)
    try:
        await api.new_session()
        yield api
    finally:
        await api.close()


@asynccontextmanager 
async def api_page_session(timeout: float = DEFAULT_TIMEOUT, **kwargs):
    """
    Async context manager для управления API сессией с созданием страницы.
    
    Args:
        timeout: Таймаут для запросов
        **kwargs: Дополнительные параметры для BaseAPI
    """
    api = BaseAPI(timeout=timeout, **kwargs)
    try:
        await api.new_session()
        page = await api.new_page()
        yield api, page
    finally:
        await api.close()


def assert_success_result(
    result: Union[HandlerSearchSuccess, HandlerSearchFailed],
    expected_type: Union[Type, Tuple[Type, ...], None] = None,
    expected_count: Optional[int] = None,
    check_status: bool = True
) -> HandlerSearchSuccess:
    """
    Базовая проверка успешного результата API запроса.
    
    Args:
        result: Результат выполнения запроса
        expected_type: Ожидаемый тип данных в Response
        expected_count: Ожидаемое количество ответов по 1 хандлеру
        check_status: Проверять ли статус-код
        
    Returns:
        HandlerSearchSuccess объект для дальнейшей обработки
        
    Raises:
        AssertionError: Если проверки не прошли
    """
    assert isinstance(result, HandlerSearchSuccess), (
        f"Result should be HandlerSearchSuccess, got {type(result).__name__}"
    )
    
    assert len(result.responses) > 0, "Should have at least one response"
    
    if expected_count is not None:
        assert len(result.responses) == expected_count, (
            f"Expected {expected_count} responses, got {len(result.responses)}"
        )
    
    for i, response in enumerate(result.responses):
        assert isinstance(response, Response), (
            f"Response {i} should be Response instance, got {type(response).__name__}"
        )
        
        if check_status:
            assert str(response.status).startswith("2"), (
                f"Expected 2xx status, got {response.status}"
            )
            
        if expected_type is not None:
            assert isinstance(response.response, expected_type), (
                f"Response {i} should be {expected_type}, got {type(response.response)}"
            )
    
    return result


def assert_failed_result(
    result: Union[HandlerSearchSuccess, HandlerSearchFailed],
    min_rejected: int = 1
) -> HandlerSearchFailed:
    """
    Проверка неудачного результата API запроса.
    
    Args:
        result: Результат выполнения запроса
        min_rejected: Минимальное количество отклоненных ответов
        
    Returns:
        HandlerSearchFailed объект для дальнейшей обработки
    """
    assert isinstance(result, HandlerSearchFailed), (
        f"Result should be HandlerSearchFailed, got {type(result).__name__}"
    )
    
    assert len(result.rejected_responses) >= min_rejected, (
        f"Expected at least {min_rejected} rejected responses, got {len(result.rejected_responses)}"
    )
    
    return result


def assert_html_content(response: Response, check_doctype: bool = True):
    """
    Специфические проверки для HTML контента.
    
    Args:
        response: Ответ для проверки
        check_doctype: Проверять ли наличие DOCTYPE
    """
    assert isinstance(response.response, str), "HTML response should be string"
    
    if check_doctype:
        assert response.response.strip().startswith("<!DOCTYPE html>"), (
            "HTML response should start with DOCTYPE declaration"
        )


def assert_json_content(response: Response, expected_structure: dict = None):
    """
    Специфические проверки для JSON контента.
    
    Args:
        response: Ответ для проверки  
        expected_structure: Ожидаемая структура JSON (ключи)
    """
    assert isinstance(response.response, (dict, list)), (
        "JSON response should be dict or list"
    )
    
    if expected_structure and isinstance(response.response, dict):
        for key in expected_structure:
            assert key in response.response, f"Expected key '{key}' in JSON response"


def assert_binary_content(response: Response, min_size: int = 0):
    """
    Специфические проверки для бинарного контента.
    
    Args:
        response: Ответ для проверки
        min_size: Минимальный размер содержимого в байтах
    """
    assert isinstance(response.response, BytesIO), (
        "Binary response should be BytesIO"
    )
    
    if min_size > 0:
        # Получаем размер содержимого
        current_pos = response.response.tell()
        response.response.seek(0, 2)  # В конец
        size = response.response.tell()
        response.response.seek(current_pos)  # Возвращаем позицию
        
        assert size >= min_size, f"Expected at least {min_size} bytes, got {size}"


def log_rejected_responses(result: HandlerSearchFailed, logger: logging.Logger = None):
    """
    Логирование отклоненных ответов для отладки.
    
    Args:
        result: Результат с отклоненными ответами
        logger: Логгер для записи (опционально)
    """
    if logger is None:
        logger = logging.getLogger(__name__)
    
    from standard_open_inflation_package.tools import parse_content_type
    
    content_types = []
    for response in result.rejected_responses:
        content_type_header = response.response_headers.get('content-type', 'unknown')
        parsed = parse_content_type(content_type_header)
        content_types.append(parsed["content_type"])
    
    logger.info(f"Rejected responses content types: {', '.join(content_types)}")


async def run_direct_fetch_test(
    url: str,
    handler: Any,
    expected_type: Union[Type, Tuple[Type, ...], None] = None,
    timeout: float = DEFAULT_TIMEOUT,
    additional_checks: Optional[Callable] = None
) -> HandlerSearchSuccess:
    """
    Универсальная функция для тестирования direct_fetch.
    
    Args:
        url: URL для запроса
        handler: Handler для обработки ответа
        expected_type: Ожидаемый тип данных
        timeout: Таймаут запроса
        additional_checks: Дополнительная функция проверки
        
    Returns:
        HandlerSearchSuccess результат
    """
    async with api_session(timeout=timeout) as api:
        results = await api.new_direct_fetch(url, handlers=handler)
        # new_direct_fetch возвращает список результатов
        assert len(results) == 1, f"Expected 1 result, got {len(results)}"
        result = results[0]
        
        success_result = assert_success_result(result, expected_type, expected_count=1)
        
        if additional_checks:
            additional_checks(success_result.responses[0])
            
        return success_result


async def run_page_direct_fetch_test(
    url: str,
    handler: Any,
    expected_type: Union[Type, Tuple[Type, ...], None] = None,
    timeout: float = DEFAULT_TIMEOUT,
    additional_checks: Optional[Callable] = None
) -> HandlerSearchSuccess:
    """
    Универсальная функция для тестирования page.direct_fetch.
    
    Args:
        url: URL для запроса
        handler: Handler для обработки ответа
        expected_type: Ожидаемый тип данных
        timeout: Таймаут запроса
        additional_checks: Дополнительная функция проверки
        
    Returns:
        HandlerSearchSuccess результат
    """
    async with api_page_session(timeout=timeout) as (api, page):
        results = await page.direct_fetch(url=url, handlers=handler)
        # page.direct_fetch тоже возвращает список результатов
        assert len(results) == 1, f"Expected 1 result, got {len(results)}"
        result = results[0]
        
        success_result = assert_success_result(result, expected_type, expected_count=1)
        
        if additional_checks:
            additional_checks(success_result.responses[0])
            
        return success_result


async def run_inject_fetch_test(
    url: str,
    expected_type: Union[Type, Tuple[Type, ...], None] = None,
    timeout: float = DEFAULT_TIMEOUT,
    additional_checks: Optional[Callable] = None
) -> Union[Response, NetworkError]:
    """
    Универсальная функция для тестирования inject_fetch.
    
    Args:
        url: URL для запроса
        expected_type: Ожидаемый тип данных
        timeout: Таймаут запроса
        additional_checks: Дополнительная функция проверки
        
    Returns:
        Response или NetworkError результат
    """
    async with api_page_session(timeout=timeout) as (api, page):
        result = await page.inject_fetch(url)
        
        assert isinstance(result, Response), f"Expected Response, got {type(result).__name__}"
        assert str(result.status).startswith("2"), f"Expected 2xx status, got {result.status}"
        
        if expected_type:
            assert isinstance(result.response, expected_type), (
                f"Expected {expected_type}, got {type(result.response)}"
            )
        
        if additional_checks:
            additional_checks(result)
            
        return result


async def run_page_resource_intercept_test(
    page_url: str,
    handler: Handler,
    expected_type: Union[Type, Tuple[Type, ...], None] = None,
    timeout: float = DEFAULT_TIMEOUT,
    additional_checks: Optional[Callable] = None,
    min_resources: int = 1
) -> HandlerSearchSuccess:
    """
    Универсальная функция для тестирования перехвата ресурсов страницы.
    
    Handler'ы типа CSS, JS, FONT, IMAGE, etc. предназначены для перехвата ресурсов,
    которые загружает страница, а не для прямых запросов к файлам.
    
    Args:
        page_url: URL страницы для загрузки
        handler: Handler для перехвата ресурсов
        expected_type: Ожидаемый тип данных в перехваченных ресурсах
        timeout: Таймаут запроса
        additional_checks: Дополнительная функция проверки
        min_resources: Минимальное количество ожидаемых ресурсов
        
    Returns:
        HandlerSearchSuccess с перехваченными ресурсами
    """
    async with api_page_session(timeout=timeout) as (api, page):
        # Загружаем страницу и перехватываем ресурсы
        results = await page.direct_fetch(page_url, handlers=handler)
        assert len(results) == 1, f"Expected 1 result, got {len(results)}"
        result = results[0]
        
        # Проверяем что получили успешный результат с ресурсами
        success_result = assert_success_result(result, expected_type, expected_count=None)
        
        # Проверяем что получили минимальное количество ресурсов
        assert len(success_result.responses) >= min_resources, (
            f"Expected at least {min_resources} intercepted resources, "
            f"got {len(success_result.responses)}"
        )
        
        if additional_checks:
            for response in success_result.responses:
                additional_checks(response)
                
        return success_result

async def run_no_intercept_test(page_url: str, handler: Handler, timeout: float = DEFAULT_TIMEOUT) -> HandlerSearchFailed:
    """
    Тест для случаев когда Handler НЕ должен перехватывать ресурсы.
    
    Args:
        page_url: URL страницы для загрузки
        handler: Handler который НЕ должен срабатывать
        timeout: Таймаут запроса
        
    Returns:
        HandlerSearchFailed результат
    """
    async with api_page_session(timeout=timeout) as (api, page):
        results = await page.direct_fetch(page_url, handlers=handler)
        assert len(results) == 1, f"Expected 1 result, got {len(results)}"
        result = results[0]
        
        # Ожидаем что Handler не сработал
        failed_result = assert_failed_result(result, min_rejected=1)
        return failed_result

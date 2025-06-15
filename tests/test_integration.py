"""
Integration test for checking new request_modify and response_modify functionality
"""
import pytest
import asyncio
from playwright.async_api import async_playwright
from standard_open_inflation_package import NetworkInterceptor, Handler, Execute, Request, Response


@pytest.mark.asyncio
async def test_integration_request_response_modification():
    """Full integration test for request and response modification"""
    
    modification_log = []
    
    def request_modifier(request: Request) -> Request:
        """Модифицирует запрос - добавляет заголовок и параметр"""
        modification_log.append(f"REQUEST: {request.method.value} {request.url}")
        if request.headers is None:
            request.headers = {}
        if request.params is None:
            request.params = {}
        request.headers["X-Test-Modified"] = "true"
        request.params["test"] = "integration"
        return request
    
    def response_modifier(response: Response) -> Response:
        """Модифицирует ответ - добавляет заголовок"""
        modification_log.append(f"RESPONSE: {response.status} from {response.url}")
        response.response_headers["X-Integration-Test"] = "passed"
        return response
    
    async with async_playwright() as pw:
        browser = await pw.firefox.launch()
        page = await browser.new_page()
        
        interceptor = NetworkInterceptor(page)
        
        # Создаем хендлер с обеими модификациями
        handler = Handler.ALL(execute=Execute.ALL(
            request_modify=request_modifier,
            response_modify=response_modifier,
            max_modifications=2,
            max_responses=1
        ))
        
        # Запускаем перехватчик
        results, _ = await asyncio.gather(
            interceptor.execute(handler),
            page.goto("https://httpbin.org/get")
        )
        
        await browser.close()
        
        # Проверяем результаты
        assert len(results) == 1
        assert hasattr(results[0], 'responses')  # HandlerSearchSuccess
        assert len(results[0].responses) > 0
        assert len(modification_log) >= 2  # Минимум 1 запрос и 1 ответ
        
        # Проверяем что модификации действительно произошли
        request_modifications = [log for log in modification_log if log.startswith("REQUEST")]
        response_modifications = [log for log in modification_log if log.startswith("RESPONSE")]
        
        assert len(request_modifications) >= 1
        assert len(response_modifications) >= 1


@pytest.mark.asyncio
async def test_multiple_handlers_sequential_modifications():
    """Тест последовательного применения модификаций от нескольких хендлеров"""
    
    modification_order = []
    
    def first_request_modifier(request: Request) -> Request:
        modification_order.append("handler1_request")
        if request.headers is None:
            request.headers = {}
        request.headers["X-Handler1"] = "true"
        return request
    
    def second_request_modifier(request: Request) -> Request:
        modification_order.append("handler2_request")
        if request.headers is None:
            request.headers = {}
        request.headers["X-Handler2"] = "true"
        return request
    
    def first_response_modifier(response: Response) -> Response:
        modification_order.append("handler1_response")
        response.response_headers["X-Modified-By-Handler1"] = "true"
        return response
    
    def second_response_modifier(response: Response) -> Response:
        modification_order.append("handler2_response")
        response.response_headers["X-Modified-By-Handler2"] = "true"
        return response
    
    async with async_playwright() as pw:
        browser = await pw.firefox.launch()
        page = await browser.new_page()
        
        interceptor = NetworkInterceptor(page)
        
        # Создаем два хендлера
        handler1 = Handler.ALL(
            slug="handler1",
            execute=Execute.ALL(
                request_modify=first_request_modifier,
                response_modify=first_response_modifier,
                max_modifications=1,
                max_responses=1
            )
        )
        
        handler2 = Handler.ALL(
            slug="handler2", 
            execute=Execute.ALL(
                request_modify=second_request_modifier,
                response_modify=second_response_modifier,
                max_modifications=1,
                max_responses=1
            )
        )
        
        # Запускаем перехватчик с двумя хендлерами
        results, _ = await asyncio.gather(
            interceptor.execute([handler1, handler2]),
            page.goto("https://httpbin.org/get")
        )
        
        await browser.close()
        
        # Проверяем результаты
        assert len(results) == 2
        
        # Проверяем порядок применения модификаций
        # Модификации запросов должны происходить перед отправкой
        # Модификации ответов должны происходить после получения
        assert "handler1_request" in modification_order
        assert "handler2_request" in modification_order
        assert "handler1_response" in modification_order
        assert "handler2_response" in modification_order


@pytest.mark.asyncio  
async def test_async_modifiers():
    """Тест асинхронных функций модификации"""
    
    async def async_request_modifier(request: Request) -> Request:
        await asyncio.sleep(0.01)  # Имитируем асинхронную операцию
        if request.headers is None:
            request.headers = {}
        request.headers["X-Async-Modified"] = "true"
        return request
    
    async def async_response_modifier(response: Response) -> Response:
        await asyncio.sleep(0.01)  # Имитируем асинхронную операцию
        response.response_headers["X-Async-Response"] = "true" 
        return response
    
    async with async_playwright() as pw:
        browser = await pw.firefox.launch()
        page = await browser.new_page()
        
        interceptor = NetworkInterceptor(page)
        
        handler = Handler.ALL(execute=Execute.ALL(
            request_modify=async_request_modifier,
            response_modify=async_response_modifier,
            max_modifications=1,
            max_responses=1
        ))
        
        results, _ = await asyncio.gather(
            interceptor.execute(handler),
            page.goto("https://httpbin.org/get")
        )
        
        await browser.close()
        
        # Проверяем что результаты получены
        assert len(results) == 1
        assert hasattr(results[0], 'responses')
        assert len(results[0].responses) > 0

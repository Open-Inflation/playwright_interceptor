import os
import asyncio
import time
import json
import base64
from beartype import beartype
from beartype.typing import Union, Optional
from .parsers import parse_response_data
from . import config as CFG
from .models import Response, NetworkError, Handler, Request, HandlerSearchFailedError, HttpMethod
import copy
from urllib.parse import urlparse


class RequestInterceptor:
    """Класс для перехвата HTTP-запросов через Playwright route interception"""
    
    def __init__(self, api, handler: Handler, base_url: str, start_time: float):
        self.api = api
        self.handler = handler
        self.base_url = base_url
        self.start_time = start_time
        self.captured_request_headers = {}
        self.rejected_responses = []
        self.loop = asyncio.get_running_loop()
        self.result_future = self.loop.create_future()
    
    async def handle_route(self, route):
        """Обработчик маршрута для перехвата запросов"""
        request = route.request
        
        # Захватываем заголовки запроса для базового URL
        if request.url.startswith(self.base_url):
            self.captured_request_headers = dict(request.headers)
        
        # Выполняем запрос
        response = await route.fetch()
        response_time = time.time()  # Записываем время получения response
        
        # Создаем мок-объект для проверки handler
        mock_response = self._create_mock_response(response, request.method)
        
        if self.handler.should_capture(mock_response, self.base_url):
            await self._handle_captured_response(response, response_time)
        else:
            self._handle_rejected_response(response, request, response_time)
        
        # Возвращаем оригинальный ответ
        await route.fulfill(response=response)
    
    def _create_mock_response(self, response, method: str):
        """Создает мок-объект response для проверки handler"""
        class MockResponse:
            def __init__(self, status, headers, url, method):
                self.status = status
                self.headers = headers
                self.url = url
                self.request = type('MockRequest', (), {'method': method})()
        
        return MockResponse(response.status, response.headers, response.url, method)
    
    async def _handle_captured_response(self, response, response_time: float):
        """Обрабатывает захваченный response"""
        if self.result_future.done():
            return
            
        try:
            # Получаем тело ответа
            raw_data = await response.body()
            content_type = response.headers.get("content-type", "").lower()
            
            # Парсим данные
            parsed_data = parse_response_data(raw_data, content_type)
            
            # Создаем Response объект
            duration = response_time - self.start_time
            result = Response(
                status=response.status,
                request_headers=self.captured_request_headers,
                response_headers=response.headers,
                response=parsed_data,
                duration=duration,
                url=response.url
            )
            
            self.api._logger.info(f"{CFG.LOG_REQUEST_COMPLETED} {duration:.3f}s")
            self.result_future.set_result(result)
            
        except Exception as e:
            self.api._logger.warning(f"{CFG.LOG_FAILED_TO_GET_RESPONSE_BODY} {response.url}: {e}")
            if not self.result_future.done():
                self.result_future.set_exception(e)
    
    def _handle_rejected_response(self, response, request, response_time: float):
        """Обрабатывает отклоненный response"""
        # Для Handler.NONE() или режима отладки сохраняем полное содержимое
        should_store_content = (self.handler.handler_type == "none" or self.api.debug)
        
        if should_store_content:
            # Асинхронно получаем тело ответа для анализа
            asyncio.create_task(self._store_rejected_response_with_content(response, request, response_time))
        else:
            # Обычное поведение - сохраняем без содержимого
            duration = response_time - self.start_time
            self.rejected_responses.append(Response(
                status=response.status,
                request_headers=dict(request.headers),
                response_headers=response.headers,
                response=None,
                duration=duration,
                url=response.url
            ))
    
    async def _store_rejected_response_with_content(self, response, request, response_time: float):
        """Асинхронно сохраняет отклоненный response с полным содержимым"""
        try:
            # Вычисляем duration СРАЗУ, на основе времени получения response
            duration = response_time - self.start_time
            
            # Получаем тело ответа (это может занять время, но duration уже зафиксирован)
            raw_data = await response.body()
            content_type = response.headers.get("content-type", "").lower()
            
            # Парсим данные
            parsed_data = parse_response_data(raw_data, content_type)
            
            # Создаем Response объект с полным содержимым
            self.rejected_responses.append(Response(
                status=response.status,
                request_headers=dict(request.headers),
                response_headers=response.headers,
                response=parsed_data,
                duration=duration,
                url=response.url
            ))
            
            self.api._logger.debug(f"Stored rejected response with content: {response.url}")
            
        except Exception as e:
            self.api._logger.warning(f"Failed to get rejected response body {response.url}: {e}")
            # Fallback - сохраняем без содержимого, но с правильным duration
            duration = response_time - self.start_time
            self.rejected_responses.append(Response(
                status=response.status,
                request_headers=dict(request.headers),
                response_headers=response.headers,
                response=None,
                duration=duration,
                url=response.url
            ))
    
    async def wait_for_result(self, timeout: float) -> Union[Response, HandlerSearchFailedError]:
        """Ожидает результат перехвата с таймаутом"""
        try:
            return await asyncio.wait_for(self.result_future, timeout=timeout)
        except asyncio.TimeoutError:
            duration = time.time() - self.start_time
            self.api._logger.warning(
                f"Handler {self.handler.handler_type} not found suitable response for {self.base_url}. "
                f"Rejected {len(self.rejected_responses)} responses. Duration: {duration:.3f}s"
            )
            
            return HandlerSearchFailedError(
                handler=self.handler,
                url=self.base_url,
                rejected_responses=self.rejected_responses,
                duration=duration
            )


class Page:
    def __init__(self, api, page):
        self.API = api
        self._page = page
    
    @beartype
    async def modify_request(self, request: Union[Request, str]) -> Request:
        """Создание и модификация объекта запроса"""
        # Создаем объект Request если передана строка
        if isinstance(request, str):
            default_headers = {"Content-Type": CFG.DEFAULT_CONTENT_TYPE}
            request_obj = Request(
                url=request, 
                headers=default_headers,
                method=HttpMethod.GET
            )
        else:
            request_obj = request

        # Применяем модификацию если функция задана
        if self.API.request_modifier_func:
            modified_request = self.API.request_modifier_func(copy.copy(request_obj))
            
            if asyncio.iscoroutinefunction(self.API.request_modifier_func):
                modified_request = await modified_request
            
            # Проверяем что возвращен объект Request
            if isinstance(modified_request, Request):
                if modified_request.method != HttpMethod.ANY:
                    return modified_request
                else:
                    self.API._logger.warning(CFG.LOG_REQUEST_MODIFIER_ANY_TYPE)
            else:
                self.API._logger.warning(f"{CFG.LOG_REQUEST_MODIFIER_FAILED_TYPE}: {type(modified_request)}")
        
        return request_obj

    @beartype
    async def direct_fetch(self, url: str, handler: Handler = Handler.MAIN(), wait_selector: Optional[str] = None) -> Union[Response, HandlerSearchFailedError]:
        """
        Выполняет перехват HTTP-запросов через Playwright route interception.
        Подходит для Camoufox/Firefox браузеров.
        """
        if not self._page:
            raise RuntimeError(CFG.LOG_PAGE_NOT_AVAILABLE)
            
        start_time = time.time()
        
        # Инициализируем перехватчик запросов
        interceptor = RequestInterceptor(self.API, handler, url, start_time)
        
        try:
            # Устанавливаем перехват маршрутов
            await self._page.route("**/*", interceptor.handle_route)
            
            # Переходим на страницу
            await self._page.evaluate(f"window.location.href = '{url}';")
            
            # Ожидание селектора если указан
            if wait_selector:
                await self._page.wait_for_selector(
                    wait_selector, 
                    timeout=self.API.timeout * CFG.MILLISECONDS_MULTIPLIER
                )
            
            # Ждем результат перехвата
            return await interceptor.wait_for_result(self.API.timeout)
            
        finally:
            # Очищаем перехват маршрутов
            await self._page.unroute("**/*", interceptor.handle_route)

    @beartype
    async def inject_fetch(self, request: Union[Request, str]) -> Union[Response, NetworkError]:
        """
        Выполнение HTTP-запроса через JavaScript в браузере.

        Args:
            request (Union[Request, str]): Объект Request или URL (для URL будет создан Request с GET методом).

        Returns:
            Union[Response, NetworkError]: Ответ API или ошибка.
        """
        
        if not self._page:
            raise RuntimeError(CFG.LOG_PAGE_NOT_AVAILABLE)

        start_time = time.time()
        
        # Получаем модифицированный объект Request
        final_request = await self.modify_request(request)
        
        # Перехватываем заголовки запроса через Playwright
        captured_request_headers = {}
        
        def _on_request(req):
            # Перехватываем заголовки запроса для нужного URL
            if req.url == final_request.real_url:
                nonlocal captured_request_headers
                captured_request_headers = dict(req.headers)

        # Добавляем слушатель запросов
        self.API._bcontext.on("request", _on_request)

        try:
            # JavaScript-код для выполнения запроса с возвратом статуса и заголовков
            script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), CFG.INJECT_FETCH_JS_FILE)

            def load_inject_script():
                try:
                    with open(script_path, "r") as file:
                        return file.read()
                except FileNotFoundError:
                    raise FileNotFoundError(f"{CFG.ERROR_JS_FILE_NOT_FOUND}: {script_path}")

            # Load the script once
            script = load_inject_script()

            # Подготавливаем данные для JavaScript
            body_str = json.dumps(final_request.body) if isinstance(final_request.body, dict) else "null"
            
            result = await self._page.evaluate(f"({script})(\"{final_request.real_url}\", \"{final_request.method.value}\", {body_str}, {json.dumps(final_request.headers)})")
            
        finally:
            # Удаляем слушатель запросов
            self.API._bcontext.remove_listener("request", _on_request)
        
        duration = time.time() - start_time
        
        # Проверяем, что вернул JavaScript - успешный ответ или ошибку
        if not result.get('success', False):
            # Возвращаем объект ошибки
            error_info = result.get('error', {})
            return NetworkError(
                name=error_info.get('name', CFG.ERROR_UNKNOWN),
                message=error_info.get('message', CFG.ERROR_MESSAGE_UNKNOWN),
                details=error_info.get('details', {}),
                timestamp=error_info.get('timestamp', ''),
                duration=duration
            )
        
        # Извлекаем данные успешного ответа
        response_data = result['response']
        
        # Парсим данные в зависимости от Content-Type
        raw_data = response_data['data']
        content_type = response_data['headers'].get('content-type', '')
        parsed_data = parse_response_data(raw_data, content_type)
        
        # Обрабатываем Set-Cookie заголовки вручную
        if 'set-cookie' in response_data['headers']:
            set_cookie_header = response_data['headers']['set-cookie']
            self.API._logger.debug(f"{CFG.LOG_PROCESSING_COOKIE}: {set_cookie_header}")
            
            # Устанавливаем куки через Playwright API
            try:
                # Парсим домен из URL для установки кук
                parsed_url = urlparse(final_request.real_url)
                domain = parsed_url.netloc
                
                # Простой парсинг Set-Cookie (для более сложных случаев нужен полноценный парсер)
                for cookie_string in set_cookie_header.split(','):
                    cookie_parts = cookie_string.strip().split(';')
                    if cookie_parts:
                        name_value = cookie_parts[0].split('=', 1)
                        if len(name_value) == 2:
                            name, value = name_value
                            await self.API._bcontext.add_cookies([{
                                'name': name.strip(),
                                'value': value.strip(),
                                'domain': domain,
                                'path': CFG.DEFAULT_COOKIE_PATH
                            }])
                            self.API._logger.debug(f"{CFG.LOG_COOKIE_SET}: {name.strip()}={value.strip()}")
            except Exception as e:
                self.API._logger.warning(f"{CFG.LOG_COOKIE_PROCESSING_FAILED}: {e}")
        
        self.API._logger.info(f"{CFG.LOG_INJECT_FETCH_COMPLETED} {duration:.3f}s")
        
        return Response(
            status=response_data['status'],
            request_headers=captured_request_headers,
            response_headers=response_data['headers'],
            response=parsed_data,
            duration=duration,
            url=final_request.real_url
        )

    async def close(self):
        """Закрывает страницу"""
        if self._page:
            await self._page.close()
            self._page = None
            self.API._logger.info(CFG.LOG_PAGE_CLOSED)
        else:
            self.API._logger.info(CFG.LOG_NO_PAGE_TO_CLOSE)

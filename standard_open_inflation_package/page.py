import os
import asyncio
import time
import json
from beartype import beartype
from beartype.typing import Union, Optional, List, Dict
from .content_loader import parse_response_data
from . import config as CFG
from .models import Response, Request, HttpMethod
from .exceptions import NetworkError
from .handler import Handler, HandlerSearchFailed, HandlerSearchSuccess
import copy
from urllib.parse import urlparse


@beartype
class MockResponse:
    def __init__(self, status, headers, url, method):
        self.status = status
        self.headers = headers
        self.url = url
        self.request = type('MockRequest', (), {'method': method})()


@beartype
class MultiRequestInterceptor:
    """Класс для перехвата HTTP-запросов с поддержкой множественных хандлеров"""
    
    def __init__(self, api, handlers: List[Handler], base_url: str, start_time: float):
        self.api = api
        self.handlers = handlers
        self.base_url = base_url
        self.start_time = start_time
        self.rejected_responses = []
        self.loop = asyncio.get_running_loop()
        
        # Словарь для хранения результатов каждого хандлера (используем slug как ключ)
        self.handler_results: Dict[str, List[Response]] = {handler.slug: [] for handler in handlers}
        self.handler_errors: Dict[str, HandlerSearchFailed] = {}
        
        # Future для завершения работы
        self.completion_future = self.loop.create_future()
        self.timeout_task = None
    
    async def handle_route(self, route):
        """Обработчик маршрута для перехвата запросов"""
        request = route.request
        
        # Выполняем запрос
        response = await route.fetch()
        response_time = time.time()
        
        # Создаем мок-объект для проверки хандлеров
        mock_response = MockResponse(response.status, response.headers, response.url, request.method)

        # Сначала определяем какие хендлеры должны захватить этот ответ
        capturing_handlers = []
        for handler in self.handlers:
            if handler.slug in self.handler_errors:
                continue  # Пропускаем хандлеры, которые уже завершились с ошибкой
                
            # Проверяем, не достиг ли хендлер уже своего лимита
            if handler.max_responses is not None and len(self.handler_results[handler.slug]) >= handler.max_responses:
                continue  # Хендлер уже получил максимальное количество ответов
                
            if handler.should_capture(mock_response, self.base_url):
                capturing_handlers.append(handler)
                self.api._logger.debug(f"Handler {handler.handler_type} will capture: {response.url}")
            else:
                self.api._logger.debug(f"Handler {handler.handler_type} rejected: {response.url} (content-type: {response.headers.get('content-type', 'unknown')})")
        
        # Если есть хендлеры для захвата, обрабатываем ответ один раз
        if capturing_handlers:
            await self._handle_captured_response(capturing_handlers, response, request, response_time)
        else:
            self._handle_rejected_response(response, request, response_time)
            self.api._logger.debug(f"All handlers rejected: {response.url}")
        
        # Проверяем, завершены ли все хандлеры
        self._check_completion()
        
        # Возвращаем оригинальный ответ
        await route.fulfill(response=response)
    
    async def _handle_captured_response(self, handlers: List[Handler], response, request, response_time: float):
        """Обрабатывает захваченный response для множественных хандлеров оптимально"""
        try:
            # Получаем тело ответа ТОЛЬКО ОДИН РАЗ
            raw_data = await response.body()

            content_type = response.headers.get("content-type", "").lower()
            parsed_data = parse_response_data(raw_data, content_type)
            
            # Создаем Response объект для каждого хендлера
            result = Response(
                status=response.status,
                request_headers=request.headers,
                response_headers=response.headers,
                response=parsed_data,  # Переиспользуем уже распарсенные данные
                duration=response_time - self.start_time,
                url=response.url
            )

            for handler in handlers:    
                # Добавляем результат к хандлеру
                self.handler_results[handler.slug].append(result)
                
                self.api._logger.info(f"Handler {handler.handler_type} captured response from {response.url} ({len(self.handler_results[handler.slug])}/{handler.max_responses or 'unlimited'})")
                
        except Exception as e:
            # Если произошла ошибка, логируем для всех хендлеров
            self.api._logger.warning(f"Failed to process response for handlers {', '.join(handler.handler_type for handler in handlers)} from {response.url}: {e}")

    def _handle_rejected_response(self, response, request, response_time: float):
        """Обрабатывает отклоненный response"""
        # Сохраняем отклоненные ответы для анализа
        duration = response_time - self.start_time
        self.rejected_responses.append(Response(
            status=response.status,
            request_headers=request.headers,
            response_headers=response.headers,
            response=None,
            duration=duration,
            url=response.url
        ))
    
    def _check_completion(self):
        """Проверяет, завершены ли все хандлеры"""
        if self.completion_future.done():
            return
            
        # Проверяем каждый хандлер
        all_completed = True
        for handler in self.handlers:
            if handler.slug in self.handler_errors:
                continue  # Уже завершен с ошибкой
                
            # Если хандлер достиг лимита ответов, он завершен
            if handler.max_responses is not None and len(self.handler_results[handler.slug]) >= handler.max_responses:
                continue
            
            # Если хандлер еще не завершен, продолжаем ожидание
            all_completed = False
            break
        
        # Если все хандлеры достигли своих лимитов, завершаем работу
        if all_completed:
            self.api._logger.info(f"All handlers reached their max_responses limits, completing...")
            self._complete_all_handlers()
    
    def _complete_all_handlers(self):
        """Завершает работу всех хандлеров"""
        if self.completion_future.done():
            return
            
        # Формируем результат
        result = []
        current_time = time.time()
        
        for handler in self.handlers:
            if handler.slug in self.handler_errors:
                result.append(self.handler_errors[handler.slug])
            elif self.handler_results[handler.slug]:
                duration = current_time - self.start_time
                result.append(HandlerSearchSuccess(
                    responses=self.handler_results[handler.slug],
                    duration=duration,
                    handler_slug=handler.slug
                ))
            else:
                # Хандлер не получил ни одного ответа
                duration = current_time - self.start_time
                error = HandlerSearchFailed(
                    rejected_responses=self.rejected_responses,
                    duration=duration,
                    handler_slug=handler.slug
                )
                result.append(error)
        
        self.completion_future.set_result(result)
    
    async def wait_for_results(self, timeout: float) -> List[Union[HandlerSearchSuccess, HandlerSearchFailed]]:
        """Ожидает результатов всех хандлеров с таймаутом"""
        # Устанавливаем таймаут
        self.timeout_task = asyncio.create_task(asyncio.sleep(timeout))
        
        # Ожидаем либо завершения всех хандлеров, либо таймаута
        done, _pending = await asyncio.wait(
            [self.completion_future, self.timeout_task],
            return_when=asyncio.FIRST_COMPLETED
        )
        
        if self.completion_future in done:
            # Все хандлеры завершились
            self.timeout_task.cancel()
            return await self.completion_future
        else:
            # Таймаут
            duration = time.time() - self.start_time
            self.api._logger.warning(f"Timeout reached for multi-handler request to {self.base_url}. Duration: {duration:.3f}s")
            
            # Формируем результат с тем, что успели получить
            result = []
            for handler in self.handlers:
                if self.handler_results[handler.slug]:
                    result.append(HandlerSearchSuccess(
                        responses=self.handler_results[handler.slug],
                        duration=duration,
                        handler_slug=handler.slug
                    ))
                else:
                    result.append(HandlerSearchFailed(
                        rejected_responses=self.rejected_responses,
                        duration=duration,
                        handler_slug=handler.slug
                    ))

            return result


@beartype
class Page:
    def __init__(self, api, page):
        self.API = api
        self._page = page
    
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

    async def direct_fetch(self, url: str, handlers: Union[Handler, List[Handler]] = Handler.MAIN(), wait_selector: Optional[str] = None) -> List[Union[HandlerSearchSuccess, HandlerSearchFailed]]:
        """
        Выполняет перехват HTTP-запросов через Playwright route interception.
        Поддерживает как одиночные хандлеры, так и множественные.
        
        Args:
            url: URL для запроса
            handlers: Один хандлер или список хандлеров. Если None, используется Handler.MAIN()
            wait_selector: Селектор для ожидания
            
        Returns:
            - Для множественных хандлеров: List[Union[HandlerSearchSuccess, HandlerSearchFailed]]]
        """
        if not self._page:
            raise RuntimeError(CFG.LOG_PAGE_NOT_AVAILABLE)
            
        start_time = time.time()
        
        # Обрабатываем входные параметры
        if isinstance(handlers, Handler):
            handlers = [handlers]

        # Проверяем уникальность slug'ов
        slugs = [handler.slug for handler in handlers]
        if len(slugs) != len(set(slugs)):
            duplicate_slugs = []
            seen = set()
            for slug in slugs:
                if slug in seen:
                    duplicate_slugs.append(slug)
                else:
                    seen.add(slug)
            raise ValueError(f"Обнаружены дублирующиеся slug'и в handlers: {duplicate_slugs}")

        # Новая логика для множественных хандлеров
        multi_interceptor = MultiRequestInterceptor(self.API, handlers, url, start_time)
        
        try:
            # Устанавливаем перехват маршрутов
            await self._page.route("**/*", multi_interceptor.handle_route)
            
            # Переходим на страницу
            await self._page.evaluate(f"window.location.href = '{url}';")
            
            # Ожидание селектора если указан
            if wait_selector:
                await self._page.wait_for_selector(
                    wait_selector, 
                    timeout=self.API.timeout * CFG.MILLISECONDS_MULTIPLIER
                )
            
            # Ждем результатов всех хандлеров
            return await multi_interceptor.wait_for_results(self.API.timeout)
            
        finally:
            # Очищаем перехват маршрутов
            await self._page.unroute("**/*", multi_interceptor.handle_route)

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

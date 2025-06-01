import os
import asyncio
import time
import json
from beartype import beartype
from beartype.typing import Union, Optional
from .parsers import parse_response_data
from . import config as CFG
from .models import Response, NetworkError, Handler, Request, HandlerSearchFailedError, HttpMethod
import copy
from urllib.parse import urlparse


class Page:
    def __init__(self, api, page):
        self.API = api
        self._page = page
    
    @beartype
    async def modify_request(self, request: Union[Request, str]) -> Request:
        """Создание и модификация объекта запроса"""
        # Создаем объект Request если передана строка
        if isinstance(request, str):
            from .models import HttpMethod
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
        if not self._page:
            raise RuntimeError(CFG.LOG_PAGE_NOT_AVAILABLE)
            
        start_time = time.time()

        # Готовим Future и колбэки для response и request
        loop = asyncio.get_running_loop()
        response_future = loop.create_future()
        captured_request_headers = {}
        rejected_responses = []  # Список отклоненных response

        def _on_request(req):
            # Перехватываем заголовки запроса для нужного URL
            if req.url.startswith(url):
                nonlocal captured_request_headers
                captured_request_headers = dict(req.headers)

        def _on_response(resp):
            # Получаем данные сразу в момент перехвата response
            async def get_response_data():
                data = {
                    'status': resp.status,
                    'headers': dict(resp.headers),
                    'content_type': resp.headers.get("content-type", "").lower(),
                    'raw_data': None,
                    'url': resp.url
                }

                try:
                    raw_data = await resp.body()
                    data['raw_data'] = raw_data
                except Exception as e:
                    # Если не удалось получить body, возвращаем базовую информацию
                    data['error'] = str(e)
                
                return data

            if handler.should_capture(resp, url) and not response_future.done():
                # Создаем задачу для получения данных и устанавливаем результат
                task = asyncio.create_task(get_response_data())
                response_future.set_result(task)
            else:
                # Добавляем задачу получения данных отклоненного response
                data = None
                if self.API.debug or handler.handler_type == 'none':
                    # Если это отладочный режим или Handler.NONE(), получаем данные
                    # Создаем задачу для получения данных отклоненного response
                    # но не ждем её выполнения, просто логируем что response был отклонен
                    asyncio.create_task(get_response_data())

                rejected_responses.append(Response(
                    status=resp.status,
                    request_headers=dict(resp.request.headers) if resp.request else {},
                    response_headers=dict(resp.headers),
                    response=data,
                    duration=time.time() - start_time,
                    url=resp.url
                ))

        self.API._bcontext.on("request", _on_request)
        self.API._bcontext.on("response", _on_response)

        try:
            await self._page.evaluate(f"window.location.href = '{url}';")

            # Ожидание селектора если указан
            if wait_selector:
                # Playwright требует timeout в миллисекундах
                await self._page.wait_for_selector(wait_selector, timeout=self.API.timeout * CFG.MILLISECONDS_MULTIPLIER)

            try:
                # Получаем задачу с данными response
                # asyncio.wait_for требует timeout в секундах
                response_task = await asyncio.wait_for(response_future, timeout=self.API.timeout)
                response_data = await response_task
                
                # Если возникла ошибка при получении body, логируем и поднимаем исключение
                if response_data.get('error'):
                    error_msg = f"Failed to get response body: {response_data['error']}"
                    self.API._logger.error(error_msg)
                    raise RuntimeError(error_msg)
                
                # Используем полученные данные
                raw_data = response_data['raw_data']
                content_type = response_data['content_type']
                status = response_data['status']
                response_headers = response_data['headers']
                response_url = response_data['url']
                
                data = parse_response_data(raw_data, content_type)
                
                # Вычисляем метрики производительности
                duration = time.time() - start_time
                self.API._logger.info(f"{CFG.LOG_REQUEST_COMPLETED} {duration:.3f}s")
                
                # Возвращаем объект Response с атрибутами status, request_headers, response_headers, response, duration, url
                return Response(
                    status=status,
                    request_headers=captured_request_headers,
                    response_headers=response_headers,
                    response=data,
                    duration=duration,
                    url=response_url
                )
                
            except asyncio.TimeoutError:
                # Если timeout - собираем все отклоненные response и возвращаем HandlerNotFoundError
                duration = time.time() - start_time
                
                self.API._logger.warning(f"Handler {handler.handler_type} not found suitable response for {url}. Rejected {len(rejected_responses)} responses. Duration: {duration:.3f}s")
                
                return HandlerSearchFailedError(
                    handler=handler,
                    url=url,
                    rejected_responses=rejected_responses,
                    duration=duration
                )
                
        finally:
            # Удаляем колбэки после завершения
            self.API._bcontext.remove_listener("request", _on_request)
            self.API._bcontext.remove_listener("response", _on_response)

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

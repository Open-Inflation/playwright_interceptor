import os
import asyncio
import time
import json
from beartype import beartype
from beartype.typing import Union, Optional, List
from .content_loader import parse_response_data
from . import config as CFG
from .models import Response, Request, HttpMethod
from .exceptions import NetworkError
from .handler import Handler, HandlerSearchFailed, HandlerSearchSuccess
from .direct_request_interceptor import MultiRequestInterceptor
import copy
from urllib.parse import urlparse



@beartype
class Page:
    def __init__(self, api, page):
        self.API = api
        self._page = page
    
    async def modify_request(self, request: Union[Request, str]) -> Request:
        """Создание и модификация объекта запроса"""
        # Создаем объект Request если передана строка
        if isinstance(request, str):
            default_headers = {"Content-Type": CFG.PARAMETERS.DEFAULT_CONTENT_TYPE}
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
                    self.API._logger.warning(CFG.LOGS.REQUEST_MODIFIER_ANY_TYPE)
            else:
                self.API._logger.warning(f"{CFG.LOGS.REQUEST_MODIFIER_FAILED_TYPE}: {type(modified_request)}")
        
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
            raise RuntimeError(CFG.LOGS.PAGE_NOT_AVAILABLE)
            
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
            raise ValueError(CFG.ERRORS.DUPLICATE_HANDLER_SLUGS.format(duplicate_slugs=duplicate_slugs))

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
                    timeout=self.API.timeout * CFG.PARAMETERS.MILLISECONDS_MULTIPLIER
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
            raise RuntimeError(CFG.LOGS.PAGE_NOT_AVAILABLE)

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
            script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), CFG.PARAMETERS.INJECT_FETCH_JS_FILE)

            def load_inject_script():
                try:
                    with open(script_path, "r") as file:
                        return file.read()
                except FileNotFoundError:
                    raise FileNotFoundError(f"{CFG.ERRORS.JS_FILE_NOT_FOUND}: {script_path}")

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
                name=error_info.get('name', CFG.ERRORS.UNKNOWN),
                message=error_info.get('message', CFG.ERRORS.MESSAGE_UNKNOWN),
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
            self.API._logger.debug(f"{CFG.LOGS.PROCESSING_COOKIE}: {set_cookie_header}")
            
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
                                'path': '/'
                            }])
                            self.API._logger.debug(f"{CFG.LOGS.COOKIE_SET}: {name.strip()}={value.strip()}")
            except Exception as e:
                self.API._logger.warning(f"{CFG.LOGS.COOKIE_PROCESSING_FAILED}: {e}")
        
        self.API._logger.info(f"{CFG.LOGS.INJECT_FETCH_COMPLETED} {duration:.3f}s")
        
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
            self.API._logger.info(CFG.LOGS.PAGE_CLOSED)
        else:
            self.API._logger.info(CFG.ERRORS.NO_PAGE_TO_CLOSE)

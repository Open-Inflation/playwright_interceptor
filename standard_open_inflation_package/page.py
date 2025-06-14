import os
import asyncio
import time
import json
import copy
from urllib.parse import urlparse
from beartype import beartype
from beartype.typing import Union, Optional, List
from .content_loader import parse_response_data
from . import config as CFG
from .models import Response, Request, HttpMethod, Cookie
from .exceptions import NetworkError
from .handler import Handler, HandlerSearchFailed, HandlerSearchSuccess
from .direct_request_interceptor import MultiRequestInterceptor


@beartype
class Page:
    def __init__(self, api, page):
        self.API = api
        self._page = page


    @property
    def playwright_page(self):
        """Возвращает объект Playwright Page."""
        if not self._page:
            raise RuntimeError(CFG.LOGS.PAGE_NOT_AVAILABLE)
        return self._page

    @property
    def domain(self) -> str:
        """
        Возвращает домен текущей страницы.
        
        Returns:
            str: Домен текущей страницы.
        """
        if not self._page:
            raise RuntimeError(CFG.LOGS.PAGE_NOT_AVAILABLE)
        
        current_url = self.playwright_page.url
        if current_url and current_url != "about:blank":
            parsed_url = urlparse(current_url)
            return parsed_url.netloc or "localhost"
        
        return "localhost"


    async def get_cookies(self) -> List[Cookie]:
        """
        Получает cookies текущей страницы в формате Cookie объектов.
        
        Returns:
            List[Cookie]: Список объектов Cookie для текущей страницы.
        """
        if not self._page:
            raise RuntimeError(CFG.LOGS.PAGE_NOT_AVAILABLE)
        
        # Получаем cookies в формате Playwright
        return await self.API.get_cookies(self.playwright_page.url)


    async def add_cookies(self, cookies: Union[dict, Cookie, List[Cookie]]) -> None:
        """
        Добавляет cookies в текущий контекст браузера. Если не установлен, устанавливает домен.
        
        Args:
            cookies: Может быть:
                - dict: {"name": "value"} - простое добавление cookie
                - List[dict]: [{"name": "value"}, ...] - множественное добавление
                - Cookie: объект Cookie с детальными параметрами
                - List[Cookie]: список объектов Cookie
        """
        if not self._page:
            raise RuntimeError(CFG.LOGS.PAGE_NOT_AVAILABLE)
        
        # Получаем текущий домен страницы
        current_domain = self.domain
        
        # Нормализуем входные данные к списку Cookie объектов
        cookie_objects = []
        
        if isinstance(cookies, dict):
            # Одиночный dict: {"name": "value"}
            for name, value in cookies.items():
                cookie_objects.append(Cookie(name=name, value=value, domain=current_domain))
        elif isinstance(cookies, list):
            for item in cookies:
                if isinstance(item, Cookie):
                    # Cookie объект в списке - подставляем домен если не указан
                    if not item.domain:
                        item.domain = current_domain
                    cookie_objects.append(item)
        elif isinstance(cookies, Cookie):
            # Одиночный Cookie объект - подставляем домен если не указан
            if not cookies.domain:
                cookies.domain = current_domain
            cookie_objects.append(cookies)
        
        # Вызываем метод API для добавления cookies
        await self.API.add_cookies(cookie_objects)
    
    async def remove_cookies(self, cookies: Union[str, List[str], Cookie, List[Cookie]]) -> None:
        """
        Удаляет cookies из текущего контекста браузера. Если не установлен, устанавливает домен.
        
        Args:
            cookies: Может быть:
                - str: имя cookie для удаления (домен текущей страницы)
                - List[str]: список имен cookies для удаления (домен текущей страницы)
                - Cookie: объект Cookie для удаления (по имени и домену)
                - List[Cookie]: список объектов Cookie для удаления (по имени и домену)
        """
        if not self._page:
            raise RuntimeError(CFG.LOGS.PAGE_NOT_AVAILABLE)
        
        # Получаем текущий домен страницы
        current_url = self._page.url
        if current_url and current_url != "about:blank":
            parsed_url = urlparse(current_url)
            current_domain = parsed_url.netloc or "localhost"
        else:
            current_domain = "localhost"
        
        # Нормализуем входные данные
        normalized_cookies = []
        
        if isinstance(cookies, str):
            # Одиночное имя cookie - создаем Cookie объект с текущим доменом
            normalized_cookies.append(Cookie(name=cookies, value="", domain=current_domain))
        elif isinstance(cookies, list):
            for item in cookies:
                if isinstance(item, str):
                    # Имя cookie в списке - создаем Cookie объект с текущим доменом
                    normalized_cookies.append(Cookie(name=item, value="", domain=current_domain))
                elif isinstance(item, Cookie):
                    # Cookie объект в списке - подставляем домен если не указан
                    if not item.domain:
                        item.domain = current_domain
                    normalized_cookies.append(item)
        elif isinstance(cookies, Cookie):
            # Одиночный Cookie объект - подставляем домен если не указан
            if not cookies.domain:
                cookies.domain = current_domain
            normalized_cookies.append(cookies)
        
        # Вызываем метод API для удаления cookies
        await self.API.remove_cookies(normalized_cookies)


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
            try:
                await self._page.unroute("**/*", multi_interceptor.handle_route)
            except Exception as e:
                # Игнорируем ошибки при закрытии соединения (например, при Ctrl+C)
                self.API._logger.warning(CFG.LOGS.UNROUTE_CLEANUP_ERROR_DIRECT_FETCH.format(error=e))

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
        request_url = request if isinstance(request, str) else request.url
        self.API._logger.info(CFG.LOGS.INJECT_FETCH_STARTED.format(url=request_url))

        async def modify_request(request: Union[Request, str]) -> Request:
            """Создание и модификация объекта запроса"""
            # Создаем объект Request если передана строка
            if isinstance(request, str):
                default_headers = {"Content-Type": CFG.PARAMETERS.DEFAULT_CONTENT_TYPE}
                request_obj = Request(
                    url=request, 
                    headers=default_headers,
                    method=HttpMethod.GET
                )
                self.API._logger.debug(CFG.LOGS.INJECT_FETCH_REQUEST_CREATED.format(url=request))
            else:
                request_obj = request
                self.API._logger.debug(CFG.LOGS.INJECT_FETCH_REQUEST_EXISTING.format(url=request.url))

            # Применяем модификацию если функция задана
            if self.API.request_modifier_func:
                self.API._logger.debug(CFG.LOGS.INJECT_FETCH_MODIFIER_APPLYING)
                modified_request = self.API.request_modifier_func(copy.copy(request_obj))
                
                if asyncio.iscoroutinefunction(self.API.request_modifier_func):
                    modified_request = await modified_request
                    self.API._logger.debug(CFG.LOGS.INJECT_FETCH_MODIFIER_AWAITED)
                
                # Проверяем что возвращен объект Request
                if isinstance(modified_request, Request):
                    if modified_request.method != HttpMethod.ANY:
                        self.API._logger.info(CFG.LOGS.INJECT_FETCH_REQUEST_MODIFIED.format(
                            url=modified_request.url,
                            method=modified_request.method.value
                        ))
                        return modified_request
                    else:
                        self.API._logger.warning(CFG.LOGS.REQUEST_MODIFIER_ANY_TYPE)
                else:
                    self.API._logger.warning(CFG.LOGS.REQUEST_MODIFIER_FAILED_TYPE.format(object_type=type(modified_request)))
            
            return request_obj

        # Получаем модифицированный объект Request
        final_request = await modify_request(request)
        
        # Создаем специальный handler для перехвата нашего запроса
        # Используем ALL с ANY типом контента и указываем конкретный URL + метод
        request_interceptor_handler = Handler.ALL(
            startswith_url=final_request.real_url,
            method=final_request.method,
            max_responses=1 # Нам нужен только один запрос
        )
        
        self.API._logger.info(CFG.LOGS.INJECT_FETCH_INTERCEPTOR_SETUP.format(url=final_request.real_url))
        
        # Используем MultiRequestInterceptor для перехвата
        multi_interceptor = MultiRequestInterceptor(
            self.API, 
            [request_interceptor_handler], 
            final_request.real_url, 
            start_time
        )

        try:
            # Устанавливаем перехват маршрутов
            await self._page.route("**/*", multi_interceptor.handle_route)
            interceptor_waitor = multi_interceptor.wait_for_results(self.API.timeout)
            
            # JavaScript-код для выполнения запроса с возвратом статуса и заголовков
            script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), CFG.PARAMETERS.INJECT_FETCH_JS_FILE)
            self.API._logger.debug(CFG.LOGS.INJECT_FETCH_JS_LOADING.format(path=script_path))

            def load_inject_script():
                try:
                    with open(script_path, "r") as file:
                        return file.read()
                except FileNotFoundError:
                    error_msg = f"{CFG.ERRORS.JS_FILE_NOT_FOUND}: {script_path}"
                    self.API._logger.error(error_msg)
                    raise FileNotFoundError(error_msg)

            # Load the script once
            script = load_inject_script()

            # Подготавливаем данные для JavaScript
            body_str = json.dumps(final_request.body) if isinstance(final_request.body, dict) else "null"
            
            # Логируем параметры запроса
            self.API._logger.info(CFG.LOGS.INJECT_FETCH_JS_EVALUATING.format(
                url=final_request.real_url, 
                method=final_request.method.value
            ))
            
            # Сначала выполняем запрос через JavaScript
            result = await self._page.evaluate(f"({script})(\"{final_request.real_url}\", \"{final_request.method.value}\", {body_str}, {json.dumps(final_request.headers)})")
            
            # Логируем результат выполнения JavaScript
            self.API._logger.debug(CFG.LOGS.INJECT_FETCH_JS_COMPLETED.format(success=result.get('success', False)))
            
            # Затем ждём результатов перехвата
            intercept_results = await interceptor_waitor
        finally:
            # Очищаем перехват маршрутов
            self.API._logger.debug(CFG.LOGS.INJECT_FETCH_ROUTE_CLEANUP)
            try:
                await self._page.unroute("**/*", multi_interceptor.handle_route)
                self.API._logger.debug(CFG.LOGS.INJECT_FETCH_ROUTE_CLEANUP_SUCCESS)
            except Exception as e:
                # Игнорируем ошибки при закрытии соединения (например, при Ctrl+C)
                self.API._logger.debug(CFG.LOGS.UNROUTE_CLEANUP_ERROR_INJECT_FETCH.format(error=e))
        
        # Проверяем, что вернул JavaScript - успешный ответ или ошибку
        if not result.get('success', False):
            # Возвращаем объект ошибки
            error_info = result.get('error', {})
            error_name = error_info.get('name', CFG.ERRORS.UNKNOWN)
            error_message = error_info.get('message', CFG.ERRORS.MESSAGE_UNKNOWN)
            
            self.API._logger.error(CFG.LOGS.INJECT_FETCH_ERROR.format(
                error_name=error_name,
                error_message=error_message
            ))
            
            return NetworkError(
                name=error_name,
                message=error_message,
                details=error_info.get('details', {}),
                timestamp=error_info.get('timestamp', ''),
                duration=time.time() - start_time
            )
        
        # Получаем заголовки из перехваченного запроса
        captured_request_headers = {}
        if intercept_results and len(intercept_results) > 0:
            first_result = intercept_results[0]
            if isinstance(first_result, HandlerSearchSuccess) and len(first_result.responses) > 0:
                captured_request_headers = first_result.responses[0].request_headers
                self.API._logger.info(CFG.LOGS.INJECT_FETCH_HEADERS_CAPTURED.format(
                    headers_count=len(captured_request_headers)
                ))
                self.API._logger.debug(f"Captured request headers: {captured_request_headers}")
            else:
                self.API._logger.info(CFG.LOGS.INJECT_FETCH_NO_HEADERS)
        else:
            self.API._logger.info(CFG.LOGS.INJECT_FETCH_NO_HEADERS)
        
        # Проверяем результаты перехвата и получаем объект ответа
        if intercept_results and len(intercept_results) > 0 and isinstance(intercept_results[0], HandlerSearchSuccess) and len(intercept_results[0].responses) > 0:
            real_resp = intercept_results[0].responses[0]
            duration = real_resp.duration
        else:
            self.API._logger.warning(CFG.LOGS.INJECT_FETCH_NO_VALID_RESPONSE)
            duration = time.time() - start_time
            # Возвращаем NetworkError, так как перехват не удался
            return NetworkError(
                name=CFG.ERRORS.UNKNOWN,
                message=CFG.LOGS.INJECT_FETCH_INTERCEPTION_FAILED.format(reason="No response captured"),
                details={"url": final_request.real_url, "method": final_request.method.value},
                timestamp="",
                duration=duration
            )
        
        self.API._logger.info(CFG.LOGS.INJECT_FETCH_COMPLETED.format(duration=duration))
        
        return real_resp

    async def close(self):
        """Закрывает страницу"""
        if self._page:
            await self._page.close()
            self._page = None
            self.API._logger.info(CFG.LOGS.PAGE_CLOSED)
        else:
            self.API._logger.info(CFG.ERRORS.NO_PAGE_TO_CLOSE)

import os
import asyncio
import time
import json
from beartype import beartype
from beartype.typing import Union, Optional
from .tools import parse_response_data
from . import config as CFG
from .models import Response, NetworkError, Handler


class Page:
    def __init__(self, api, page):
        self.API = api
        self._page = page
    
    @beartype
    async def direct_fetch(self, url: str, handler: Handler = Handler.MAIN(), wait_selector: Optional[str] = None) -> Response:
        start_time = time.time()

        # Готовим Future и колбэки для response и request
        loop = asyncio.get_running_loop()
        response_future = loop.create_future()
        captured_request_headers = {}

        def _on_request(req):
            # Перехватываем заголовки запроса для нужного URL
            if req.url.startswith(url):
                nonlocal captured_request_headers
                captured_request_headers = dict(req.headers)

        def _on_response(resp):
            if handler.should_capture(resp, url) and not response_future.done():
                response_future.set_result(resp)

        self.API._bcontext.on("request", _on_request)
        self.API._bcontext.on("response", _on_response)

        try:
            await self._page.evaluate(f"window.location.href = '{url}';")

            # Ожидание селектора если указан
            if wait_selector:
                await self._page.wait_for_selector(wait_selector, timeout=self.API.timeout * CFG.MILLISECONDS_MULTIPLIER)

            resp = await asyncio.wait_for(response_future, timeout=self.API.timeout)

            # Получаем сырые данные и content-type для единообразного парсинга
            raw_data = await resp.text()
            data = parse_response_data(raw_data, resp.headers.get("content-type", ""))
        finally:
            # Удаляем колбэки после завершения
            self.API._bcontext.remove_listener("request", _on_request)
            self.API._bcontext.remove_listener("response", _on_response)
        
        # Вычисляем метрики производительности
        duration = time.time() - start_time
        self.API._logger.info(f"{CFG.LOG_REQUEST_COMPLETED} {duration:.3f}s")
        
        # Возвращаем объект Response с атрибутами status, request_headers, response_headers, response, duration
        return Response(
            status=resp.status,
            request_headers=captured_request_headers,
            response_headers=dict(resp.headers),
            response=data,
            duration=duration
        )

    @beartype
    async def inject_fetch(self, url: str, method: str = "GET", body: dict | None = None) -> Union[Response, NetworkError]:
        """
        Выполнение HTTP-запроса через JavaScript в браузере.

        Args:
            url (str): API endpoint.
            method (str): HTTP метод (GET/POST).
            body (dict): Данные для POST-запросов.

        Returns:
            dict: Ответ API.
        """
        
        async def gen_headers() -> dict:
            """Генерация заголовков для запроса"""
            headers = {
                "Content-Type": CFG.DEFAULT_CONTENT_TYPE
            }
            if self.API.inject_headers_gen:
                if not asyncio.iscoroutinefunction(self.API.inject_headers_gen):
                    custom_headers = self.API.inject_headers_gen(self)
                else:
                    custom_headers = await self.API.inject_headers_gen(self)

                if isinstance(custom_headers, dict):
                    headers.update(custom_headers)
                else:
                    self.API._logger.warning(f"{CFG.LOG_CUSTOM_HEADERS_WARNING}: {custom_headers}")
            return headers

        start_time = time.time()
        
        # Перехватываем заголовки запроса через Playwright
        captured_request_headers = {}
        
        def _on_request(req):
            # Перехватываем заголовки запроса для нужного URL
            if req.url == url:
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

            headers = await gen_headers()
            body_str = "null" if body is None else json.dumps(body)
            result = await self._page.evaluate(f"({script})(\"{url}\", \"{method}\", {body_str}, {json.dumps(headers)})")
            
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
                from urllib.parse import urlparse
                parsed_url = urlparse(url)
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
            duration=duration
        )

    async def close(self):
        """Закрывает страницу"""
        if self._page:
            await self._page.close()
            self._page = None
            self.API._logger.info(CFG.LOG_PAGE_CLOSED)
        else:
            self.API._logger.info(CFG.LOG_NO_PAGE_TO_CLOSE)

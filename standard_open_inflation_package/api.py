import os
import asyncio
import urllib.parse
from camoufox import AsyncCamoufox
import logging
from beartype import beartype
from beartype.typing import Union, Optional, Callable
import json
from enum import Enum
from io import BytesIO
import time
from .tools import parse_proxy, parse_response_data


class HttpMethod(Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"


class Response:
    """Класс для представления ответа от API"""
    
    @beartype
    def __init__(self, status: int, headers: dict, response: Union[dict, list, str, BytesIO], 
                 duration: float = 0.0):
        self.status = status
        self.headers = headers
        self.response = response
        self.duration = duration  # Время выполнения запроса в секундах


class Handler:
    @beartype
    def __init__(self, handler_type: str, target_url: Optional[str] = None, content_type: Optional[str] = None, method: HttpMethod = HttpMethod.GET):
        self.handler_type = handler_type
        self.target_url = target_url
        self.content_type = content_type
        self.method = method
    
    @classmethod
    @beartype
    def MAIN(cls, method: HttpMethod = HttpMethod.GET):
        return cls("main", method=method)
    
    @classmethod
    @beartype
    def CAPTURE(cls, target_url: Optional[str] = None, type: Optional[str] = None, method: HttpMethod = HttpMethod.GET):
        return cls("capture", target_url, type, method)
    
    @classmethod
    @beartype
    def JSON(cls, target_url: Optional[str] = None, method: HttpMethod = HttpMethod.GET):
        return cls("json", target_url, "json", method)
    
    @classmethod
    @beartype
    def JS(cls, target_url: Optional[str] = None, method: HttpMethod = HttpMethod.GET):
        return cls("js", target_url, "js", method)
    
    @classmethod
    @beartype
    def CSS(cls, target_url: Optional[str] = None, method: HttpMethod = HttpMethod.GET):
        return cls("css", target_url, "css", method)
    
    @classmethod
    @beartype
    def IMAGE(cls, target_url: Optional[str] = None, method: HttpMethod = HttpMethod.GET):
        return cls("image", target_url, "image", method)

    @beartype
    def should_capture(self, resp, base_url: str) -> bool:
        """Определяет, должен ли handler захватить данный response"""
        full_url = urllib.parse.unquote(resp.url)
        ctype = resp.headers.get("content-type", "").lower()
        
        # Проверяем метод запроса
        if resp.request.method != self.method.value:
            return False
        
        if self.handler_type == "main":
            # Для MAIN проверяем основную страницу
            if not full_url.startswith(base_url):
                return False
            return "application/json" in ctype or "text/html" in ctype or "image/" in ctype
        
        # Для всех остальных типов проверяем URL если указан
        if self.target_url and not full_url.startswith(self.target_url):
            return False
        
        # Проверяем тип контента на основе реального content-type из response
        if self.handler_type == "json":
            return "application/json" in ctype
        elif self.handler_type == "js":
            return 'javascript' in ctype
        elif self.handler_type == "css":
            return 'text/css' in ctype
        elif self.handler_type == "image":
            return "image/" in ctype
        elif self.handler_type == "capture":
            # Любой первый запрос
            return True
        
        return False


class BaseAPI:
    """
    Класс для загрузки JSON/image/html.
    """

    @beartype
    def __init__(self,
                 debug:              bool               = False,
                 proxy:              str | None         = None,
                 autoclose_browser:  bool               = False,
                 trust_env:          bool               = False,
                 timeout:            float              = 10.0,
                 start_func:         Callable | None = None,
                 inject_headers_gen: Callable | None = None
        ) -> None:
        # Используем property для установки настроек
        self.debug = debug
        self.proxy = proxy
        self.autoclose_browser = autoclose_browser
        self.trust_env = trust_env
        self.timeout = timeout
        self.start_func = start_func
        self.inject_headers_gen = inject_headers_gen

        self._browser = None
        self._bcontext = None
        self.cookies = {}  # Инициализируем cookies

        self._logger = logging.getLogger(self.__class__.__name__)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('[%(asctime)s] %(levelname)s %(name)s: %(message)s')
        handler.setFormatter(formatter)
        if not self._logger.hasHandlers():
            self._logger.addHandler(handler)

    # Properties для настроек
    @property
    def debug(self) -> bool:
        return self._debug

    @debug.setter
    @beartype
    def debug(self, value: bool) -> None:
        self._debug = value

    @property
    def proxy(self) -> str | None:
        return self._proxy

    @proxy.setter
    @beartype
    def proxy(self, value: str | None) -> None:
        self._proxy = value

    @property
    def autoclose_browser(self) -> bool:
        return self._autoclose_browser

    @autoclose_browser.setter
    @beartype
    def autoclose_browser(self, value: bool) -> None:
        self._autoclose_browser = value

    @property
    def trust_env(self) -> bool:
        return self._trust_env

    @trust_env.setter
    @beartype
    def trust_env(self, value: bool) -> None:
        self._trust_env = value

    @property
    def timeout(self) -> float:
        return self._timeout

    @timeout.setter
    @beartype
    def timeout(self, value: float) -> None:
        if value <= 0:
            raise ValueError("Timeout must be positive")
        if value > 3600:  # 1 час максимум
            raise ValueError("Timeout too large (max 3600 seconds)")
        self._timeout = value
    
    @property
    def start_func(self) -> Callable | None:
        return self._start_func
    
    @start_func.setter
    @beartype
    def start_func(self, value: Callable | None) -> None:
        self._start_func = value

    @property
    def inject_headers_gen(self) -> Callable | None:
        return self._inject_headers_gen
    
    @inject_headers_gen.setter
    @beartype
    def inject_headers_gen(self, value: Callable | None) -> None:
        self._inject_headers_gen = value
    

    @beartype
    async def new_direct_fetch(self, url: str, handler: Handler = Handler.MAIN(), wait_selector: Optional[str] = None) -> Response:  
        page = await self.new_page()
        response = await page.direct_fetch(url, handler, wait_selector)
        await page.close()
        return response

    @beartype
    async def new_page(self) -> 'Page':
        """
        Создает новую страницу в текущем контексте браузера.
        :return: Объект Page
        """
        if not self._bcontext:
            await self.new_session(include_browser=True)
        
        self._logger.info("Creating a new page in the browser context...")
        page = await self._bcontext.new_page()
        self._logger.info("New page created successfully.")
        
        return Page(self, page)

    @beartype
    async def new_session(self, include_browser: bool = False) -> None:
        await self.close(include_browser=include_browser)

        if include_browser:
            prox = parse_proxy(self.proxy, self.trust_env, self._logger)
            self._logger.info(f"Opening new browser connection with proxy: {'SYSTEM_PROXY' if prox and not self.proxy else prox}")
            self._browser = await AsyncCamoufox(headless=not self.debug, proxy=prox, geoip=True).__aenter__()
            self._bcontext = await self._browser.new_context()
            self._logger.info(f"A new browser context has been opened.")
            if self.start_func:
                self._logger.info(f"Executing start function: {self.start_func.__name__}")
                if not asyncio.iscoroutinefunction(self.start_func):
                    self.start_func(self)
                else:
                    await self.start_func(self)
                self._logger.info(f"Start function {self.start_func.__name__} executed successfully.")
            self._logger.info("New session created successfully.")

    @beartype
    async def close(
        self,
        include_browser: bool = False
    ) -> None:
        """
        Close the Camoufox browser if it is open.
        :param include_browser: close browser if True
        """
        to_close = []
        if include_browser:
            to_close.append("bcontext")
            to_close.append("browser")

        self._logger.info(f"Preparing to close: {to_close if to_close else 'nothing'}")

        if not to_close:
            self._logger.warning("No connections to close")
            return

        checks = {
            "browser": lambda a: a is not None,
            "bcontext": lambda a: a is not None
        }

        for name in to_close:
            attr = getattr(self, f"_{name}", None)
            if checks[name](attr):
                self._logger.info(f"Closing {name} connection...")
                try:
                    if name == "browser":
                        await attr.__aexit__(None, None, None)
                    elif name in ["bcontext"]:
                        await attr.close()
                    else:
                        raise ValueError(f"Unknown connection type: {name}")
                    
                    setattr(self, f"_{name}", None)
                    self._logger.info(f"The {name} connection was closed")
                except Exception as e:
                    self._logger.error(f"Error closing {name}: {e}")
            else:
                self._logger.warning(f"The {name} connection was not open")


class Page:
    def __init__(self, api: BaseAPI, page):
        self.API = api
        self._page = page
    
    @beartype
    async def direct_fetch(self, url: str, handler: Handler = Handler.MAIN(), wait_selector: Optional[str] = None) -> Response:
        start_time = time.time()

        # Готовим Future и колбэк
        loop = asyncio.get_running_loop()
        response_future = loop.create_future()

        def _on_response(resp):
            if handler.should_capture(resp, url) and not response_future.done():
                response_future.set_result(resp)

        self.API._bcontext.on("response", _on_response)

        try:
            await self._page.evaluate(f"window.location.href = '{url}';")

            # Ожидание селектора если указан
            if wait_selector:
                await self._page.wait_for_selector(wait_selector, timeout=self.API.timeout * 1000)

            resp = await asyncio.wait_for(response_future, timeout=self.API.timeout)

            # Получаем сырые данные и content-type для единообразного парсинга
            raw_data = await resp.text()
            data = parse_response_data(raw_data, resp.headers.get("content-type", ""))

            # Собираем куки
            raw = await self.API._bcontext.cookies()
            new_cookies = {
                urllib.parse.unquote(c["name"]): urllib.parse.unquote(c["value"])
                for c in raw
            }
            self.cookies = new_cookies
        finally:
            # Удаляем колбэк после завершения
            self.API._bcontext.remove_listener("response", _on_response)
        
        # Вычисляем метрики производительности
        duration = time.time() - start_time
        self.API._logger.info(f"Request completed in {duration:.3f}s")
        
        # Возвращаем объект Response с атрибутами status, headers, response, duration
        return Response(
            status=resp.status,
            headers=dict(resp.headers),
            response=data,
            duration=duration
        )

    @beartype
    async def inject_fetch(self, url: str, method: str = "GET", body: dict | None = None) -> Response:
        """
        Выполнение HTTP-запроса через JavaScript в браузере.

        Args:
            url (str): API endpoint.
            method (str): HTTP метод (GET/POST).
            data (dict): Данные для POST-запросов.

        Returns:
            dict: Ответ API.
        """
        
        # Получение accessToken из cookies
        #access_token = await self._page.evaluate("""
        #    () => {
        #        const cookies = document.cookie.split('; ').reduce((acc, cookie) => {
        #            const [key, value] = cookie.split('=');
        #            acc[key] = value;
        #            return acc;
        #        }, {});
        #        return JSON.parse(decodeURIComponent(cookies['session'])).accessToken;
        #    }
        #""")
        #if not access_token:
        #    raise ValueError("Access token not found")


        async def gen_headers() -> dict:
            """Генерация заголовков для запроса"""
            headers = {
                "Content-Type": "application/json"
            }
            if self.API.inject_headers_gen:
                if not asyncio.iscoroutinefunction(self.API.inject_headers_gen):
                    custom_headers = self.API.inject_headers_gen(self)
                else:
                    custom_headers = await self.API.inject_headers_gen(self)

                if isinstance(custom_headers, dict):
                    headers = custom_headers
                else:
                    self.API._logger.warning(f"Custom headers generator returned non-dict: {custom_headers}")
            return headers

        start_time = time.time()

        # JavaScript-код для выполнения запроса с возвратом статуса и заголовков
        # Function to load JavaScript code from file
        script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "inject_fetch.js")

        def load_inject_script():
            try:
                with open(script_path, "r") as file:
                    return file.read()
            except FileNotFoundError:
                raise FileNotFoundError(f"JavaScript file not found at: {script_path}")

        # Load the script once
        script = load_inject_script()

        headers = await gen_headers()
        body_str = "null" if body is None else json.dumps(body)
        result = await self._page.evaluate(f"({script})(\"{url}\", \"{method}\", {body_str}, {json.dumps(headers)})")
        duration = time.time() - start_time
        
        # Парсим данные в зависимости от Content-Type
        raw_data = result['data']
        content_type = result['headers'].get('content-type', '')
        parsed_data = parse_response_data(raw_data, content_type)
        
        self.API._logger.info(f"Inject fetch request completed in {duration:.3f}s")
        
        return Response(
            status=result['status'],
            headers=result['headers'],
            response=parsed_data,
            duration=duration
        )

    async def close(self):
        """Закрывает страницу"""
        if self._page:
            await self._page.close()
            self._page = None
            self.API._logger.info("Page closed successfully")
        else:
            self.API._logger.info("No page to close")

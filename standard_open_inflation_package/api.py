import aiohttp
import asyncio
import urllib.parse
from camoufox import AsyncCamoufox
import logging
from beartype import beartype
from beartype.typing import Union, Optional
from enum import Enum
from io import BytesIO
import time
from .tools import parse_proxy


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


class BaseAPI:
    """
    Класс для загрузки JSON/image/html.
    """

    @beartype
    def __init__(self,
                 debug:             bool       = False,
                 proxy:             str | None = None,
                 autoclose_browser: bool       = False,
                 trust_env:         bool       = False,
                 timeout:           float      = 10.0
        ) -> None:
        # Используем property для установки настроек
        self.debug = debug
        self.proxy = proxy
        self.autoclose_browser = autoclose_browser
        self.trust_env = trust_env
        self.timeout = timeout
        
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


    @beartype
    async def fetch(self, url: str, handler: Handler = Handler.MAIN(), wait_selector: Optional[str] = None) -> Response:  
        if not self._bcontext:
            await self.new_session(include_browser=True)
        
        start_time = time.time()

        page = await self._bcontext.new_page()

        # Готовим Future и колбэк
        loop = asyncio.get_running_loop()
        response_future = loop.create_future()

        def _on_response(resp):
            full_url = urllib.parse.unquote(resp.url)
            ctype = resp.headers.get("content-type", "").lower()
            
            if handler.handler_type == "main":
                # Для MAIN проверяем основную страницу
                if not (full_url.startswith(url) and resp.request.method == handler.method.value):
                    return
                if "application/json" in ctype or "text/html" in ctype or "image/" in ctype:
                    if not response_future.done():
                        response_future.set_result(resp)
            else:
                # Для всех остальных типов
                should_capture = False
                
                # Проверяем URL если указан
                if handler.target_url and not full_url.startswith(handler.target_url):
                    return
                # Проверяем метод запроса
                elif resp.request.method != handler.method.value:
                    return
                
                # Проверяем тип контента на основе реального content-type из response
                if handler.handler_type == "json":
                    should_capture = "application/json" in ctype
                elif handler.handler_type == "js":
                    should_capture = 'javascript' in ctype
                elif handler.handler_type == "css":
                    should_capture = 'text/css' in ctype
                elif handler.handler_type == "image":
                    should_capture = "image/" in ctype
                elif handler.handler_type == "capture":
                    # Любой первый запрос
                    should_capture = True
                
                if should_capture and not response_future.done():
                    response_future.set_result(resp)

        self._bcontext.on("response", _on_response)

        async with self._bcontext.expect_page() as ev:
            await page.evaluate(f"window.open('{url}', '_blank');")
        popup = await ev.value

        # Ожидание селектора если указан
        if wait_selector:
            await popup.wait_for_selector(wait_selector, timeout=self.timeout * 1000)

        resp = await asyncio.wait_for(response_future, timeout=self.timeout)

        # Обработка ответа ВСЕГДА на основе реального content-type из response
        ctype = resp.headers.get("content-type", "").lower()
        
        if "application/json" in ctype:
            data = await resp.json()
        elif "image/" in ctype:
            # Для изображений возвращаем BytesIO с заполненным name
            image_bytes = await resp.body()
            data = BytesIO(image_bytes)
            # Извлекаем имя файла из URL или используем расширение на основе content-type
            url_path = urllib.parse.urlparse(resp.url).path
            if url_path and '.' in url_path:
                data.name = url_path.split('/')[-1]
            else:
                # Определяем расширение по content-type
                ext_map = {
                    'image/jpeg': '.jpg',
                    'image/jpg': '.jpg', 
                    'image/png': '.png',
                    'image/gif': '.gif',
                    'image/webp': '.webp',
                    'image/svg+xml': '.svg'
                }
                ext = ext_map.get(ctype, '.img')
                data.name = f"image{ext}"
        else:
            data = await resp.text()

        # Собираем куки
        raw = await self._bcontext.cookies()
        new_cookies = {
            urllib.parse.unquote(c["name"]): urllib.parse.unquote(c["value"])
            for c in raw
        }

        await popup.close()
        await page.close()

        self.cookies = new_cookies
        
        # Вычисляем метрики производительности
        duration = time.time() - start_time
        self._logger.info(f"Request completed in {duration:.3f}s")
        
        # Возвращаем объект Response с атрибутами status, headers, response, duration
        return Response(
            status=resp.status,
            headers=dict(resp.headers),
            response=data,
            duration=duration
        )

    @beartype
    async def new_session(self, include_browser: bool = False) -> None:
        await self.close(include_browser=include_browser)

        if include_browser:
            prox = parse_proxy(self.proxy, self.trust_env, self._logger)
            self._logger.info(f"Opening new browser connection with proxy: {'SYSTEM_PROXY' if prox and not self.proxy else prox}")
            self._browser = await AsyncCamoufox(headless=not self.debug, proxy=prox, geoip=True).__aenter__()
            self._bcontext = await self._browser.new_context()
            self._logger.info(f"A new browser context has been opened.")

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



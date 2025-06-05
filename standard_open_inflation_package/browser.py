import asyncio
import urllib.parse
from camoufox import AsyncCamoufox
import logging
from beartype import beartype
from beartype.typing import Union, Optional, Callable, List, TYPE_CHECKING, Any
from .tools import parse_proxy
from . import config as CFG
from .handler import Handler, HandlerSearchSuccess, HandlerSearchFailed
from .models import Cookie

if TYPE_CHECKING:
    pass


@beartype
class BaseAPI:
    """
    Класс для загрузки JSON/image/html.
    """

    def __init__(self,
                 debug:                 bool            = False,
                 proxy:                 str | None      = None,
                 autoclose_browser:     bool            = False,
                 trust_env:             bool            = False,
                 timeout:               float           = 10.0,
                 start_func:            Callable | None = None,
                 request_modifier_func: Callable | None = None
        ) -> None:
        # Используем property для установки настроек
        self.debug = debug
        self.proxy = proxy
        self.autoclose_browser = autoclose_browser
        self.trust_env = trust_env
        self.timeout = timeout
        self.start_func = start_func
        self.request_modifier_func = request_modifier_func

        self._browser = None
        self._bcontext = None

        self._logger = logging.getLogger(self.__class__.__name__)
        handler = logging.StreamHandler()
        formatter = logging.Formatter(CFG.PARAMETERS.LOG_FORMAT)
        handler.setFormatter(formatter)
        if not self._logger.hasHandlers():
            self._logger.addHandler(handler)

    async def get_cookies(self, urls: Union[str, List[str], None] = None) -> List[Cookie]:
        """
        Возвращает текущие куки в виде списка объектов Cookie.

        Args:
            urls: Список URL-адресов, для которых нужно получить куки.
                  Если None, возвращает куки для всех URL в текущем контексте.
                  Если строка, то возвращает куки для одного URL.
        Returns:
            List[Cookie]: Список объектов Cookie, полученных из текущего контекста браузера.
        """
        if not self._bcontext:
            return []
        
        if isinstance(urls, str):
            urls = [urls]

        raw = await self._bcontext.cookies(urls=urls)
        cookies = [
            Cookie.from_playwright_dict(cookie_data) for cookie_data in raw  # type: ignore
        ]
        return cookies


    async def add_cookies(self, cookies: Union[Cookie, List[Cookie]]) -> None:
        """
        Добавляет cookies в текущий контекст браузера.
        
        Args:
            cookies: Может быть:
                - dict: {"name": "value"} - простое добавление cookie
                - List[dict]: [{"name": "value"}, ...] - множественное добавление
        """
        # Нормализуем входные данные к списку Cookie объектов
        cookie_objects = []
        
        if isinstance(cookies, list):
            cookie_objects = cookies
        else:
            # Одиночный Cookie объект
            cookie_objects.append(cookies)
        
        # Добавляем cookies в браузер
        playwright_cookies = []
        for cookie in cookie_objects:
            # Если домен не указан, используем текущий домен
            cookie_dict = cookie.to_playwright_dict()
            if not cookie.path:
                cookie_dict['path'] = "/"
            
            playwright_cookies.append(cookie_dict)
            self._logger.debug(CFG.LOGS.COOKIE_ADDED.format(
                name=cookie.name, 
                value=cookie.value, 
                domain=cookie.domain
            ))
        
        if playwright_cookies:
            await self._bcontext.add_cookies(playwright_cookies)
            self._logger.info(CFG.LOGS.COOKIES_ADDED.format(count=len(playwright_cookies)))

    async def remove_cookies(self, cookies: Union[str, List[str], Cookie, List[Cookie]]) -> None:
        """
        Удаляет cookies из текущего контекста браузера.
        
        Args:
            cookies: Может быть:
                - str: имя cookie для удаления
                - List[str]: список имен cookies для удаления
                - Cookie: объект Cookie для удаления (по имени и домену)
                - List[Cookie]: список объектов Cookie для удаления (по имени и домену)
        """
        
        # Получаем текущие cookies
        current_cookies = await self._bcontext.cookies()
        
        # Нормализуем входные данные к списку имен или (имя, домен) пар
        cookies_to_remove = []
        
        if isinstance(cookies, str):
            cookies_to_remove.append((cookies, None))
            
        elif isinstance(cookies, list):
            for item in cookies:
                if isinstance(item, str):
                    cookies_to_remove.append((item, None))
                else:
                    # Cookie объект
                    cookies_to_remove.append((item.name, item.domain))
        else:
            # Одиночный Cookie объект
            cookies_to_remove.append((cookies.name, cookies.domain))
        
        # Удаляем cookies
        removed_count = 0
        for cookie_name, cookie_domain in cookies_to_remove:
            # Ищем подходящие cookies для удаления
            for current_cookie in current_cookies[:]:  # Копия списка для безопасного удаления
                if current_cookie.get('name') == cookie_name:
                    # Если домен указан, проверяем его совпадение
                    if cookie_domain is None or current_cookie.get('domain') == cookie_domain:
                        # Удаляем cookie (очищаем его значение с истекшей датой)
                        await self._bcontext.add_cookies([{
                            'name': cookie_name,
                            'value': '',
                            'domain': current_cookie.get('domain', 'localhost'),
                            'path': current_cookie.get('path', '/'),
                            'expires': 0  # Истекший cookie
                        }])
                        current_cookies.remove(current_cookie)
                        removed_count += 1
                        self._logger.debug(CFG.LOGS.COOKIE_REMOVED.format(name=cookie_name))
                        break
            else:
                self._logger.debug(CFG.LOGS.COOKIE_NOT_FOUND.format(name=cookie_name))
        
        if removed_count > 0:
            self._logger.info(CFG.LOGS.COOKIES_REMOVED.format(count=removed_count))


    # Properties для настроек
    @property
    def debug(self) -> bool:
        return self._debug

    @debug.setter
    def debug(self, value: bool) -> None:
        self._debug = value

    @property
    def proxy(self) -> str | None:
        return self._proxy

    @proxy.setter
    def proxy(self, value: str | None) -> None:
        self._proxy = value

    @property
    def autoclose_browser(self) -> bool:
        return self._autoclose_browser

    @autoclose_browser.setter
    def autoclose_browser(self, value: bool) -> None:
        self._autoclose_browser = value

    @property
    def trust_env(self) -> bool:
        return self._trust_env

    @trust_env.setter
    def trust_env(self, value: bool) -> None:
        self._trust_env = value

    @property
    def timeout(self) -> float:
        return self._timeout

    @timeout.setter
    def timeout(self, value: float) -> None:
        if value <= 0:
            raise ValueError(CFG.ERRORS.TIMEOUT_POSITIVE)
        if value > CFG.PARAMETERS.MAX_TIMEOUT_SECONDS:
            raise ValueError(CFG.ERRORS.TIMEOUT_TOO_LARGE)
        self._timeout = value
    
    @property
    def start_func(self) -> Callable | None:
        return self._start_func
    
    @start_func.setter
    def start_func(self, value: Callable | None) -> None:
        self._start_func = value

    @property
    def request_modifier_func(self) -> Callable | None:
        return self._request_modifier_func
    
    @request_modifier_func.setter
    def request_modifier_func(self, value: Callable | None) -> None:
        self._request_modifier_func = value
    

    async def new_direct_fetch(self, url: str, handlers: Handler | List[Handler] = Handler.MAIN(), wait_selector: Optional[str] = None) -> List[Union[HandlerSearchSuccess, HandlerSearchFailed]]:  
        page = await self.new_page()
        response = await page.direct_fetch(url, handlers, wait_selector)
        await page.close()
        return response

    async def new_page(self):
        """
        Создает новую страницу в текущем контексте браузера.
        :return: Объект Page
        """
        # Отложенный импорт для избежания циклических зависимостей
        from .page import Page
        
        if not self._bcontext:
            await self.new_session(include_browser=True)
        
        self._logger.info(CFG.LOGS.NEW_PAGE_CREATING)
        page = await self._bcontext.new_page()
        self._logger.info(CFG.LOGS.NEW_PAGE_CREATED)

        return Page(self, page)

    async def new_session(self, include_browser: bool = True) -> None:
        await self.close(include_browser=include_browser)

        if include_browser:
            prox = parse_proxy(self.proxy, self.trust_env, self._logger)
            self._logger.info(CFG.LOGS.OPENING_BROWSER.format(proxy=CFG.LOGS.SYSTEM_PROXY if prox and not self.proxy else prox))
            self._browser = await AsyncCamoufox(headless=not self.debug, proxy=prox, geoip=True).__aenter__()
            self._bcontext = await self._browser.new_context()
            self._logger.info(CFG.LOGS.BROWSER_CONTEXT_OPENED)
            if self.start_func:
                self._logger.info(CFG.LOGS.START_FUNC_EXECUTING.format(function_name=self.start_func.__name__))
                if not asyncio.iscoroutinefunction(self.start_func):
                    self.start_func(self)
                else:
                    await self.start_func(self)
                self._logger.info(CFG.LOGS.START_FUNC_EXECUTED.format(function_name=self.start_func.__name__))
            self._logger.info(CFG.LOGS.NEW_SESSION_CREATED)

    async def close(
        self,
        include_browser: bool = True
    ) -> None:
        """
        Close the Camoufox browser if it is open.
        :param include_browser: close browser if True
        """
        to_close = []
        if include_browser:
            to_close.append("bcontext")
            to_close.append("browser")

        self._logger.info(CFG.LOGS.PREPARING_TO_CLOSE.format(connections=to_close if to_close else CFG.LOGS.NOTHING))

        if not to_close:
            self._logger.warning(CFG.LOGS.NO_CONNECTIONS)
            return

        checks = {
            "browser": lambda a: a is not None,
            "bcontext": lambda a: a is not None
        }

        for name in to_close:
            attr = getattr(self, f"_{name}", None)
            if checks[name](attr):
                self._logger.info(CFG.LOGS.CLOSING_CONNECTION.format(connection_name=name))
                try:
                    if name == "browser":
                        await attr.__aexit__(None, None, None)
                    elif name in ["bcontext"]:
                        await attr.close()
                    else:
                        raise ValueError(f"{CFG.ERRORS.UNKNOWN_CONNECTION_TYPE}: {name}")

                    setattr(self, f"_{name}", None)
                    self._logger.info(CFG.LOGS.CONNECTION_CLOSED_SUCCESS.format(connection_name=name, status=CFG.LOGS.CONNECTION_CLOSED))
                except Exception as e:
                    self._logger.error(CFG.ERRORS.BROWSER_COMPONENT_CLOSING_WITH_NAME.format(component_name=name, error=e))
            else:
                self._logger.warning(CFG.LOGS.CONNECTION_NOT_OPEN_WARNING.format(connection_name=name, status=CFG.LOGS.CONNECTION_NOT_OPEN))

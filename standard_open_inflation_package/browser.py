import asyncio
import urllib.parse
from camoufox import AsyncCamoufox
import logging
from beartype import beartype
from beartype.typing import Union, Optional, Callable, List
from .tools import parse_proxy
from . import config as CFG
from .handler import Handler, HandlerSearchSuccess, HandlerSearchFailed


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
        formatter = logging.Formatter('[%(asctime)s] %(levelname)s %(name)s: %(message)s')
        handler.setFormatter(formatter)
        if not self._logger.hasHandlers():
            self._logger.addHandler(handler)
    
    async def get_cookies(self) -> dict:
        """
        Возвращает текущие куки в виде словаря.
        """
        if not self._bcontext:
            return {}

        raw = await self._bcontext.cookies()
        new_cookies = {
            urllib.parse.unquote(c.get("name", "")): urllib.parse.unquote(c.get("value", ""))
            for c in raw
        }
        return new_cookies


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
            raise ValueError(CFG.ERROR_TIMEOUT_POSITIVE)
        if value > CFG.MAX_TIMEOUT_SECONDS:
            raise ValueError(CFG.ERROR_TIMEOUT_TOO_LARGE)
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
        
        self._logger.info(CFG.LOG_NEW_PAGE_CREATING)
        page = await self._bcontext.new_page()
        self._logger.info(CFG.LOG_NEW_PAGE_CREATED)
        
        return Page(self, page)

    async def new_session(self, include_browser: bool = True) -> None:
        await self.close(include_browser=include_browser)

        if include_browser:
            prox = parse_proxy(self.proxy, self.trust_env, self._logger)
            self._logger.info(f"{CFG.LOG_OPENING_BROWSER}: {CFG.LOG_SYSTEM_PROXY if prox and not self.proxy else prox}")
            self._browser = await AsyncCamoufox(headless=not self.debug, proxy=prox, geoip=True).__aenter__()
            self._bcontext = await self._browser.new_context()
            self._logger.info(CFG.LOG_BROWSER_CONTEXT_OPENED)
            if self.start_func:
                self._logger.info(f"{CFG.LOG_START_FUNC_EXECUTING}: {self.start_func.__name__}")
                if not asyncio.iscoroutinefunction(self.start_func):
                    self.start_func(self)
                else:
                    await self.start_func(self)
                self._logger.info(f"{CFG.LOG_START_FUNC_EXECUTING} {self.start_func.__name__} {CFG.LOG_START_FUNC_EXECUTED}")
            self._logger.info(CFG.LOG_NEW_SESSION_CREATED)

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

        self._logger.info(f"{CFG.LOG_PREPARING_TO_CLOSE}: {to_close if to_close else 'nothing'}")

        if not to_close:
            self._logger.warning(CFG.LOG_NO_CONNECTIONS)
            return

        checks = {
            "browser": lambda a: a is not None,
            "bcontext": lambda a: a is not None
        }

        for name in to_close:
            attr = getattr(self, f"_{name}", None)
            if checks[name](attr):
                self._logger.info(f"{CFG.LOG_CLOSING_CONNECTION} {name} connection...")
                try:
                    if name == "browser":
                        await attr.__aexit__(None, None, None)
                    elif name in ["bcontext"]:
                        await attr.close()
                    else:
                        raise ValueError(f"{CFG.ERROR_UNKNOWN_CONNECTION_TYPE}: {name}")
                    
                    setattr(self, f"_{name}", None)
                    self._logger.info(CFG.LOG_CONNECTION_CLOSED_SUCCESS.format(connection_name=name, status=CFG.LOG_CONNECTION_CLOSED))
                except Exception as e:
                    self._logger.error(f"{CFG.LOG_ERROR_CLOSING} {name}: {e}")
            else:
                self._logger.warning(CFG.LOG_CONNECTION_NOT_OPEN_WARNING.format(connection_name=name, status=CFG.LOG_CONNECTION_NOT_OPEN))

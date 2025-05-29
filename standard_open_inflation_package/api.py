import aiohttp
import asyncio
import urllib.parse
from camoufox import AsyncCamoufox
import logging
from beartype import beartype
from beartype.typing import Union, Optional
from .tools import parse_proxy


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
        self._debug = debug
        self._proxy = proxy
        self._autoclose_browser = autoclose_browser
        self._browser = None
        self._bcontext = None
        self._trust_env = trust_env
        self._timeout = timeout

        self._logger = logging.getLogger(self.__class__.__name__)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('[%(asctime)s] %(levelname)s %(name)s: %(message)s')
        handler.setFormatter(formatter)
        if not self._logger.hasHandlers():
            self._logger.addHandler(handler)


    async def fetch(self, url: str) -> dict:
        page = await self._bcontext.new_page()

        # Готовим Future и колбэк
        loop = asyncio.get_running_loop()
        response_future = loop.create_future()

        def _on_response(resp):
            full_url = urllib.parse.unquote(resp.url)
            if not (full_url.startswith(url) and resp.request.method == "GET"):
                return
            ctype = resp.headers.get("content-type", "").lower()
            if "application/json" not in ctype:
                return
            if not response_future.done():
                response_future.set_result(resp)

        self._bcontext.on("response", _on_response)

        async with self._bcontext.expect_page() as ev:
            await page.evaluate(f"window.open('{url}', '_blank');")
        popup = await ev.value

        resp = await asyncio.wait_for(response_future, timeout=10.0)
        data = await resp.json()

        # Собираем куки
        raw = await self._bcontext.cookies()
        new_cookies = {
            urllib.parse.unquote(c["name"]): urllib.parse.unquote(c["value"])
            for c in raw
        }

        await self._bcontext.close()

        self.cookies = new_cookies
        await self._new_session()
        
        return data

    @beartype
    async def new_session(self, include_browser: bool = False) -> None:
        await self.close(include_browser=include_browser)

        if include_browser:
            prox = parse_proxy(self._proxy, self._trust_env, self._logger)
            self._logger.info(f"Opening new browser connection with proxy: {'SYSTEM_PROXY' if prox and not self._proxy else prox}")
            self._browser = await AsyncCamoufox(headless=not self._debug, proxy=prox, geoip=True).__aenter__()
            self._bcontext = await self._browser.new_context()
            self._logger.info(f"A new browser context has been opened.")

    @beartype
    async def close(
        self,
        include_browser: bool = False
    ) -> None:
        """
        Close the aiohttp session and/or Camoufox browser if they are open.
        :param include_aiohttp: close aiohttp session if True
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



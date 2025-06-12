from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Optional, Tuple
from . import config as CFG


__all__ = [
    "BrowserEngine",
    "BaseBrowserConfig",
    "CamoufoxConfig",
    "PlaywrightConfig",
]


class BrowserEngine(Enum):
    CAMOUFOX = auto()
    FIREFOX = auto()
    CHROMIUM = auto()
    WEBKIT = auto()

    def __call__(self, **kwargs) -> "BaseBrowserConfig":
        if self is BrowserEngine.CAMOUFOX:
            return CamoufoxConfig(**kwargs)
        return PlaywrightConfig(engine=self, **kwargs)


@dataclass(slots=True)
class BaseBrowserConfig:
    headless: bool = True

    async def initialize(
        self, proxy: Optional[str]
    ) -> Tuple[Any, dict, Optional[Any]]:
        """Launch browser and return (browser, context_options, extra)."""
        raise NotImplementedError


@dataclass(slots=True)
class CamoufoxConfig(BaseBrowserConfig):
    humanization: Any = True
    geoip: bool = True

    async def initialize(
        self, proxy: Optional[str]
    ) -> Tuple[Any, dict, Optional[Any]]:
        try:
            from camoufox import AsyncCamoufox
        except ImportError as e:
            raise ImportError(CFG.LOGS.CAMOUFOX_NOT_INSTALLED) from e

        browser = await AsyncCamoufox(
            headless=self.headless,
            humanize=self.humanization,
            proxy=proxy,
            geoip=self.geoip,
        ).__aenter__()
        return browser, {}, None


@dataclass(slots=True)
class PlaywrightConfig(BaseBrowserConfig):
    engine: BrowserEngine = BrowserEngine.CHROMIUM
    ignore_https_errors: bool = True

    async def initialize(
        self, proxy: Optional[str]
    ) -> Tuple[Any, dict, Optional[Any]]:
        from playwright.async_api import async_playwright

        playwright = await async_playwright().start()
        launch_args = {"headless": self.headless}
        if proxy:
            launch_args["proxy"] = proxy

        launcher = {
            BrowserEngine.CHROMIUM: playwright.chromium,
            BrowserEngine.FIREFOX: playwright.firefox,
            BrowserEngine.WEBKIT: playwright.webkit,
        }[self.engine]

        browser = await launcher.launch(**launch_args)
        return browser, {"ignore_https_errors": self.ignore_https_errors}, playwright


from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Optional, Tuple

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
    headless: Optional[bool] = None

    async def initialize(
        self, proxy: Optional[str], debug: bool
    ) -> Tuple[Any, dict, Optional[Any]]:
        """Launch browser and return (browser, context_options, extra)."""
        raise NotImplementedError


@dataclass(slots=True)
class CamoufoxConfig(BaseBrowserConfig):
    humanization: Any = True
    geoip: bool = True

    async def initialize(
        self, proxy: Optional[str], debug: bool
    ) -> Tuple[Any, dict, Optional[Any]]:
        try:
            from camoufox import AsyncCamoufox
        except ImportError as e:
            print(
                "Camoufox is not installed. Install with 'pip install standard_open_inflation_package[camoufox]'"
            )
            raise

        headless = self.headless if self.headless is not None else not debug
        browser = await AsyncCamoufox(
            headless=headless,
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
        self, proxy: Optional[str], debug: bool
    ) -> Tuple[Any, dict, Optional[Any]]:
        from playwright.async_api import async_playwright

        headless = self.headless if self.headless is not None else not debug
        playwright = await async_playwright().start()
        launch_args = {"headless": headless}
        if proxy:
            launch_args["proxy"] = proxy

        launcher = {
            BrowserEngine.CHROMIUM: playwright.chromium,
            BrowserEngine.FIREFOX: playwright.firefox,
            BrowserEngine.WEBKIT: playwright.webkit,
        }[self.engine]

        browser = await launcher.launch(**launch_args)
        return browser, {"ignore_https_errors": self.ignore_https_errors}, playwright


import asyncio
import pytest

from standard_open_inflation_package import BaseAPI
from standard_open_inflation_package.browser_engines import (
    BrowserEngine,
    BaseBrowserConfig,
    CamoufoxConfig,
    PlaywrightConfig,
)

class DummyBrowser:
    def __init__(self):
        self.context_kwargs = None
    async def new_context(self, **kwargs):
        self.context_kwargs = kwargs
        return f"context:{kwargs}"

class DummyConfig(BaseBrowserConfig):
    async def initialize(self, proxy):
        return DummyBrowser(), {"foo": "bar"}, None

@pytest.mark.asyncio
@pytest.mark.parametrize("cfg", [
    DummyConfig(),
])
async def test_engine_selection(cfg):
    api = BaseAPI(browser_engine=cfg)
    await api.new_session()
    assert isinstance(api._browser, DummyBrowser)
    assert api._bcontext == "context:{'foo': 'bar'}"
    await api.close()


@pytest.mark.asyncio
async def test_default_engine_config():
    assert isinstance(BrowserEngine.CAMOUFOX(), CamoufoxConfig)
    for e in (BrowserEngine.CHROMIUM, BrowserEngine.FIREFOX, BrowserEngine.WEBKIT):
        assert isinstance(e(), PlaywrightConfig)


@pytest.mark.asyncio
async def test_default_engine_is_firefox():
    api = BaseAPI()
    assert isinstance(api.engine_config, PlaywrightConfig)
    assert api.engine_config.engine == BrowserEngine.FIREFOX


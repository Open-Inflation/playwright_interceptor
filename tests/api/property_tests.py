import pytest
from . import api_page_session, DEFAULT_TIMEOUT


@pytest.mark.asyncio
async def test_playwright_properties():
    async with api_page_session(timeout=DEFAULT_TIMEOUT) as (api, page):
        assert api.playwright_browser is not None
        assert api.playwright_context is not None
        assert page.playwright_page is not None

        await page.direct_fetch("https://example.com", wait_selector="body")
        assert page.playwright_page.url.startswith("https://")


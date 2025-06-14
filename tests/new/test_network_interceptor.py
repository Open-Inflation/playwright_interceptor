import asyncio
import pytest
from playwright.async_api import async_playwright
from standard_open_inflation_package import NetworkInterceptor, Handler, Execute

@pytest.mark.asyncio
@pytest.mark.xfail(reason="Network interception may not work in sandbox")
async def test_interceptor_basic():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch()
        context = await browser.new_context()
        page = await context.new_page()
        await page.goto("data:text/html,<html></html>")
        interceptor = NetworkInterceptor(page)
        task = asyncio.create_task(interceptor.execute(Handler.ALL(execute=Execute.RETURN(1)), timeout=5.0))
        await page.evaluate("fetch('data:text/plain,hello')")
        results = await task
        assert len(results) == 1
        assert len(results[0].responses) == 1
        await browser.close()

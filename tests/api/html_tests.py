import pytest
from standard_open_inflation_package import BaseAPI, Handler, Response
from standard_open_inflation_package.exceptions import NetworkError


CHECK_HTML = "https://httpbin.org"


@pytest.mark.asyncio
async def test_html_new_direct_getter():
    api = BaseAPI()
    await api.new_session()
    
    result = await api.new_direct_fetch(CHECK_HTML, handler=Handler.MAIN())
    await check_html(result)

    await api.close()

@pytest.mark.asyncio
async def test_html_page_direct_getter():
    api = BaseAPI()
    await api.new_session()

    page = await api.new_page()
    result = await page.direct_fetch(
        url=CHECK_HTML,
        handler=Handler.MAIN(),
    )
    await check_html(result)

    await page.close()

@pytest.mark.asyncio
async def test_html_inject_getter():
    api = BaseAPI()
    await api.new_session()

    page = await api.new_page()
    result = await page.inject_fetch(CHECK_HTML)
    await check_html(result)

    await page.close()


async def check_html(result: Response | NetworkError):
    assert isinstance(result, Response), "Result should be an instance of Response"
    assert result.status == 200, f"Expected status 200, got {result.status}"
    assert isinstance(result.response, str), "Response should be a string"
    assert result.response.startswith("<!DOCTYPE html>"), "Response should start with HTML doctype"

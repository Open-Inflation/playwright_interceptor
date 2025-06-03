import pytest
from standard_open_inflation_package.handler import Handler

# Импортируем утилиты для тестирования
from . import (
    run_direct_fetch_test, 
    run_page_direct_fetch_test,
    run_inject_fetch_test,
    assert_html_content,
    DEFAULT_URLS
)

CHECK_HTML = DEFAULT_URLS['html']


@pytest.mark.asyncio
async def test_html_new_direct_getter():
    await run_direct_fetch_test(
        CHECK_HTML, 
        Handler.MAIN(),
        expected_type=str,
        additional_checks=assert_html_content
    )

@pytest.mark.asyncio
async def test_html_page_direct_getter():
    await run_page_direct_fetch_test(
        CHECK_HTML,
        Handler.MAIN(),
        expected_type=str,
        additional_checks=assert_html_content
    )

@pytest.mark.asyncio
async def test_html_inject_getter():
    await run_inject_fetch_test(
        CHECK_HTML,
        expected_type=str,
        additional_checks=assert_html_content
    )

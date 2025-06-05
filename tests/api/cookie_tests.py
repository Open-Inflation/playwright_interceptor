"""
Тесты для системы управления cookies
"""
import pytest
import logging
from . import api_session, api_page_session, DEFAULT_TIMEOUT
from standard_open_inflation_package import Cookie


@pytest.mark.asyncio
async def test_cookie_removal():
    """Тест удаления cookies"""
    async with api_page_session(timeout=DEFAULT_TIMEOUT, debug=False) as (api, page):
        await page.direct_fetch("https://example.com", wait_selector="body")
        # Добавляем несколько cookies
        cookies_to_add = {
            "cookie1": "value1",
            "cookie2": "value2", 
            "cookie3": "value3"
        }
        await page.add_cookies(cookies_to_add)

        # Проверяем, что cookies добавлены
        cookies_after_add = await page.get_cookies()
        cookie_names = [c.name for c in cookies_after_add]
        assert "cookie1" in cookie_names, "cookie1 должен быть добавлен"
        assert "cookie2" in cookie_names, "cookie2 должен быть добавлен"
        assert "cookie3" in cookie_names, "cookie3 должен быть добавлен"
        
        # Удаляем один cookie по имени
        await api.remove_cookies("cookie1")

        cookies_after_remove_one = await api.get_cookies()
        cookie_names_after_remove = [c.name for c in cookies_after_remove_one]
        assert "cookie1" not in cookie_names_after_remove, "cookie1 должен быть удален"
        assert "cookie2" in cookie_names_after_remove, "cookie2 должен остаться"
        assert "cookie3" in cookie_names_after_remove, "cookie3 должен остаться"
        
        # Удаляем несколько cookies списком
        await api.remove_cookies(["cookie2", "cookie3"])

        cookies_after_remove_multiple = await api.get_cookies()
        cookie_names_final = [c.name for c in cookies_after_remove_multiple]
        assert "cookie2" not in cookie_names_final, "cookie2 должен быть удален"
        assert "cookie3" not in cookie_names_final, "cookie3 должен быть удален"


@pytest.mark.asyncio 
async def test_cookie_types_handling():
    """Тест обработки различных типов входных данных для cookies"""
    async with api_page_session(timeout=DEFAULT_TIMEOUT, debug=False) as (api, page):
        await page.direct_fetch("https://example.com", wait_selector="body")
        # Тест простого словаря
        simple_dict = {"simple": "value"}
        await page.add_cookies(simple_dict)

        # Тест списка словарей
        dict_list = {"dict1": "value1", "dict2": "value2"}
        await page.add_cookies(dict_list)

        # Тест одиночного Cookie объекта
        single_cookie = Cookie(name="singleCookie", value="single_value", domain=page.domain)
        await page.add_cookies(single_cookie)

        # Тест одиночного Cookie объекта
        list_cookie = [Cookie(name="listCookie1", value="list_value1", domain=page.domain), Cookie(name="listCookie2", value="list_value2", domain=page.domain)]
        await page.add_cookies(list_cookie)

        # Тест списка Cookie объектов
        cookie_list = [
            Cookie(name="list1", value="list_value1", domain=page.domain),
            Cookie(name="list2", value="list_value2", domain=page.domain)
        ]
        await page.add_cookies(cookie_list)

        # Проверяем, что все cookies добавлены
        all_cookies = await page.get_cookies()
        cookie_names = [c.name for c in all_cookies]

        expected_names = ["simple", "dict1", "dict2", "singleCookie", "listCookie1", "listCookie2", "list1", "list2"]
        for expected_name in expected_names:
            assert expected_name in cookie_names, f"Cookie '{expected_name}' должен быть найден"


@pytest.mark.asyncio
async def test_cookie_object_functionality():
    """Тест функциональности объекта Cookie"""
    # Тест создания Cookie через конструктор
    cookie1 = Cookie(name="test", value="value", domain="example.com", path="/")
    assert cookie1.name == "test"
    assert cookie1.value == "value"
    assert cookie1.domain == "example.com"
    assert cookie1.path == "/"
    
    # Тест конвертации в Playwright формат
    playwright_dict = cookie1.to_playwright_dict()
    assert playwright_dict["name"] == "test"
    assert playwright_dict["value"] == "value"
    assert playwright_dict["domain"] == "example.com"
    assert playwright_dict["path"] == "/"
    
    # Тест создания Cookie из Playwright данных
    playwright_data = {
        "name": "playwright_cookie",
        "value": "playwright_value",
        "domain": "test.com",
        "path": "/api",
        "secure": True,
        "httpOnly": False
    }
    
    cookie2 = Cookie.from_playwright_dict(playwright_data)
    assert cookie2.name == "playwright_cookie"
    assert cookie2.value == "playwright_value"
    assert cookie2.domain == "test.com"
    assert cookie2.path == "/api"
    assert cookie2.secure == True
    assert cookie2.http_only == False
    
    # Тест строкового представления
    cookie_str = str(cookie2)
    assert "playwright_cookie" in cookie_str
    assert "playwright_value" in cookie_str
    assert "test.com" in cookie_str


@pytest.mark.asyncio
async def test_get_cookies():
    async with api_page_session(timeout=DEFAULT_TIMEOUT, debug=False) as (api, page):
        await page.direct_fetch("https://example.com", wait_selector="body")
        # Добавляем несколько cookies
        await page.add_cookies({"cookie1": "value1", "cookie2": "value2"})
        await api.add_cookies(Cookie(name="outer_cookie", value="outer_value", domain="outersite.com"))
        
        # Получаем cookies
        cookies = await page.get_cookies()
        assert isinstance(cookies, list), "get_cookies должен возвращать список"
        assert len(cookies) == 2, "Должно быть ровно 2 cookie"

        all_cookies = await api.get_cookies()
        assert isinstance(all_cookies, list), "get_cookies должен возвращать список"
        assert len(all_cookies) == 3, "Должно быть ровно 3 cookie"

        cookie_names = [cookie.name for cookie in all_cookies]
        assert "cookie1" in cookie_names, "cookie1 должен быть в списке"
        assert "cookie2" in cookie_names, "cookie2 должен быть в списке"
        assert "outer_cookie" in cookie_names, "outer_cookie должен быть в списке"

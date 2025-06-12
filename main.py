from standard_open_inflation_package import BaseAPI, Request, Response, HttpMethod, Page
from standard_open_inflation_package.exceptions import NetworkError
from standard_open_inflation_package import config as CFG
from standard_open_inflation_package.handler import Handler, ExpectedContentType, HandlerSearchSuccess, HandlerSearchFailed
from standard_open_inflation_package.browser_engines import BrowserEngine
from pprint import pprint
import time
from io import BytesIO

class Sample:
    def __init__(self):
        self.API = BaseAPI(
            timeout=60.0,
            start_func=self.start_func,
            request_modifier_func=self.modify_request,
            browser_engine=BrowserEngine.CHROMIUM(headless=False),
        )
        self.API._logger.setLevel("DEBUG")
        self.base_page: Page | None = None
    
    async def modify_request(self, request: Request) -> Request:
        """
        Модифицирует объект Request перед каждым inject_fetch запросом.
        """
        pprint(f"Modifying request: {request.url}, method={request.method}, headers={request.headers}, params={request.params}")

        return request
    
    async def start_func(self, api: BaseAPI):
        print("Starting the API...")
        self.base_page = await api.new_page()
        resp = await self.base_page.direct_fetch(
            url="https://5ka.ru/catalog/",
            wait_selector=".chakra-stack"
        )
        return resp
        
    async def __aenter__(self):
        await self.API.new_session(include_browser=True)
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        print(f"__aexit__ called with exc_type={exc_type}, exc_val={exc_val}")
        if exc_type:
            print(f"Exception occurred: {exc_val}")
        await self.API.close()

    async def get_page(self):
        return await self.base_page.direct_fetch(
            url="https://5ka.ru/product/produkt-rassolnyy-sirtaki-original-dlya-grecheskog--3483307/",
            wait_selector=".priceContainer_productCent__J1bRL",
            handlers=Handler.SIDE(expected_content=ExpectedContentType.IMAGE, max_responses=1)
        )

    async def get_categories(self):
        # Можем использовать старый способ - передать URL как строку
        resp = await self.base_page.direct_fetch(
            url="https://5ka.ru/catalog/okroshka--251C38644/",
            wait_selector=".chakra-heading.css-1y7neaf",
            handlers=Handler.SIDE(
                expected_content=ExpectedContentType.JSON,
                startswith_url="https://5d.5ka.ru/api/catalog/v2/stores/", #todo поддержка регулярных выражений
            )
        )
        return resp
    



async def main():
    async with Sample() as sample:
        try:
            product_page = await sample.get_page()
            assert isinstance(product_page[0], HandlerSearchSuccess)
            assert isinstance(product_page[0].responses, Response)
            assert isinstance(product_page[0].responses.response, BytesIO)
        except Exception as e:
            print(f"Error fetching product page: {e}")
        
        try:
            categories = await sample.get_categories()
            assert isinstance(categories[0], HandlerSearchSuccess)
            assert isinstance(categories[0].responses, Response)
            assert isinstance(categories[0].responses.response, dict)
        except Exception as e:
            print(f"Error fetching categories: {e}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
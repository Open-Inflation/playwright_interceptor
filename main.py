from playwright.async_api import async_playwright
from standard_open_inflation_package import NetworkInterceptor, Handler, Execute, Request, Response
import asyncio

async def main():
    async with async_playwright() as pw:
        browser = await pw.firefox.launch()  # Используем firefox, так как он у вас работает
        page = await browser.new_page()

        interceptor = NetworkInterceptor(page)
        interceptor._logger.setLevel("DEBUG")
        
        # Запускаем перехватчик и навигацию одновременно
        # asyncio.gather() запустит обе задачи параллельно
        results, _ = await asyncio.gather(
            interceptor.execute(Handler.ALL(execute=Execute.ALL(
                request_modify=request_modifier,
                response_modify=response_modifier,
                max_modifications=4,
                max_responses=2
            ))),
            page.goto("https://httpbin.org/")
        )

        print("Results:", results)
        await browser.close()

def request_modifier(request: Request) -> Request:
    """Модифицирует запрос перед отправкой на сервер"""
    print(f"Modifying request: {request.method.value} {request.url}")
    
    # Добавляем заголовок
    request.add_header("X-Modified-By", "NetworkInterceptor")
    
    # Добавляем параметр
    request.add_param("intercepted", "true")
    
    print(f"Modified request URL: {request.real_url}")
    return request

def response_modifier(response: Response) -> Response:
    """Модифицирует ответ после получения от сервера"""
    print(f"Modifying response: {response.status} from {response.url}")
    
    # Можем модифицировать заголовки ответа
    response.response_headers["X-Response-Modified"] = "true"
    
    return response

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
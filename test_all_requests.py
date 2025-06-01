#!/usr/bin/env python3
"""
Тест для проверки захвата ВСЕХ HTTP-запросов
Проверяем, может ли система обработать большое количество запросов
"""

import asyncio
import time
from standard_open_inflation_package import BaseAPI, Handler, Response, HandlerSearchFailedError
from io import BytesIO


async def main():
    """Тестируем захват ВСЕХ запросов на сложной странице"""
    api = BaseAPI(timeout=10.0)  # Увеличиваем timeout для сложных страниц
    await api.new_session()
    
    print("🚀 Тестируем захват ВСЕХ запросов на РЕАЛЬНО сложной странице...")
    
    # Используем Handler.ANY() для захвата ЛЮБОГО первого запроса
    # Это покажет, работает ли система при множественных запросах
    start_time = time.time()
    
    # YouTube главная - около 70+ запросов!
    complex_url = "https://chromedevtools.github.io/devtools-protocol/"
    
    result = await api.new_direct_fetch(complex_url, handler=Handler.TEXT())

    if isinstance(result, HandlerSearchFailedError):
        for i in result.rejected_responses:
            typpe = type(i.response)
            size = len(str(i.response)) if isinstance(i.response, (str, bytes, dict, list)) else 0
            if typpe is BytesIO:
                size = i.response.getbuffer().nbytes if hasattr(i.response, 'getbuffer') else 0
            type_name = typpe.__name__
            content_type = i.response_headers.get('content-type', 'unknown')
            print(f"{i.duration:6.1f}s | {i.status:3} | {content_type[:30]:<30} | Size: {size:<8} | {type_name:<15}")
    else:
        print(f"Response: {result.response}...")


if __name__ == "__main__":
    asyncio.run(main())

"""
Расширенная демонстрация новой функциональности request_modify и response_modify
"""
from playwright.async_api import async_playwright
from standard_open_inflation_package import NetworkInterceptor, Handler, Execute, Request, Response
import asyncio
import json

# Глобальные счетчики для демонстрации
request_counter = 0
response_counter = 0


def auth_request_modifier(request: Request) -> Request:
    """Добавляет аутентификацию к запросам"""
    global request_counter
    request_counter += 1
    
    print(f"🔐 [AUTH] Модификация запроса #{request_counter}: {request.method.value} {request.url}")
    
    # Добавляем заголовок авторизации
    request.add_header("Authorization", "Bearer demo-token-123")
    request.add_header("X-Request-ID", f"req-{request_counter}")
    
    print(f"   ✅ Добавлены заголовки авторизации")
    return request


def tracking_request_modifier(request: Request) -> Request:
    """Добавляет трекинг к запросам"""
    print(f"📊 [TRACKING] Дополнительная модификация запроса: {request.url}")
    
    # Добавляем параметры трекинга
    request.add_param("utm_source", "interceptor")
    request.add_param("session_id", "demo-session-456")
    
    print(f"   ✅ Добавлены параметры трекинга")
    print(f"   🔗 Итоговый URL: {request.real_url}")
    return request


def security_response_modifier(response: Response) -> Response:
    """Добавляет заголовки безопасности к ответам"""
    global response_counter
    response_counter += 1
    
    print(f"🛡️ [SECURITY] Модификация ответа #{response_counter}: {response.status} от {response.url}")
    
    # Добавляем заголовки безопасности
    security_headers = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "X-Response-Modified": "true",
        "X-Modification-Count": str(response_counter)
    }
    
    response.response_headers.update(security_headers)
    print(f"   ✅ Добавлены {len(security_headers)} заголовков безопасности")
    return response


async def analytics_response_modifier(response: Response) -> Response:
    """Асинхронно обрабатывает ответы для аналитики"""
    print(f"📈 [ANALYTICS] Асинхронная обработка ответа: {response.url}")
    
    # Имитируем асинхронную операцию (например, отправка метрик)
    await asyncio.sleep(0.01)
    
    # Добавляем информацию об аналитике
    response.response_headers["X-Analytics-Processed"] = "true"
    response.response_headers["X-Processing-Time"] = "0.01s"
    
    print(f"   ✅ Аналитика обработана асинхронно")
    return response


async def demo_multiple_handlers():
    """Демонстрация работы с несколькими хендлерами"""
    print("🚀 Запуск демонстрации множественных хендлеров\n")
    
    async with async_playwright() as pw:
        browser = await pw.firefox.launch(headless=True)
        page = await browser.new_page()
        
        interceptor = NetworkInterceptor(page)
        interceptor._logger.setLevel("WARNING")  # Уменьшаем логирование для чистоты вывода
        
        # Создаем несколько хендлеров с разными ролями
        
        # 1. Хендлер аутентификации - модифицирует только запросы
        auth_handler = Handler.ALL(
            slug="auth_handler",
            execute=Execute.ALL(
                request_modify=auth_request_modifier,
                max_modifications=3,
                max_responses=1
            )
        )
        
        # 2. Хендлер трекинга - модифицирует запросы и захватывает ответы  
        tracking_handler = Handler.ALL(
            slug="tracking_handler",
            execute=Execute.ALL(
                request_modify=tracking_request_modifier,
                max_modifications=3,
                max_responses=1
            )
        )
        
        # 3. Хендлер безопасности - модифицирует только ответы
        security_handler = Handler.ALL(
            slug="security_handler", 
            execute=Execute.ALL(
                response_modify=security_response_modifier,
                max_modifications=3,
                max_responses=1
            )
        )
        
        # 4. Хендлер аналитики - асинхронно обрабатывает ответы
        analytics_handler = Handler.ALL(
            slug="analytics_handler",
            execute=Execute.ALL(
                response_modify=analytics_response_modifier,
                max_modifications=3,
                max_responses=1
            )
        )
        
        print("📋 Настроенные хендлеры:")
        print("   🔐 auth_handler - добавляет авторизацию к запросам")
        print("   📊 tracking_handler - добавляет трекинг к запросам")
        print("   🛡️ security_handler - добавляет заголовки безопасности к ответам")
        print("   📈 analytics_handler - асинхронно обрабатывает ответы")
        print()
        
        # Запускаем перехватчик с множественными хендлерами
        print("🌐 Переходим на https://httpbin.org/get")
        print("=" * 60)
        
        results, _ = await asyncio.gather(
            interceptor.execute([auth_handler, tracking_handler, security_handler, analytics_handler]),
            page.goto("https://httpbin.org/get")
        )
        
        await browser.close()
        
        print("=" * 60)
        print("📊 Результаты выполнения:")
        print(f"   📥 Обработано запросов: {request_counter}")
        print(f"   📤 Обработано ответов: {response_counter}")
        print(f"   🎯 Активных хендлеров: {len(results)}")
        print()
        
        for i, result in enumerate(results, 1):
            if hasattr(result, 'responses'):
                print(f"   ✅ Хендлер {i} ({result.handler_slug}): {len(result.responses)} ответов за {result.duration:.2f}с")
            else:
                print(f"   ❌ Хендлер {i} ({result.handler_slug}): ошибка за {result.duration:.2f}с")
        
        print("\n🎉 Демонстрация завершена успешно!")


async def demo_simple_modification():
    """Простая демонстрация базовой модификации"""
    print("\n" + "=" * 60)
    print("🔧 Простая демонстрация модификации запроса и ответа")
    print("=" * 60)
    
    def simple_request_mod(request: Request) -> Request:
        print(f"📝 Простая модификация запроса: добавляем параметр 'demo=true'")
        request.add_param("demo", "true")
        return request
    
    def simple_response_mod(response: Response) -> Response:
        print(f"📝 Простая модификация ответа: добавляем заголовок 'X-Demo=true'")
        response.response_headers["X-Demo"] = "true"
        return response
    
    async with async_playwright() as pw:
        browser = await pw.firefox.launch(headless=True)
        page = await browser.new_page()
        
        interceptor = NetworkInterceptor(page)
        interceptor._logger.setLevel("ERROR")
        
        simple_handler = Handler.ALL(execute=Execute.ALL(
            request_modify=simple_request_mod,
            response_modify=simple_response_mod,
            max_modifications=1,
            max_responses=1
        ))
        
        results, _ = await asyncio.gather(
            interceptor.execute(simple_handler),
            page.goto("https://httpbin.org/get")
        )
        
        await browser.close()
        
        print(f"✅ Простая демонстрация завершена: {len(results)} результат(ов)")


async def main():
    """Главная функция демонстрации"""
    print("🎭 Демонстрация новой функциональности NetworkInterceptor")
    print("=" * 60)
    
    # Сначала простая демонстрация
    await demo_simple_modification()
    
    # Затем сложная с множественными хендлерами
    await demo_multiple_handlers()
    
    print("\n🏁 Все демонстрации завершены!")
    print("\n💡 Ключевые особенности:")
    print("   • Запросы модифицируются ПЕРЕД отправкой на сервер")
    print("   • Ответы модифицируются ПОСЛЕ получения от сервера")
    print("   • Модифицированные ответы попадают в браузер")
    print("   • Несколько хендлеров применяются последовательно")
    print("   • Поддерживаются как синхронные, так и асинхронные модификации")


if __name__ == "__main__":
    asyncio.run(main())

#!/usr/bin/env python3
"""
Тест для проверки того, что модифицированный response действительно передается в браузер
"""
import asyncio
from playwright.async_api import async_playwright
from standard_open_inflation_package import NetworkInterceptor, Handler, Execute, Request, Response

async def test_response_reaches_browser():
    """Тест, который проверяет что модифицированный response действительно достигает браузера"""
    
    def response_modifier(response: Response) -> Response:
        """Модифицирует JSON ответ - добавляет специальные поля"""
        print(f"🔧 MODIFYING RESPONSE from {response.url}")
        
        # Парсим содержимое для работы с ним
        parsed_content = response.content_parse()
        
        # Если это JSON ответ, добавляем специальные поля
        if isinstance(parsed_content, dict):
            parsed_content['INTERCEPTED'] = True
            parsed_content['MODIFICATION_MARKER'] = 'THIS_PROVES_MODIFICATION_WORKS'
            parsed_content['INJECTED_DATA'] = {
                'test_value': 12345,
                'proof': 'Response modification reached browser'
            }
            print(f"   ✅ Added INTERCEPTED=True and MODIFICATION_MARKER to JSON response")
            
            # Обновляем content с модифицированными данными
            import json
            response.content = json.dumps(parsed_content).encode('utf-8')
        
        # Добавляем заголовки
        response.response_headers['X-Intercepted'] = 'true'
        response.response_headers['X-Modification-Proof'] = 'MODIFIED_BY_INTERCEPTOR'
        
        return response

    async with async_playwright() as pw:
        browser = await pw.firefox.launch(headless=False)  # Видимый браузер для наблюдения
        page = await browser.new_page()
        
        interceptor = NetworkInterceptor(page)
        
        # Создаем хендлер только с response_modify
        handler = Handler.ALL(
            slug="response_tester",
            execute=Execute.ALL(
                response_modify=response_modifier,
                max_modifications=5,
                max_responses=1
            )
        )
        
        print("🚀 Запускаем тест модификации ответов...")
        print("🌐 Переходим на httpbin.org/get для получения JSON ответа")
        
        # Запускаем перехватчик и навигацию
        results, _ = await asyncio.gather(
            interceptor.execute(handler),
            page.goto("https://httpbin.org/get")
        )
        
        print(f"\n📊 Handler завершился, результатов: {len(results)}")
        
        # Теперь проверяем что видит браузер/JavaScript
        print("\n🔍 ПРОВЕРЯЕМ ЧТО ВИДИТ БРАУЗЕР:")
        
        # Получаем содержимое страницы, которое видит браузер
        page_content = await page.content()
        
        # Проверяем наличие наших модификаций в HTML странице
        if 'INTERCEPTED' in page_content:
            print("   ✅ INTERCEPTED найден в HTML - модификация дошла до браузера!")
        else:
            print("   ❌ INTERCEPTED НЕ найден в HTML - модификация НЕ дошла")
            
        if 'MODIFICATION_MARKER' in page_content:
            print("   ✅ MODIFICATION_MARKER найден в HTML - модификация дошла!")
        else:
            print("   ❌ MODIFICATION_MARKER НЕ найден в HTML - модификация НЕ дошла")
            
        if 'THIS_PROVES_MODIFICATION_WORKS' in page_content:
            print("   ✅ Маркер доказательства найден - модификация дошла!")
        else:
            print("   ❌ Маркер доказательства НЕ найден - модификация НЕ дошла")
        
        # Выполняем JavaScript для доступа к JSON данным
        try:
            js_result = await page.evaluate("""
                () => {
                    // Ищем JSON данные на странице
                    const preElements = document.querySelectorAll('pre');
                    for (let pre of preElements) {
                        try {
                            const data = JSON.parse(pre.textContent);
                            return {
                                found_intercepted: 'INTERCEPTED' in data,
                                found_marker: 'MODIFICATION_MARKER' in data,
                                intercepted_value: data.INTERCEPTED,
                                marker_value: data.MODIFICATION_MARKER,
                                injected_data: data.INJECTED_DATA || null,
                                full_json: data
                            };
                        } catch (e) {
                            continue;
                        }
                    }
                    return { error: 'JSON not found' };
                }
            """)
            
            print(f"\n🔍 JAVASCRIPT АНАЛИЗ:")
            if 'error' in js_result:
                print(f"   ❌ Ошибка: {js_result['error']}")
            else:
                print(f"   INTERCEPTED найден: {js_result.get('found_intercepted', False)}")
                print(f"   MODIFICATION_MARKER найден: {js_result.get('found_marker', False)}")
                print(f"   Значение INTERCEPTED: {js_result.get('intercepted_value')}")
                print(f"   Значение MARKER: {js_result.get('marker_value')}")
                print(f"   Injected data: {js_result.get('injected_data')}")
                
                # Проверяем конкретные значения
                if js_result.get('found_intercepted') and js_result.get('intercepted_value') == True:
                    print("   ✅ ДОКАЗАТЕЛЬСТВО: Поле INTERCEPTED=True найдено через JavaScript!")
                    
                if js_result.get('found_marker') and js_result.get('marker_value') == 'THIS_PROVES_MODIFICATION_WORKS':
                    print("   ✅ ДОКАЗАТЕЛЬСТВО: Маркер модификации найден через JavaScript!")
                    
                if js_result.get('injected_data') and js_result['injected_data'].get('test_value') == 12345:
                    print("   ✅ ДОКАЗАТЕЛЬСТВО: Injected data найдена через JavaScript!")
                    
        except Exception as e:
            print(f"   ❌ JavaScript ошибка: {e}")
        
        # Проверяем заголовки ответа
        print(f"\n🔍 ПРОВЕРКА ЗАГОЛОВКОВ:")
        try:
            # Выполняем запрос через JavaScript для проверки заголовков
            headers_result = await page.evaluate("""
                async () => {
                    try {
                        const response = await fetch('/get');
                        const headers = {};
                        for (let [key, value] of response.headers) {
                            headers[key] = value;
                        }
                        return headers;
                    } catch (e) {
                        return { error: e.message };
                    }
                }
            """)
            
            if 'x-intercepted' in headers_result:
                print(f"   ✅ X-Intercepted заголовок найден: {headers_result['x-intercepted']}")
            else:
                print(f"   ❌ X-Intercepted заголовок НЕ найден")
                
            if 'x-modification-proof' in headers_result:
                print(f"   ✅ X-Modification-Proof заголовок найден: {headers_result['x-modification-proof']}")
            else:
                print(f"   ❌ X-Modification-Proof заголовок НЕ найден")
                
        except Exception as e:
            print(f"   ❌ Ошибка проверки заголовков: {e}")
        
        # Ждем немного для наблюдения
        print(f"\n⏱️  Ждем 3 секунды для визуального осмотра...")
        await asyncio.sleep(3)
        
        await browser.close()
        
        print(f"\n📋 ИТОГОВАЯ ПРОВЕРКА:")
        
        # Итоговые assert'ы для подтверждения
        assert 'INTERCEPTED' in page_content, "Модификация НЕ достигла браузера - INTERCEPTED не найден в HTML"
        assert 'MODIFICATION_MARKER' in page_content, "Модификация НЕ достигла браузера - MODIFICATION_MARKER не найден в HTML"
        assert 'THIS_PROVES_MODIFICATION_WORKS' in page_content, "Маркер доказательства НЕ найден в HTML"
        
        print("✅ ВСЕ ПРОВЕРКИ ПРОШЛИ!")
        print("✅ ДОКАЗАНО: Модифицированный response действительно передается в браузер!")
        print("✅ JavaScript может видеть наши модификации!")
        print("✅ HTML содержит модифицированные данные!")

if __name__ == "__main__":
    asyncio.run(test_response_reaches_browser())

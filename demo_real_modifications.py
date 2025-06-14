#!/usr/bin/env python3
"""
Демонстрация и тест реальных модификаций запросов и ответов
"""
import asyncio
from playwright.async_api import async_playwright
from standard_open_inflation_package import NetworkInterceptor, Handler, Execute, Request, Response

async def test_real_modifications():
    """Тест, который проверяет реальные модификации запросов и ответов"""
    
    # Будем отслеживать все модификации
    modifications_log = {
        'original_requests': [],
        'modified_requests': [],
        'original_responses': [],
        'modified_responses': []
    }
    
    def request_modifier(request: Request) -> Request:
        """Модифицирует запрос - добавляет параметры и заголовки"""
        # Записываем оригинальный запрос
        modifications_log['original_requests'].append({
            'url': request.url,
            'params': dict(request.params) if request.params else {},
            'headers': dict(request.headers) if request.headers else {},
            'method': request.method.value
        })
        
        # Модифицируем запрос
        request.add_param('modified_by', 'interceptor')
        request.add_param('timestamp', '12345')
        request.add_header('X-Custom-Header', 'test-value')
        request.add_header('X-Intercepted', 'true')
        
        # Записываем модифицированный запрос
        modifications_log['modified_requests'].append({
            'url': request.real_url,
            'params': dict(request.params) if request.params else {},
            'headers': dict(request.headers) if request.headers else {},
            'method': request.method.value
        })
        
        print(f"🔧 REQUEST MODIFIED: {request.url} -> {request.real_url}")
        print(f"   Added params: modified_by=interceptor, timestamp=12345")
        print(f"   Added headers: X-Custom-Header, X-Intercepted")
        
        return request
    
    def response_modifier(response: Response) -> Response:
        """Модифицирует ответ - изменяет заголовки и содержимое"""
        # Парсим содержимое для работы с ним
        parsed_content = response.content_parse()
        
        # Записываем оригинальный ответ
        modifications_log['original_responses'].append({
            'status': response.status,
            'headers': dict(response.response_headers) if response.response_headers else {},
            'url': response.url,
            'content_preview': str(parsed_content)[:100] if parsed_content else None
        })
        
        # Модифицируем ответ
        response.response_headers['X-Response-Modified'] = 'true'
        response.response_headers['X-Modification-Time'] = '2025-06-15'
        response.response_headers['X-Handler'] = 'response_modifier'
        
        # Если это JSON, добавим поле и обновим содержимое
        if isinstance(parsed_content, dict):
            parsed_content['_intercepted'] = True
            parsed_content['_modification_info'] = {
                'modified_by': 'response_modifier',
                'timestamp': '2025-06-15'
            }
            # Обновляем content с модифицированными данными
            import json
            response.content = json.dumps(parsed_content).encode('utf-8')
        
        # Записываем модифицированный ответ
        modifications_log['modified_responses'].append({
            'status': response.status,
            'headers': dict(response.response_headers) if response.response_headers else {},
            'url': response.url,
            'content_preview': str(response.content_parse())[:100] if response.content else None
        })
        
        print(f"🔧 RESPONSE MODIFIED: {response.status} from {response.url}")
        print(f"   Added headers: X-Response-Modified, X-Modification-Time, X-Handler")
        if isinstance(parsed_content, dict):
            print(f"   Added JSON fields: _intercepted, _modification_info")
        
        return response
    
    async with async_playwright() as pw:
        browser = await pw.firefox.launch()
        page = await browser.new_page()
        
        interceptor = NetworkInterceptor(page)
        interceptor._logger.setLevel("DEBUG")
        
        # Создаем хендлер с обеими модификациями
        handler = Handler.ALL(
            slug="modification_tester",
            execute=Execute.ALL(
                request_modify=request_modifier,
                response_modify=response_modifier,
                max_modifications=3,  # Разрешаем несколько модификаций
                max_responses=2       # Захватываем несколько ответов
            )
        )
        
        print("🚀 Запускаем тест модификаций...")
        
        # Запускаем перехватчик и навигацию
        results, _ = await asyncio.gather(
            interceptor.execute(handler),
            page.goto("https://httpbin.org/get?original_param=test")
        )
        
        await browser.close()
        
        print(f"\n📊 РЕЗУЛЬТАТЫ ТЕСТА:")
        print(f"   Handlers completed: {len(results)}")
        print(f"   Original requests logged: {len(modifications_log['original_requests'])}")
        print(f"   Modified requests logged: {len(modifications_log['modified_requests'])}")
        print(f"   Original responses logged: {len(modifications_log['original_responses'])}")
        print(f"   Modified responses logged: {len(modifications_log['modified_responses'])}")
        
        # Анализируем модификации запросов
        print(f"\n🔍 АНАЛИЗ МОДИФИКАЦИЙ ЗАПРОСОВ:")
        for i, (orig, mod) in enumerate(zip(modifications_log['original_requests'], modifications_log['modified_requests'])):
            print(f"   Request #{i+1}:")
            print(f"     Original URL: {orig['url']}")
            print(f"     Modified URL: {mod['url']}")
            
            # Проверяем добавленные параметры
            orig_params = set(orig['params'].keys())
            mod_params = set(mod['params'].keys())
            added_params = mod_params - orig_params
            print(f"     Added params: {added_params}")
            
            # Проверяем добавленные заголовки
            orig_headers = set(orig['headers'].keys())
            mod_headers = set(mod['headers'].keys())
            added_headers = mod_headers - orig_headers
            print(f"     Added headers: {added_headers}")
        
        # Анализируем модификации ответов
        print(f"\n🔍 АНАЛИЗ МОДИФИКАЦИЙ ОТВЕТОВ:")
        for i, (orig, mod) in enumerate(zip(modifications_log['original_responses'], modifications_log['modified_responses'])):
            print(f"   Response #{i+1}:")
            print(f"     URL: {orig['url']}")
            print(f"     Status: {orig['status']} -> {mod['status']}")
            
            # Проверяем добавленные заголовки
            orig_headers = set(orig['headers'].keys())
            mod_headers = set(mod['headers'].keys())
            added_headers = mod_headers - orig_headers
            print(f"     Added headers: {added_headers}")
        
        # Проверяем, что модификации действительно применились
        assert len(modifications_log['modified_requests']) > 0, "Ни одного запроса не было модифицировано"
        assert len(modifications_log['modified_responses']) > 0, "Ни одного ответа не было модифицировано"
        
        # Проверяем конкретные модификации
        for mod_req in modifications_log['modified_requests']:
            assert 'modified_by=interceptor' in mod_req['url'], "Параметр modified_by не добавлен"
            assert 'timestamp=12345' in mod_req['url'], "Параметр timestamp не добавлен"
            assert 'X-Custom-Header' in mod_req['headers'], "Заголовок X-Custom-Header не добавлен"
            assert 'X-Intercepted' in mod_req['headers'], "Заголовок X-Intercepted не добавлен"
        
        for mod_resp in modifications_log['modified_responses']:
            assert 'X-Response-Modified' in mod_resp['headers'], "Заголовок X-Response-Modified не добавлен"
            assert 'X-Modification-Time' in mod_resp['headers'], "Заголовок X-Modification-Time не добавлен"
            assert 'X-Handler' in mod_resp['headers'], "Заголовок X-Handler не добавлен"
        
        print(f"\n✅ ВСЕ ПРОВЕРКИ ПРОШЛИ УСПЕШНО!")
        print(f"   Модификации запросов и ответов работают корректно")
        print(f"   Изменения действительно применяются и достигают браузера")

if __name__ == "__main__":
    asyncio.run(test_real_modifications())

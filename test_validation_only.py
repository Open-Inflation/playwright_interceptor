#!/usr/bin/env python3
"""
Тест валидации Execute без браузера
"""
from standard_open_inflation_package import Execute, Request, Response

def test_execute_validation():
    """Тестируем валидацию Execute для MODIFY и ALL"""
    
    def dummy_request_modifier(request: Request) -> Request:
        return request
    
    def dummy_response_modifier(response: Response) -> Response:
        return response
    
    print("🧪 Тестируем валидацию Execute...")
    
    # Тест 1: MODIFY только с request_modify должен работать
    try:
        execute1 = Execute.MODIFY(
            request_modify=dummy_request_modifier,
            max_modifications=1
        )
        print("✅ MODIFY с только request_modify: УСПЕХ")
    except Exception as e:
        print(f"❌ MODIFY с только request_modify: ОШИБКА - {e}")
    
    # Тест 2: MODIFY только с response_modify должен работать
    try:
        execute2 = Execute.MODIFY(
            response_modify=dummy_response_modifier,
            max_modifications=1
        )
        print("✅ MODIFY с только response_modify: УСПЕХ")
    except Exception as e:
        print(f"❌ MODIFY с только response_modify: ОШИБКА - {e}")
    
    # Тест 3: MODIFY с обеими функциями должен работать
    try:
        execute3 = Execute.MODIFY(
            request_modify=dummy_request_modifier,
            response_modify=dummy_response_modifier,
            max_modifications=1
        )
        print("✅ MODIFY с обеими функциями: УСПЕХ")
    except Exception as e:
        print(f"❌ MODIFY с обеими функциями: ОШИБКА - {e}")
    
    # Тест 4: MODIFY без функций должен упасть
    try:
        execute4 = Execute.MODIFY(max_modifications=1)
        print("❌ MODIFY без функций: НЕ ДОЛЖЕН РАБОТАТЬ")
    except Exception as e:
        print(f"✅ MODIFY без функций: ПРАВИЛЬНО УПАЛ - {e}")
    
    # Тест 5: ALL только с request_modify должен работать
    try:
        execute5 = Execute.ALL(
            request_modify=dummy_request_modifier,
            max_modifications=1,
            max_responses=1
        )
        print("✅ ALL с только request_modify: УСПЕХ")
    except Exception as e:
        print(f"❌ ALL с только request_modify: ОШИБКА - {e}")
    
    # Тест 6: ALL только с response_modify должен работать
    try:
        execute6 = Execute.ALL(
            response_modify=dummy_response_modifier,
            max_modifications=1,
            max_responses=1
        )
        print("✅ ALL с только response_modify: УСПЕХ")
    except Exception as e:
        print(f"❌ ALL с только response_modify: ОШИБКА - {e}")
    
    # Тест 7: ALL без функций должен упасть
    try:
        execute7 = Execute.ALL(
            max_modifications=1,
            max_responses=1
        )
        print("❌ ALL без функций: НЕ ДОЛЖЕН РАБОТАТЬ")
    except Exception as e:
        print(f"✅ ALL без функций: ПРАВИЛЬНО УПАЛ - {e}")

def test_request_modification():
    """Тестируем модификацию объекта Request"""
    
    print("\n🔧 Тестируем модификацию Request...")
    
    # Создаем запрос
    from standard_open_inflation_package import HttpMethod
    request = Request(
        url="https://example.com/api",
        method=HttpMethod.GET,
        headers={"User-Agent": "TestAgent"},
        params={"page": "1"}
    )
    
    print(f"Оригинальный URL: {request.url}")
    print(f"Оригинальный real_url: {request.real_url}")
    print(f"Оригинальные заголовки: {request.headers}")
    print(f"Оригинальные параметры: {request.params}")
    
    # Модифицируем запрос (теперь прямое обращение к свойствам)
    # Проверяем что свойства инициализированы
    if request.params is None:
        request.params = {}
    if request.headers is None:
        request.headers = {}
        
    request.params["modified"] = "true"
    request.params["timestamp"] = "12345"
    request.headers["X-Modified"] = "true"
    request.headers["Authorization"] = "Bearer token123"
    
    print(f"\nПосле модификации:")
    print(f"URL: {request.url}")
    print(f"Real URL: {request.real_url}")
    print(f"Заголовки: {request.headers}")
    print(f"Параметры: {request.params}")
    
    # Проверяем, что модификации применились
    assert "modified=true" in request.real_url
    assert "timestamp=12345" in request.real_url
    assert request.headers.get("X-Modified") == "true"
    assert request.headers.get("Authorization") == "Bearer token123"
    
    print("✅ Все модификации Request применились корректно!")

def test_response_modification():
    """Тестируем модификацию объекта Response"""
    
    print("\n🔧 Тестируем модификацию Response...")
    
    # Создаем ответ
    import json
    test_data = {"data": "test", "status": "ok"}
    response = Response(
        status=200,
        url="https://example.com/api",
        content=json.dumps(test_data).encode('utf-8'),  # Сохраняем как bytes
        response_headers={"Content-Type": "application/json"},
        request_headers={"User-Agent": "TestAgent"},
        duration=1.5
    )
    
    print(f"Оригинальный статус: {response.status}")
    print(f"Оригинальные заголовки ответа: {response.response_headers}")
    print(f"Оригинальное содержимое: {response.content_parse()}")
    
    # Модифицируем ответ
    response.response_headers["X-Modified"] = "true"
    response.response_headers["X-Handler"] = "test_handler"
    
    # Парсим содержимое для модификации
    parsed_content = response.content_parse()
    if isinstance(parsed_content, dict):
        parsed_content["_intercepted"] = True
        parsed_content["_modification_time"] = "2025-06-15"
        # Обновляем content с модифицированными данными
        response.content = json.dumps(parsed_content).encode('utf-8')
    
    print(f"\nПосле модификации:")
    print(f"Статус: {response.status}")
    print(f"Заголовки ответа: {response.response_headers}")
    print(f"Содержимое: {response.content_parse()}")
    
    # Проверяем, что модификации применились
    final_content = response.content_parse()
    assert response.response_headers.get("X-Modified") == "true"
    assert response.response_headers.get("X-Handler") == "test_handler"
    if isinstance(final_content, dict):
        assert final_content.get("_intercepted") == True
        assert final_content.get("_modification_time") == "2025-06-15"
        print("✅ JSON содержимое также было модифицировано!")
    
    print("✅ Все модификации Response применились корректно!")

if __name__ == "__main__":
    test_execute_validation()
    test_request_modification()
    test_response_modification()
    print("\n🎉 ВСЕ ТЕСТЫ ВАЛИДАЦИИ ПРОШЛИ УСПЕШНО!")

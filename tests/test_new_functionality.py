"""
Демонстрационный тест для новой функциональности request_modify и response_modify
"""
import pytest
from standard_open_inflation_package import Execute, Request, Response, HttpMethod, ExecuteAction


def test_execute_modify_with_request_and_response():
    """Тест Execute.MODIFY с обеими функциями: request_modify и response_modify"""
    
    def mock_request_modify(req: Request) -> Request:
        req.add_header("X-Test", "request-modified")
        return req
    
    def mock_response_modify(resp: Response) -> Response:
        resp.response_headers["X-Test"] = "response-modified"
        return resp
    
    # Создаем Execute с обеими функциями
    execute = Execute.MODIFY(
        request_modify=mock_request_modify,
        response_modify=mock_response_modify,
        max_modifications=1
    )
    
    assert execute.action.name == "MODIFY"
    assert execute.request_modify is not None
    assert execute.response_modify is not None
    assert execute.max_modifications == 1


def test_execute_all_with_request_and_response():
    """Тест Execute.ALL с обеими функциями: request_modify и response_modify"""
    
    def mock_request_modify(req: Request) -> Request:
        req.add_param("modified", "true")
        return req
    
    def mock_response_modify(resp: Response) -> Response:
        resp.response_headers["X-Modified"] = "true"
        return resp
    
    # Создаем Execute с обеими функциями
    execute = Execute.ALL(
        request_modify=mock_request_modify,
        response_modify=mock_response_modify,
        max_modifications=2,
        max_responses=3
    )
    
    assert execute.action.name == "ALL"
    assert execute.request_modify is not None
    assert execute.response_modify is not None
    assert execute.max_modifications == 2
    assert execute.max_responses == 3


def test_request_object_functionality():
    """Тест функциональности Request объекта"""
    
    # Создаем Request объект
    request = Request(
        url="https://example.com/api",
        headers={"Authorization": "Bearer token"},
        params={"page": "1"},
        method=HttpMethod.POST
    )
    
    # Проверяем базовые свойства
    assert request.url == "https://example.com/api"
    assert request.method == HttpMethod.POST
    assert "Authorization" in request.headers
    assert request.params["page"] == "1"
    
    # Тестируем модификацию свойств (новый API)
    # Убеждаемся что свойства инициализированы
    if request.headers is None:
        request.headers = {}
    if request.params is None:
        request.params = {}
        
    request.headers["X-Custom"] = "value"
    request.params["limit"] = "10"
    
    assert request.headers["X-Custom"] == "value"
    assert request.params["limit"] == "10"
    
    # Проверяем real_url
    assert "page=1" in request.real_url
    assert "limit=10" in request.real_url


def test_execute_validation():
    """Тест валидации параметров Execute"""
    
    # MODIFY должен требовать хотя бы одну из функций модификации
    with pytest.raises(ValueError, match="at least one of response_modify or request_modify"):
        Execute.MODIFY(max_modifications=1)
    
    # ALL должен требовать хотя бы одну из функций модификации
    with pytest.raises(ValueError, match="at least one of response_modify or request_modify"):
        Execute.ALL(max_modifications=1, max_responses=1)
    
    # RETURN не должен принимать функции модификации
    with pytest.raises(ValueError, match="should not have response_modify"):
        Execute(action=ExecuteAction.RETURN, response_modify=lambda x: x, max_responses=1)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

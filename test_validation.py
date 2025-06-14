"""
Тест для проверки правильности валидации Execute
"""
import pytest
from standard_open_inflation_package import Execute, Request, Response

def test_execute_validation_correct():
    """Тест правильной валидации Execute - требуется ОДНО ИЗ (request_modify ИЛИ response_modify)"""
    
    def dummy_request_modifier(req: Request) -> Request:
        return req
    
    def dummy_response_modifier(resp: Response) -> Response:
        return resp
    
    # MODIFY с только request_modify - должно работать
    execute1 = Execute.MODIFY(request_modify=dummy_request_modifier, max_modifications=1)
    assert execute1.request_modify is not None
    assert execute1.response_modify is None
    
    # MODIFY с только response_modify - должно работать
    execute2 = Execute.MODIFY(response_modify=dummy_response_modifier, max_modifications=1)
    assert execute2.request_modify is None
    assert execute2.response_modify is not None
    
    # MODIFY с обеими функциями - тоже должно работать
    execute3 = Execute.MODIFY(
        request_modify=dummy_request_modifier,
        response_modify=dummy_response_modifier,
        max_modifications=1
    )
    assert execute3.request_modify is not None
    assert execute3.response_modify is not None
    
    # ALL с только request_modify - должно работать
    execute4 = Execute.ALL(request_modify=dummy_request_modifier, max_modifications=1, max_responses=1)
    assert execute4.request_modify is not None
    assert execute4.response_modify is None
    
    # ALL с только response_modify - должно работать
    execute5 = Execute.ALL(response_modify=dummy_response_modifier, max_modifications=1, max_responses=1)
    assert execute5.request_modify is None
    assert execute5.response_modify is not None

def test_execute_validation_fails():
    """Тест что валидация падает когда не указано ни одного модификатора"""
    
    # MODIFY без модификаторов - должно падать
    with pytest.raises(ValueError, match="requires at least one of"):
        Execute.MODIFY(max_modifications=1)
    
    # ALL без модификаторов - должно падать  
    with pytest.raises(ValueError, match="requires at least one of"):
        Execute.ALL(max_modifications=1, max_responses=1)

if __name__ == "__main__":
    test_execute_validation_correct()
    test_execute_validation_fails()
    print("Все тесты валидации прошли успешно!")

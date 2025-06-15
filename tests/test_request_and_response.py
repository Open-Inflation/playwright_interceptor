"""
Demonstration test for new request_modify and response_modify functionality
"""
import pytest
from playwright_interceptor import Execute, Request, Response, HttpMethod, ExecuteAction


def test_execute_modify_with_request_and_response():
    """Test Execute.MODIFY with both functions: request_modify and response_modify"""
    
    def mock_request_modify(req: Request) -> Request:
        if req.headers is None:
            req.headers = {}
        req.headers["X-Test"] = "request-modified"
        return req
    
    def mock_response_modify(resp: Response) -> Response:
        resp.response_headers["X-Test"] = "response-modified"
        return resp
    
    # Create Execute with both functions
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
    """Test Execute.ALL with both functions: request_modify and response_modify"""
    
    def mock_request_modify(req: Request) -> Request:
        if req.params is None:
            req.params = {}
        req.params["modified"] = "true"
        return req
    
    def mock_response_modify(resp: Response) -> Response:
        resp.response_headers["X-Modified"] = "true"
        return resp
    
    # Create Execute with both functions
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
    """Test Request object functionality"""
    
    # Create Request object
    request = Request(
        url="https://example.com/api",
        headers={"Authorization": "Bearer token"},
        params={"page": "1"},
        method=HttpMethod.POST
    )
    
    # Check basic properties
    assert request.url == "https://example.com/api"
    assert request.method == HttpMethod.POST
    assert request.headers is not None
    assert "Authorization" in request.headers
    assert request.params is not None
    assert request.params["page"] == "1"
    
    # Test property modification (direct access)
    request.headers["X-Custom"] = "value"
    request.params["limit"] = "10"
    
    assert request.headers["X-Custom"] == "value"
    assert request.params["limit"] == "10"
    
    # Check real_url
    assert "page=1" in request.real_url
    assert "limit=10" in request.real_url


def test_execute_validation():
    """Test Execute parameter validation"""
    
    # MODIFY should require at least one modification function
    with pytest.raises(ValueError, match="at least one of response_modify or request_modify"):
        Execute.MODIFY(max_modifications=1)
    
    # ALL should require at least one modification function
    with pytest.raises(ValueError, match="at least one of response_modify or request_modify"):
        Execute.ALL(max_modifications=1, max_responses=1)
    
    # RETURN should not accept modification functions
    with pytest.raises(ValueError, match="should not have response_modify"):
        Execute(action=ExecuteAction.RETURN, response_modify=lambda x: x, max_responses=1)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

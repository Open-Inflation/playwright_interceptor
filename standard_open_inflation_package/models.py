import urllib.parse
from beartype import beartype
from beartype.typing import Union, Optional
from enum import Enum
from io import BytesIO
from . import config as CFG


class HttpMethod(Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"


class Response:
    """Класс для представления ответа от API"""
    
    @beartype
    def __init__(self, status: int, request_headers: dict, response_headers: dict, response: Union[dict, list, str, BytesIO], 
                 duration: float = 0.0):
        self.status = status
        self.request_headers = request_headers
        self.response_headers = response_headers
        self.response = response
        self.duration = duration  # Время выполнения запроса в секундах


class NetworkError:
    """Класс для представления сетевых ошибок"""
    
    @beartype
    def __init__(self, name: str, message: str, details: dict, timestamp: str, duration: float = 0.0):
        self.name = name
        self.message = message
        self.details = details
        self.timestamp = timestamp
        self.duration = duration
    
    def __str__(self):
        return f"NetworkError({self.name}: {self.message})"
    
    def __repr__(self):
        return f"NetworkError(name='{self.name}', message='{self.message}', timestamp='{self.timestamp}')"


class Handler:
    @beartype
    def __init__(self, handler_type: str, target_url: Optional[str] = None, content_type: Optional[str] = None, method: HttpMethod = HttpMethod.GET):
        self.handler_type = handler_type
        self.target_url = target_url
        self.content_type = content_type
        self.method = method
    
    @classmethod
    @beartype
    def MAIN(cls, method: HttpMethod = HttpMethod.GET):
        return cls("main", method=method)
    
    @classmethod
    @beartype
    def CAPTURE(cls, target_url: Optional[str] = None, type: Optional[str] = None, method: HttpMethod = HttpMethod.GET):
        return cls("capture", target_url, type, method)
    
    @classmethod
    @beartype
    def JSON(cls, target_url: Optional[str] = None, method: HttpMethod = HttpMethod.GET):
        return cls("json", target_url, "json", method)
    
    @classmethod
    @beartype
    def JS(cls, target_url: Optional[str] = None, method: HttpMethod = HttpMethod.GET):
        return cls("js", target_url, "js", method)
    
    @classmethod
    @beartype
    def CSS(cls, target_url: Optional[str] = None, method: HttpMethod = HttpMethod.GET):
        return cls("css", target_url, "css", method)
    
    @classmethod
    @beartype
    def IMAGE(cls, target_url: Optional[str] = None, method: HttpMethod = HttpMethod.GET):
        return cls("image", target_url, "image", method)

    @beartype
    def should_capture(self, resp, base_url: str) -> bool:
        """Определяет, должен ли handler захватить данный response"""
        full_url = urllib.parse.unquote(resp.url)
        ctype = resp.headers.get("content-type", "").lower()
        
        # Проверяем метод запроса
        if resp.request.method != self.method.value:
            return False
        
        if self.handler_type == "main":
            # Для MAIN проверяем основную страницу
            if not full_url.startswith(base_url):
                return False
            return CFG.CONTENT_TYPE_JSON in ctype or CFG.CONTENT_TYPE_HTML in ctype or CFG.CONTENT_TYPE_IMAGE in ctype
        
        # Для всех остальных типов проверяем URL если указан
        if self.target_url and not full_url.startswith(self.target_url):
            return False
        
        # Проверяем тип контента на основе реального content-type из response
        if self.handler_type == "json":
            return CFG.CONTENT_TYPE_JSON in ctype
        elif self.handler_type == "js":
            return CFG.CONTENT_TYPE_JAVASCRIPT in ctype
        elif self.handler_type == "css":
            return CFG.CONTENT_TYPE_CSS in ctype
        elif self.handler_type == "image":
            return CFG.CONTENT_TYPE_IMAGE in ctype
        elif self.handler_type == "capture":
            # Любой первый запрос
            return True
        
        return False

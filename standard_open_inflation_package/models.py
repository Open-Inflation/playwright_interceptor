import urllib.parse
from beartype import beartype
from beartype.typing import Union, Optional, Dict
from .tools import parse_content_type
from enum import Enum
from io import BytesIO
import urllib.parse
from . import config as CFG


class HttpMethod(Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"
    ANY = None  # Специальный метод для захвата любых запросов


class Response:
    """Класс для представления ответа от API"""
    
    @beartype
    def __init__(self, status: int, request_headers: dict, response_headers: dict, response: Union[dict, list, str, BytesIO, None] = None, 
                 duration: float = 0.0, url: Optional[str] = None):
        self.status = status
        self.request_headers = request_headers
        self.response_headers = response_headers
        self.response = response
        self.duration = duration  # Время выполнения запроса в секундах
        self.url = url  # URL эндпоинта, с которого пришёл ответ
    
    def __str__(self) -> str:
        type_data = parse_content_type(self.response_headers.get('content-type', 'unknown'))
        content_type = type_data["content_type"]
        response_type = type(self.response).__name__
        response_size = "unknown"
        
        # Определяем размер ответа
        if isinstance(self.response, (dict, list)):
            response_size = f"{len(str(self.response))} chars"
        elif isinstance(self.response, str):
            response_size = f"{len(self.response)} chars"
        elif isinstance(self.response, BytesIO):
            response_size = f"{len(self.response.getvalue())} bytes"
        
        url_info = f", url='{self.url}'" if self.url else ""
        return f"Response(status={self.status}, type={response_type}, content_type='{content_type}', size={response_size}, duration={self.duration:.3f}s{url_info})"
    
    def __repr__(self) -> str:
        url_info = f", url='{self.url}'" if self.url else ""
        return f"Response(status={self.status}, headers={len(self.response_headers)}, response_type={type(self.response).__name__}, duration={self.duration}{url_info})"

class Request:
    """Класс для представления HTTP запроса с возможностью модификации"""
    
    @beartype
    def __init__(self, url: str, headers: Optional[Dict[str, str]] = None, params: Optional[Dict[str, str]] = None, 
                 body: Optional[Union[dict, str]] = None, method: HttpMethod = HttpMethod.GET):
        self._original_url = url
        self._parsed_url = urllib.parse.urlparse(url)
        
        # Парсим существующие параметры из URL
        self._parsed_params = dict(urllib.parse.parse_qsl(self._parsed_url.query))
        
        # Объединяем с переданными параметрами
        if params:
            self._parsed_params.update(params)
        
        # Инициализируем заголовки
        self._headers = headers or {}
        
        # Инициализируем body и method
        self._body = body
        self._method = method
    
    @property
    def url(self) -> str:
        """Возвращает базовый URL без параметров"""
        return urllib.parse.urlunparse((
            self._parsed_url.scheme,
            self._parsed_url.netloc,
            self._parsed_url.path,
            self._parsed_url.params,
            '',  # query - пустая, так как параметры отдельно
            self._parsed_url.fragment
        ))
    
    @property
    def headers(self) -> Dict[str, str]:
        """Возвращает словарь заголовков"""
        return self._headers.copy()
    
    @property
    def params(self) -> Dict[str, str]:
        """Возвращает словарь параметров запроса"""
        return self._parsed_params.copy()
    
    @property
    def body(self) -> Optional[Union[dict, str]]:
        """Возвращает тело запроса"""
        return self._body
    
    @property
    def method(self) -> HttpMethod:
        """Возвращает HTTP метод запроса"""
        return self._method
    
    @property
    def real_url(self) -> str:
        """Собирает и возвращает финальный URL с параметрами"""
        if not self._parsed_params:
            return self.url
        
        query_string = urllib.parse.urlencode(self._parsed_params)
        return urllib.parse.urlunparse((
            self._parsed_url.scheme,
            self._parsed_url.netloc,
            self._parsed_url.path,
            self._parsed_url.params,
            query_string,
            self._parsed_url.fragment
        ))
    
    @beartype
    def add_header(self, name: str, value: str) -> 'Request':
        """Добавляет заголовок к запросу"""
        self._headers[name] = value
        return self
    
    @beartype
    def add_headers(self, headers: Dict[str, str]) -> 'Request':
        """Добавляет множественные заголовки к запросу"""
        self._headers.update(headers)
        return self
    
    @beartype
    def add_param(self, name: str, value: str) -> 'Request':
        """Добавляет параметр к запросу"""
        self._parsed_params[name] = value
        return self
    
    @beartype
    def add_params(self, params: Dict[str, str]) -> 'Request':
        """Добавляет множественные параметры к запросу"""
        self._parsed_params.update(params)
        return self
    
    @beartype
    def remove_header(self, name: Union[str, list[str]]) -> 'Request':
        """Удаляет заголовок(и) из запроса"""
        if isinstance(name, str):
            self._headers.pop(name, None)
        else:
            for header_name in name:
                self._headers.pop(header_name, None)
        return self
    
    @beartype
    def remove_param(self, name: Union[str, list[str]]) -> 'Request':
        """Удаляет параметр(ы) из запроса"""
        if isinstance(name, str):
            self._parsed_params.pop(name, None)
        else:
            for param_name in name:
                self._parsed_params.pop(param_name, None)
        return self
    
    @beartype
    def set_body(self, body: Optional[Union[dict, str]]) -> 'Request':
        """Устанавливает тело запроса"""
        self._body = body
        return self
    
    @beartype
    def set_method(self, method: HttpMethod) -> 'Request':
        """Устанавливает HTTP метод запроса"""
        self._method = method
        return self
    
    def __str__(self) -> str:
        return f"Request(method={self._method.value}, url='{self.real_url}', headers={len(self._headers)}, params={len(self._parsed_params)}, body={'set' if self._body else 'none'})"
    
    def __repr__(self) -> str:
        return f"Request(method={self._method.value}, url='{self._original_url}', headers={self._headers}, params={self._parsed_params}, body={self._body})"


class Handler:
    @beartype
    def __init__(self, handler_type: str, startswith_url: Optional[str] = None, content_type: Optional[str] = None, method: HttpMethod = HttpMethod.ANY):
        self.handler_type = handler_type
        self.startswith_url = startswith_url
        self.content_type = content_type
        self.method = method
    
    @classmethod
    @beartype
    def MAIN(cls):
        return cls("main")
    
    @classmethod
    @beartype
    def ANY(cls, startswith_url: Optional[str] = None, method: HttpMethod = HttpMethod.ANY):
        return cls("any", startswith_url, "", method)
    
    @classmethod
    @beartype
    def JSON(cls, startswith_url: Optional[str] = None, method: HttpMethod = HttpMethod.ANY):
        return cls("json", startswith_url, "json", method)
    
    @classmethod
    @beartype
    def JS(cls, startswith_url: Optional[str] = None, method: HttpMethod = HttpMethod.ANY):
        return cls("js", startswith_url, "js", method)
    
    @classmethod
    @beartype
    def CSS(cls, startswith_url: Optional[str] = None, method: HttpMethod = HttpMethod.ANY):
        return cls("css", startswith_url, "css", method)
    
    @classmethod
    @beartype
    def IMAGE(cls, startswith_url: Optional[str] = None, method: HttpMethod = HttpMethod.ANY):
        return cls("image", startswith_url, "image", method)
    
    @classmethod
    @beartype
    def VIDEO(cls, startswith_url: Optional[str] = None, method: HttpMethod = HttpMethod.ANY):
        return cls("video", startswith_url, "video", method)
    
    @classmethod
    @beartype
    def AUDIO(cls, startswith_url: Optional[str] = None, method: HttpMethod = HttpMethod.ANY):
        return cls("audio", startswith_url, "audio", method)
    
    @classmethod
    @beartype
    def FONT(cls, startswith_url: Optional[str] = None, method: HttpMethod = HttpMethod.ANY):
        return cls("font", startswith_url, "font", method)
    
    @classmethod
    @beartype
    def APPLICATION(cls, startswith_url: Optional[str] = None, method: HttpMethod = HttpMethod.ANY):
        return cls("application", startswith_url, "application", method)
    
    @classmethod
    @beartype
    def ARCHIVE(cls, startswith_url: Optional[str] = None, method: HttpMethod = HttpMethod.ANY):
        return cls("archive", startswith_url, "archive", method)
    
    @classmethod
    @beartype
    def TEXT(cls, startswith_url: Optional[str] = None, method: HttpMethod = HttpMethod.ANY):
        return cls("text", startswith_url, "text", method)
    
    @classmethod
    @beartype
    def NONE(cls):
        return cls("none")

    @beartype
    def should_capture(self, resp, base_url: str) -> bool:
        """Определяет, должен ли handler захватить данный response"""
        full_url = urllib.parse.unquote(resp.url)
        type_data = parse_content_type(resp.headers.get("content-type", ""))
        ctype = type_data["content_type"]
        
        # Проверяем метод запроса
        if self.method != HttpMethod.ANY and resp.request.method != self.method.value:
            return False
        
        if self.handler_type == "main":
            # Для MAIN проверяем основную страницу с учетом возможных редиректов
            from urllib.parse import urlparse
            base_parsed = urlparse(base_url)
            resp_parsed = urlparse(full_url)
            
            # Сравниваем схему, хост и порт
            return (base_parsed.scheme == resp_parsed.scheme and 
                    base_parsed.netloc == resp_parsed.netloc and
                    # Путь может быть пустым или корневым
                    (resp_parsed.path in ['', '/'] or resp_parsed.path == base_parsed.path))
        # Если мы не слушаем main, то не реагируем
        elif base_url == full_url:
            return False

        # Для всех остальных типов проверяем URL если указан
        if self.startswith_url and not full_url.startswith(self.startswith_url):
            return False
        
        # Проверяем тип контента на основе реального content-type из response
        match self.handler_type:
            case "json":
                return ctype in CFG.JSON_EXTENSIONS
            case "js":
                return ctype in CFG.JS_EXTENSIONS
            case "css":
                return ctype in CFG.CSS_EXTENSIONS
            case "image":
                return ctype in CFG.IMAGE_EXTENSIONS
            case "video":
                return ctype in CFG.VIDEO_EXTENSIONS
            case "audio":
                return ctype in CFG.AUDIO_EXTENSIONS
            case "font":
                return ctype in CFG.FONT_EXTENSIONS
            case "application":
                return ctype in CFG.APPLICATION_EXTENSIONS
            case "archive":
                return ctype in CFG.ARCHIVE_EXTENSIONS
            case "text":
                return ctype in CFG.TEXT_EXTENSIONS
            case "any":
                # Любой первый запрос
                return True
            case "none":
                # Не захватываем ничего
                return False
            case _:
                raise TypeError(f"Unknown handler type: {self.handler_type}")

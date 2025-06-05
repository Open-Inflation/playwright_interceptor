import urllib.parse
from beartype import beartype
from beartype.typing import Union, Optional, Dict, List
from .tools import parse_content_type
from enum import Enum
from io import BytesIO
from dataclasses import dataclass
from datetime import datetime
from . import config as CFG


@beartype
@dataclass(frozen=False)
class Cookie:
    """Класс для представления HTTP cookie с полной информацией"""
    
    name: str
    value: str
    domain: str
    path: Optional[str] = None
    expires: Optional[datetime] = None
    max_age: Optional[int] = None
    secure: bool = False
    http_only: bool = False
    same_site: Optional[str] = None  # None, 'Strict', 'Lax', 'None'
    
    def to_playwright_dict(self) -> Dict:
        """Конвертирует Cookie в формат для Playwright API"""
        cookie_dict: Dict = {
            'name': self.name,
            'value': self.value,
        }
        
        if self.domain:
            cookie_dict['domain'] = self.domain
        if self.path:
            cookie_dict['path'] = self.path
        if self.expires:
            cookie_dict['expires'] = int(self.expires.timestamp())
        if self.max_age is not None:
            cookie_dict['maxAge'] = self.max_age
        if self.secure:
            cookie_dict['secure'] = self.secure
        if self.http_only:
            cookie_dict['httpOnly'] = self.http_only
        if self.same_site:
            cookie_dict['sameSite'] = self.same_site
            
        return cookie_dict
    
    @classmethod
    def from_playwright_dict(cls, cookie_data: Dict) -> 'Cookie':
        """Создает Cookie из данных Playwright API"""
        expires = None
        if 'expires' in cookie_data and cookie_data['expires'] != -1:
            expires = datetime.fromtimestamp(cookie_data['expires'])
            
        return cls(
            name=cookie_data.get('name', ''),
            value=cookie_data.get('value', ''),
            domain=cookie_data.get('domain'),
            path=cookie_data.get('path'),
            expires=expires,
            max_age=cookie_data.get('maxAge'),
            secure=cookie_data.get('secure', False),
            http_only=cookie_data.get('httpOnly', False),
            same_site=cookie_data.get('sameSite')
        )
    
    @staticmethod
    def _parse_cookie_date(date_str: str) -> Optional[datetime]:
        """
        Парсит дату из Cookie в различных форматах.
        
        Args:
            date_str: Строка с датой
            
        Returns:
            datetime объект или None если парсинг не удался
        """
        # Список поддерживаемых форматов дат в cookies
        date_formats = [
            '%a, %d %b %Y %H:%M:%S GMT',  # RFC 1123: Wed, 21 Oct 2015 07:28:00 GMT
            '%a, %d-%b-%Y %H:%M:%S GMT',  # RFC 1036: Wednesday, 21-Oct-15 07:28:00 GMT  
            '%a %b %d %H:%M:%S %Y',       # ANSI C: Wed Oct 21 07:28:00 2015
            '%a, %d %b %Y %H:%M:%S %Z',   # RFC 1123 с временной зоной
            '%a, %d-%b-%y %H:%M:%S %Z',   # RFC 1036 с временной зоной
        ]
        
        for date_format in date_formats:
            try:
                return datetime.strptime(date_str.strip(), date_format)
            except ValueError:
                continue
                
        return None  # Если ни один формат не подошёл
    
    def __str__(self) -> str:
        return f"Cookie(name='{self.name}', value='{self.value}', domain='{self.domain}', path='{self.path}')"
    
    def __repr__(self) -> str:
        return f"Cookie(name='{self.name}', value='{self.value}', domain='{self.domain}', path='{self.path}', secure={self.secure}, http_only={self.http_only})"


class HttpMethod(Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"
    ANY = None  # Специальный метод для захвата любых запросов


@beartype
@dataclass(frozen=True)
class Response:
    """Класс для представления ответа от API"""
    
    status: int
    request_headers: dict
    response_headers: dict
    response: Union[dict, list, str, BytesIO, None] = None
    duration: float = 0.0
    url: Optional[str] = None
    
    def __str__(self) -> str:
        type_data = parse_content_type(self.response_headers.get('content-type', CFG.LOGS.UNKNOWN_HEADER_TYPE))
        content_type = type_data["content_type"]
        response_type = type(self.response).__name__

        response_size = CFG.LOGS.UNLIMITED_SIZE
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

@beartype
class Request:
    """Класс для представления HTTP запроса с возможностью модификации"""
    
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
    
    def add_header(self, name: str, value: str) -> 'Request':
        """Добавляет заголовок к запросу"""
        self._headers[name] = value
        return self
    
    def add_headers(self, headers: Dict[str, str]) -> 'Request':
        """Добавляет множественные заголовки к запросу"""
        self._headers.update(headers)
        return self
    
    def add_param(self, name: str, value: str) -> 'Request':
        """Добавляет параметр к запросу"""
        self._parsed_params[name] = value
        return self
    
    def add_params(self, params: Dict[str, str]) -> 'Request':
        """Добавляет множественные параметры к запросу"""
        self._parsed_params.update(params)
        return self
    
    def remove_header(self, name: Union[str, list[str]]) -> 'Request':
        """Удаляет заголовок(и) из запроса"""
        if isinstance(name, str):
            self._headers.pop(name, None)
        else:
            for header_name in name:
                self._headers.pop(header_name, None)
        return self
    
    def remove_param(self, name: Union[str, list[str]]) -> 'Request':
        """Удаляет параметр(ы) из запроса"""
        if isinstance(name, str):
            self._parsed_params.pop(name, None)
        else:
            for param_name in name:
                self._parsed_params.pop(param_name, None)
        return self
    
    def set_body(self, body: Optional[Union[dict, str]]) -> 'Request':
        """Устанавливает тело запроса"""
        self._body = body
        return self
    
    def set_method(self, method: HttpMethod) -> 'Request':
        """Устанавливает HTTP метод запроса"""
        self._method = method
        return self
    
    def __str__(self) -> str:
        return f"Request(method={self._method.value}, url='{self.real_url}', headers={len(self._headers)}, params={len(self._parsed_params)}, body={'set' if self._body else 'none'})"
    
    def __repr__(self) -> str:
        return f"Request(method={self._method.value}, url='{self._original_url}', headers={self._headers}, params={self._parsed_params}, body={self._body})"

import urllib.parse
from beartype import beartype
from beartype.typing import Union, Optional, Dict
from .tools import parse_content_type
from enum import Enum
from io import BytesIO
from dataclasses import dataclass
from . import config as CFG
from enum import auto


class WatcherType(Enum):
    MAIN = auto()
    SIDE = auto()
    ALL = auto()

class ExpectedContentType(Enum):
    JSON = auto()
    JS = auto()
    CSS = auto()
    IMAGE = auto()
    VIDEO = auto()
    AUDIO = auto()
    FONT = auto()
    APPLICATION = auto()
    ARCHIVE = auto()
    TEXT = auto()
    ANY = auto()


class HttpMethod(Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"
    ANY = None  # Special method for capturing any requests


@beartype
@dataclass(frozen=False)
class Response:
    """Class for representing API response"""
    
    status: int
    request_headers: dict
    response_headers: dict
    content: bytes = b""
    duration: float = 0.0
    url: Optional[str] = None
    
    def content_parse(self) -> Union[dict, list, str, BytesIO]:
        """Parses response content into Python-like format"""
        from .content_loader import parse_response_data
        
        if not self.content:
            return ""
        
        # Look for content-type regardless of case
        content_type = ''
        for key, value in self.response_headers.items():
            if key.lower() == 'content-type':
                content_type = value
                break
        else:
            raise ValueError("Content-Type header not found in response headers")
                
        return parse_response_data(self.content, content_type)
    
    def __str__(self) -> str:
        type_data = parse_content_type(self.response_headers.get('content-type', CFG.LOGS.UNKNOWN_HEADER_TYPE))
        content_type = type_data["content_type"]
        content_size = f"{len(self.content)} bytes" if self.content else "0 bytes"
        
        url_info = f", url='{self.url}'" if self.url else ""
        return f"Response(status={self.status}, content_type='{content_type}', size={content_size}, duration={self.duration:.3f}s{url_info})"
    
    def __repr__(self) -> str:
        url_info = f", url='{self.url}'" if self.url else ""
        content_size = len(self.content) if self.content else 0
        return f"Response(status={self.status}, headers={len(self.response_headers)}, content_size={content_size}, duration={self.duration}{url_info})"

@beartype
@dataclass(frozen=False)
class Request:
    """Class for representing HTTP request with modification capability"""
    
    url: str
    headers: Optional[Dict[str, str]] = None
    params: Optional[Dict[str, str]] = None
    body: Optional[Union[dict, str]] = None
    method: HttpMethod = HttpMethod.GET
    
    def __post_init__(self):
        """Initialization after dataclass creation"""
        # Initialize empty dictionaries if None
        if self.headers is None:
            self.headers = {}
        if self.params is None:
            self.params = {}
            
        # Parse URL and extract existing parameters
        self._parsed_url = urllib.parse.urlparse(self.url)
        existing_params = dict(urllib.parse.parse_qsl(self._parsed_url.query))
        
        # Merge existing parameters with passed ones
        if existing_params:
            merged_params = existing_params.copy()
            merged_params.update(self.params)
            self.params = merged_params
    
    @property
    def base_url(self) -> str:
        """Returns base URL without parameters"""
        return urllib.parse.urlunparse((
            self._parsed_url.scheme,
            self._parsed_url.netloc,
            self._parsed_url.path,
            self._parsed_url.params,
            '',  # query - empty since parameters are separate
            self._parsed_url.fragment
        ))
    
    @property
    def real_url(self) -> str:
        """Builds and returns final URL with parameters"""
        if not self.params:
            return self.base_url
        
        query_string = urllib.parse.urlencode(self.params)
        return urllib.parse.urlunparse((
            self._parsed_url.scheme,
            self._parsed_url.netloc,
            self._parsed_url.path,
            self._parsed_url.params,
            query_string,
            self._parsed_url.fragment
        ))
    
    def __str__(self) -> str:
        headers_count = len(self.headers) if self.headers else 0
        params_count = len(self.params) if self.params else 0
        return f"Request(method={self.method.value}, url='{self.real_url}', headers={headers_count}, params={params_count}, body={'set' if self.body else 'none'})"
    
    def __repr__(self) -> str:
        return f"Request(method={self.method.value}, url='{self.url}', headers={self.headers}, params={self.params}, body={self.body})"

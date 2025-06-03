from .models import Response, HttpMethod
from .tools import parse_content_type
from beartype import beartype
from beartype.typing import List, Optional
import uuid
from . import config as CFG
import urllib.parse
from dataclasses import dataclass


@beartype
@dataclass(frozen=True)
class Handler:
    handler_type: str
    startswith_url: Optional[str] = None
    content_type: Optional[str] = None
    method: HttpMethod = HttpMethod.ANY
    max_responses: Optional[int] = None
    slug: Optional[str] = None
    
    def __post_init__(self):
        if self.slug is None:
            object.__setattr__(self, 'slug', str(uuid.uuid4())[:8])
    
    def __repr__(self) -> str:
        parts = [f"Handler.{self.handler_type.upper()}()"]
        if self.startswith_url:
            parts.append(f"url='{self.startswith_url}'")
        if self.method != HttpMethod.ANY:
            parts.append(f"method={self.method.value}")
        if self.max_responses is not None:
            parts.append(f"max_responses={self.max_responses}")
        parts.append(f"slug='{self.slug}'")
        return f"Handler({', '.join(parts)})"

    @classmethod
    def MAIN(cls, max_responses: Optional[int] = 1, slug: Optional[str] = None):
        return cls("main", max_responses=max_responses, slug=slug)
    
    @classmethod
    def ANY(cls, startswith_url: Optional[str] = None, method: HttpMethod = HttpMethod.ANY, max_responses: Optional[int] = None, slug: Optional[str] = None):
        return cls("any", startswith_url, "", method, max_responses, slug)
    
    @classmethod
    def JSON(cls, startswith_url: Optional[str] = None, method: HttpMethod = HttpMethod.ANY, max_responses: Optional[int] = None, slug: Optional[str] = None):
        return cls("json", startswith_url, "json", method, max_responses, slug)
    
    @classmethod
    def JS(cls, startswith_url: Optional[str] = None, method: HttpMethod = HttpMethod.ANY, max_responses: Optional[int] = None, slug: Optional[str] = None):
        return cls("js", startswith_url, "js", method, max_responses, slug)
    
    @classmethod
    def CSS(cls, startswith_url: Optional[str] = None, method: HttpMethod = HttpMethod.ANY, max_responses: Optional[int] = None, slug: Optional[str] = None):
        return cls("css", startswith_url, "css", method, max_responses, slug)
    
    @classmethod
    def IMAGE(cls, startswith_url: Optional[str] = None, method: HttpMethod = HttpMethod.ANY, max_responses: Optional[int] = None, slug: Optional[str] = None):
        return cls("image", startswith_url, "image", method, max_responses, slug)
    
    @classmethod
    def VIDEO(cls, startswith_url: Optional[str] = None, method: HttpMethod = HttpMethod.ANY, max_responses: Optional[int] = None, slug: Optional[str] = None):
        return cls("video", startswith_url, "video", method, max_responses, slug)
    
    @classmethod
    def AUDIO(cls, startswith_url: Optional[str] = None, method: HttpMethod = HttpMethod.ANY, max_responses: Optional[int] = None, slug: Optional[str] = None):
        return cls("audio", startswith_url, "audio", method, max_responses, slug)
    
    @classmethod
    def FONT(cls, startswith_url: Optional[str] = None, method: HttpMethod = HttpMethod.ANY, max_responses: Optional[int] = None, slug: Optional[str] = None):
        return cls("font", startswith_url, "font", method, max_responses, slug)
    
    @classmethod
    def APPLICATION(cls, startswith_url: Optional[str] = None, method: HttpMethod = HttpMethod.ANY, max_responses: Optional[int] = None, slug: Optional[str] = None):
        return cls("application", startswith_url, "application", method, max_responses, slug)
    
    @classmethod
    def ARCHIVE(cls, startswith_url: Optional[str] = None, method: HttpMethod = HttpMethod.ANY, max_responses: Optional[int] = None, slug: Optional[str] = None):
        return cls("archive", startswith_url, "archive", method, max_responses, slug)
    
    @classmethod
    def TEXT(cls, startswith_url: Optional[str] = None, method: HttpMethod = HttpMethod.ANY, max_responses: Optional[int] = None, slug: Optional[str] = None):
        return cls("text", startswith_url, "text", method, max_responses, slug)
    
    @classmethod
    def NONE(cls, max_responses: Optional[int] = None, slug: Optional[str] = None):
        return cls("none", max_responses=max_responses, slug=slug)

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
                raise TypeError(CFG.ERROR_UNKNOWN_HANDLER_TYPE.format(handler_type=self.handler_type))


@beartype
@dataclass(frozen=True)
class HandlerSearchSuccess:
    """Класс для представления успешного поиска handler'ом подходящего response"""
    responses: List[Response]
    duration: float = 0.0
    handler_slug: str = 'unknown'
    
    def __str__(self):
        return CFG.HANDLER_SUCCESS_MESSAGE.format(response_count=len(self.responses), handler_slug=self.handler_slug)
    
    def __repr__(self):
        return CFG.HANDLER_SUCCESS_REPR.format(duration=self.duration, response_count=len(self.responses))

@beartype
@dataclass(frozen=True)
class HandlerSearchFailed:
    """Класс для представления ошибки, когда handler не нашел подходящего response"""
    rejected_responses: List['Response']
    duration: float = 0.0
    handler_slug: str = 'unknown'
    
    def __str__(self):
        return CFG.HANDLER_FAILED_MESSAGE.format(handler_slug=self.handler_slug, rejected_count=len(self.rejected_responses))

    def __repr__(self):
        return CFG.HANDLER_FAILED_REPR.format(duration=self.duration, rejected_count=len(self.rejected_responses))

from .models import Response, HttpMethod
from .execute import Execute
from .tools import parse_content_type
from beartype import beartype
from beartype.typing import List, Optional
import uuid
from . import config as CFG
import urllib.parse
from urllib.parse import urlparse
from dataclasses import dataclass
from .models import WatcherType, ExpectedContentType


@beartype
@dataclass(frozen=True)
class Handler:
    watcher: WatcherType
    expected_content: ExpectedContentType = ExpectedContentType.ANY
    startswith_url: Optional[str] = None
    method: HttpMethod = HttpMethod.ANY
    execute: Execute = Execute.RETURN()
    slug: str = ""

    def __post_init__(self):
        if self.slug == "":
            object.__setattr__(self, 'slug', str(uuid.uuid4())[:8])

    def __repr__(self) -> str:
        parts = [f"Handler.{self.watcher.name}()"]
        if self.startswith_url:
            parts.append(f"url='{self.startswith_url}'")
        if self.expected_content:
            parts.append(f"content_types={self.expected_content.name}")
        if self.method != HttpMethod.ANY:
            parts.append(f"method={self.method.value}")
        parts.append(f"execute={self.execute.action.name}")
        parts.append(f"slug='{self.slug}'")
        return f"Handler({', '.join(parts)})"

    @classmethod
    def MAIN(
        cls,
        expected_content: ExpectedContentType = ExpectedContentType.TEXT,
        startswith_url: Optional[str] = None,
        method: HttpMethod = HttpMethod.ANY,
        execute: Execute = Execute.RETURN(1),
        slug: str = "",
    ):
        return cls(WatcherType.MAIN, expected_content, startswith_url, method, execute, slug)

    @classmethod
    def SIDE(
        cls,
        expected_content: ExpectedContentType = ExpectedContentType.ANY,
        startswith_url: Optional[str] = None,
        method: HttpMethod = HttpMethod.ANY,
        execute: Execute = Execute.RETURN(1),
        slug: str = "",
    ):
        return cls(WatcherType.SIDE, expected_content, startswith_url, method, execute, slug)

    @classmethod
    def ALL(
        cls,
        expected_content: ExpectedContentType = ExpectedContentType.ANY,
        startswith_url: Optional[str] = None,
        method: HttpMethod = HttpMethod.ANY,
        execute: Execute = Execute.RETURN(1),
        slug: str = "",
    ):
        return cls(WatcherType.ALL, expected_content, startswith_url, method, execute, slug)

    @classmethod
    def NONE(cls, slug: str = ""):
        return cls(WatcherType.ALL, startswith_url="!NONE!", execute=Execute.RETURN(), slug=slug)

    def should_capture(self, resp, base_url: str) -> bool:
        """Определяет, должен ли handler захватить данный response"""
        full_url = urllib.parse.unquote(resp.url)
        type_data = parse_content_type(resp.headers.get("content-type", ""))
        ctype = type_data["content_type"]

        def match_method() -> bool:
            # Проверяем метод запроса
            return self.method == HttpMethod.ANY or resp.request.method == self.method.value

        def match_content(ctype: str, expected: ExpectedContentType) -> bool:
            return {
                ExpectedContentType.JSON: ctype in CFG.NETWORK.JSON_EXTENSIONS,
                ExpectedContentType.JS: ctype in CFG.NETWORK.JS_EXTENSIONS,
                ExpectedContentType.CSS: ctype in CFG.NETWORK.CSS_EXTENSIONS,
                ExpectedContentType.IMAGE: ctype in CFG.NETWORK.IMAGE_EXTENSIONS,
                ExpectedContentType.VIDEO: ctype in CFG.NETWORK.VIDEO_EXTENSIONS,
                ExpectedContentType.AUDIO: ctype in CFG.NETWORK.AUDIO_EXTENSIONS,
                ExpectedContentType.FONT: ctype in CFG.NETWORK.FONT_EXTENSIONS,
                ExpectedContentType.APPLICATION: ctype in CFG.NETWORK.APPLICATION_EXTENSIONS,
                ExpectedContentType.ARCHIVE: ctype in CFG.NETWORK.ARCHIVE_EXTENSIONS,
                ExpectedContentType.TEXT: ctype in CFG.NETWORK.TEXT_EXTENSIONS,
                ExpectedContentType.ANY: True
            }[expected]
        
        def match_watcher():
            if self.watcher == WatcherType.ALL:
                return True
            else:
                is_main = (
                    base_parsed.scheme == resp_parsed.scheme and
                    base_parsed.netloc == resp_parsed.netloc and
                    (resp_parsed.path in ['', '/'] or resp_parsed.path == base_parsed.path)
                )
                if self.watcher == WatcherType.MAIN:
                    return is_main
                else:
                    return not is_main

        base_parsed = urlparse(base_url)
        resp_parsed = urlparse(full_url)

        return (self.startswith_url is None or full_url.startswith(self.startswith_url)) and \
                match_watcher() and \
                match_method() and \
                match_content(ctype, self.expected_content)



@beartype
@dataclass(frozen=True)
class HandlerSearchSuccess:
    """Class for representing successful handler search for suitable response"""
    responses: List[Response]
    duration: float = 0.0
    handler_slug: str = 'unknown'
    
    def __str__(self):
        return f"HandlerSearchSuccess: Found {len(self.responses)} responses for `{self.handler_slug}` handler."
    
    def __repr__(self):
        return f"HandlerSearchSuccess(duration={self.duration:.1f}, response_count={len(self.responses)})"

@beartype
@dataclass(frozen=True)
class HandlerSearchFailed:
    """Class for representing error when handler didn't find suitable response"""
    rejected_responses: List['Response']
    duration: float = 0.0
    handler_slug: str = 'unknown'
    
    def __str__(self):
        return f"HandlerSearchFailedError: Not found suitable response for `{self.handler_slug}` handler. Rejected {len(self.rejected_responses)} responses."

    def __repr__(self):
        return f"HandlerSearchFailedError(duration={self.duration:.1f}, rejected_count={len(self.rejected_responses)})"

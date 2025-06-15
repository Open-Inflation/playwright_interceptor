"""
NetworkInterceptor addon for Playwright.

Provides advanced request interception and modification utilities.
"""

from .models import HttpMethod, Response, Request, ExpectedContentType
from .execute import Execute, ExecuteAction
from .handler import (
    Handler,
    HandlerSearchSuccess,
    HandlerSearchFailed,
)
from .network_interceptor import NetworkInterceptor

__version__ = "0.1.1"

__all__ = [
    "NetworkInterceptor",
    "Handler",
    "ExpectedContentType",
    "HandlerSearchSuccess",
    "HandlerSearchFailed",
    "Request",
    "Response",
    "HttpMethod",
    "Execute",
    "ExecuteAction",
]

import asyncio
import logging
import time
from typing import List, Optional, Union

from .handler import Handler
from .direct_request_interceptor import MultiRequestInterceptor
from .config import errors as ERR, logs as LOGS


class NetworkInterceptor:
    """Intercept and modify network requests for a Playwright page."""

    def __init__(self, page, *, logger: Optional[logging.Logger] = None) -> None:
        self.page = page
        self._logger = logger or logging.getLogger(self.__class__.__name__)

    async def execute(
        self,
        handlers: Union[Handler, List[Handler]],
        timeout: float = 30.0,
    ):
        if isinstance(handlers, Handler):
            handlers = [handlers]

        slugs = [h.slug for h in handlers]
        if len(slugs) != len(set(slugs)):
            duplicate_slugs = []
            seen = set()
            for slug in slugs:
                if slug in seen:
                    duplicate_slugs.append(slug)
                else:
                    seen.add(slug)
            raise ValueError(ERR.DUPLICATE_HANDLER_SLUGS.format(duplicate_slugs=duplicate_slugs))

        start_time = time.time()
        interceptor = MultiRequestInterceptor(self, handlers, self.page.url, start_time)

        try:
            await self.page.route("**/*", interceptor.handle_route)
            return await interceptor.wait_for_results(timeout)
        finally:
            try:
                await self.page.unroute("**/*", interceptor.handle_route)
            except Exception as e:
                self._logger.warning(LOGS.UNROUTE_CLEANUP_ERROR_DIRECT_FETCH.format(error=e))

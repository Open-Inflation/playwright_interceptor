import asyncio
import time
from beartype import beartype
from beartype.typing import Union, List, Dict
from .content_loader import parse_response_data
from . import config as CFG
from .models import Response, Request, HttpMethod
from .handler import Handler, HandlerSearchFailed, HandlerSearchSuccess
from .execute import ExecuteAction
from playwright._impl._errors import TargetClosedError


@beartype
class MockResponse:
    def __init__(self, status, headers, url, method):
        self.status = status
        self.headers = headers
        self.url = url
        self.request = type('MockRequest', (), {'method': method})()


@beartype
class MultiRequestInterceptor:
    """Class for intercepting HTTP requests with multiple handlers support"""
    
    def __init__(self, api, handlers: List[Handler], base_url: str, start_time: float):
        self.api = api
        self.handlers = handlers
        self.base_url = base_url
        self.start_time = start_time
        self.rejected_responses = []
        self.loop = asyncio.get_running_loop()
        
        # Dictionary for storing results of each handler (using slug as key)
        self.handler_results: Dict[str, List[Response]] = {handler.slug: [] for handler in handlers}
        self.handler_errors: Dict[str, HandlerSearchFailed] = {}
        self.handler_modifications: Dict[str, int] = {handler.slug: 0 for handler in handlers}
        
        # Future for completion
        self.completion_future = self.loop.create_future()
        self.timeout_task = None

    def _response_to_body(self, response: Response) -> Union[str, bytes]:
        """Converts Response object back to body for Playwright"""
        if not response.content:
            return ""
        # Always use content as bytes
        return response.content
    
    async def handle_route(self, route):
        """Route handler for intercepting requests"""
        request = route.request
        
        # Add explicit logging for each request
        self.api._logger.debug(f"INTERCEPTOR_HANDLE_ROUTE: URL={request.url}, Method={request.method}")
        
        # Check URL protocol - skip unsupported protocols
        if request.url.startswith(CFG.PARAMETERS.UNSUPPORTED_PROTOCOLS):
            self.api._logger.debug(f"UNSUPPORTED_PROTOCOL: {request.url}")
            # Continue request processing without interception
            await route.continue_()
            return
        
        # Check if there are handlers with request_modify
        request_modifying_handlers = []
        for handler in self.handlers:
            if handler.slug in self.handler_errors:
                continue
            
            # Check if handler hasn't completed all necessary actions
            if handler.execute.action in (ExecuteAction.MODIFY, ExecuteAction.ALL):
                if handler.execute.request_modify is not None:
                    if handler.execute.max_modifications is None or self.handler_modifications[handler.slug] < handler.execute.max_modifications:
                        request_modifying_handlers.append(handler)

        # Apply request modifications if there are suitable handlers
        modified_request = None
        if request_modifying_handlers:
            # Create Request object from original request
            try:
                method = HttpMethod(request.method) if request.method != "ANY" else HttpMethod.GET
            except ValueError:
                method = HttpMethod.GET
            
            # Parse parameters from URL
            from urllib.parse import urlparse, parse_qsl
            parsed_url = urlparse(request.url)
            params = dict(parse_qsl(parsed_url.query)) if parsed_url.query else {}
            
            # Get request body if exists
            body = None
            if hasattr(request, 'post_data') and request.post_data:
                body = request.post_data
            
            modified_request = Request(
                url=request.url,
                headers=dict(request.headers) if request.headers else {},
                params=params,
                body=body,
                method=method
            )
            
            # Apply modifications from all suitable handlers SEQUENTIALLY
            for handler in request_modifying_handlers:
                if handler.execute.request_modify is not None:
                    try:
                        if asyncio.iscoroutinefunction(handler.execute.request_modify):
                            modified_request = await handler.execute.request_modify(modified_request)
                        else:
                            modified_request = handler.execute.request_modify(modified_request)
                        
                        if isinstance(modified_request, Request):
                            self.handler_modifications[handler.slug] += 1
                            self.api._logger.debug(f"Request modified by handler {handler.slug}: {modified_request.real_url}")
                        else:
                            self.api._logger.warning(f"Handler {handler.slug} request_modify returned non-Request object")
                            modified_request = None
                            break
                    except Exception as e:
                        self.api._logger.warning(f"Request modification failed for handler {handler.slug}: {e}")
                        modified_request = None
                        break

        response_time = time.time()

        # Выполняем запрос (оригинальный или модифицированный)
        try:
            if modified_request is not None:
                # Формируем новые параметры для запроса
                new_headers = modified_request.headers
                new_url = modified_request.real_url
                new_method = modified_request.method.value
                
                # Выполняем модифицированный запрос
                response = await route.fetch(
                    url=new_url,
                    method=new_method,
                    headers=new_headers,
                    post_data=modified_request.body if isinstance(modified_request.body, str) else None
                )
            else:
                # Выполняем оригинальный запрос
                response = await route.fetch()
        except TargetClosedError:
            self.api._logger.info(CFG.LOGS.TARGET_CLOSED_ERROR.format(url=request.url))
            return
        except Exception as e:
            self.api._logger.warning(f"Failed to execute request: {e}")
            # Fallback к оригинальному запросу
            try:
                response = await route.fetch()
            except TargetClosedError:
                self.api._logger.info(CFG.LOGS.TARGET_CLOSED_ERROR.format(url=request.url))
                return

        # Создаем мок-объект для проверки хандлеров
        mock_response = MockResponse(response.status, response.headers, response.url, request.method)

        # Сначала определяем какие хендлеры должны захватить этот ответ
        capturing_handlers = []
        for handler in self.handlers:
            if handler.slug in self.handler_errors:
                continue  # Пропускаем хандлеры, которые уже завершились с ошибкой

            # Проверяем, не завершил ли хандлер все необходимые действия
            done_return = True
            done_modify = True
            if handler.execute.action in (ExecuteAction.RETURN, ExecuteAction.ALL):
                if handler.execute.max_responses is None or len(self.handler_results[handler.slug]) < handler.execute.max_responses:
                    done_return = False
            if handler.execute.action in (ExecuteAction.MODIFY, ExecuteAction.ALL):
                if handler.execute.max_modifications is None or self.handler_modifications[handler.slug] < handler.execute.max_modifications:
                    done_modify = False

            if done_return and done_modify:
                continue  # Хендлер завершил все действия
                
            if handler.should_capture(mock_response, self.base_url):
                capturing_handlers.append(handler)
                self.api._logger.debug(CFG.LOGS.HANDLER_WILL_CAPTURE.format(handler_type=handler.expected_content, url=response.url))
            else:
                self.api._logger.debug(CFG.LOGS.HANDLER_REJECTED.format(handler_type=handler.expected_content, url=response.url, content_type=response.headers.get('content-type', CFG.PARAMETERS.DEFAULT_CONTENT_TYPE)))
        
        # Если есть хандлеры для захвата, обрабатываем ответ один раз
        modified_response = None
        if capturing_handlers:
            modified_response = await self._handle_captured_response(capturing_handlers, response, request, response_time)
        else:
            self._handle_rejected_response(response, request, response_time)
            self.api._logger.debug(CFG.LOGS.ALL_HANDLERS_REJECTED.format(url=response.url))

        # Проверяем, завершены ли все хандлеры
        self._check_completion()
        
        # Возвращаем модифицированный ответ, если есть, иначе оригинальный
        if modified_response is not None:
            # Преобразуем модифицированный Response обратно в формат Playwright
            await route.fulfill(
                status=modified_response.status,
                headers=modified_response.response_headers,
                body=self._response_to_body(modified_response)
            )
        else:
            # Возвращаем оригинальный ответ
            await route.fulfill(response=response)
    
    async def _handle_captured_response(self, handlers: List[Handler], response, request, response_time: float) -> Union[Response, None]:
        """Processes captured response for multiple handlers and returns modified response"""
        try:
            # Получаем тело ответа ТОЛЬКО ОДИН РАЗ
            raw_data = await response.body()

            content_type = response.headers.get("content-type", "").lower()
            parsed_data = parse_response_data(raw_data, content_type)
            
            # Создаем Response объект 
            result = Response(
                status=response.status,
                request_headers=request.headers,
                response_headers=response.headers,
                content=raw_data,  # Сохраняем как bytes
                duration=response_time - self.start_time,
                url=response.url
            )

            # Применяем response_modify ПОСЛЕДОВАТЕЛЬНО от всех хандлеров
            modified_result: Response = result
            for handler in handlers:
                if handler.execute.action in (ExecuteAction.MODIFY, ExecuteAction.ALL):
                    if handler.execute.max_modifications is None or self.handler_modifications[handler.slug] < handler.execute.max_modifications:
                        if handler.execute.response_modify is not None:
                            try:
                                if asyncio.iscoroutinefunction(handler.execute.response_modify):
                                    modification_result = await handler.execute.response_modify(modified_result)
                                else:
                                    modification_result = handler.execute.response_modify(modified_result)
                                
                                if isinstance(modification_result, Response):
                                    modified_result = modification_result
                                    self.handler_modifications[handler.slug] += 1
                                    self.api._logger.debug(f"Response modified by handler {handler.slug}")
                                else:
                                    # Если функция вернула что-то другое, используем предыдущий результат
                                    self.api._logger.warning(f"Handler {handler.slug} response_modify returned non-Response object")
                            except Exception as e:
                                self.api._logger.warning(f"Response modification failed for handler {handler.slug}: {e}")
                                # Продолжаем с предыдущим результатом

            # Сохраняем результаты для хандлеров, которые нуждаются в RETURN
            for handler in handlers:
                if handler.execute.action in (ExecuteAction.RETURN, ExecuteAction.ALL):
                    self.handler_results[handler.slug].append(modified_result)
                    max_resp_text = handler.execute.max_responses or CFG.LOGS.UNLIMITED_SIZE
                    self.api._logger.info(
                        CFG.LOGS.HANDLER_CAPTURED_RESPONSE.format(
                            handler_type=handler.expected_content,
                            url=response.url,
                            current_count=len(self.handler_results[handler.slug]),
                            max_responses=max_resp_text,
                        )
                    )

            # ВАЖНО: Возвращаем модифицированный ответ
            return modified_result
                
        except Exception as e:
            # Если произошла ошибка, логируем для всех хандлеров
            handler_types = ', '.join(str(handler.slug) for handler in handlers)
            self.api._logger.warning(CFG.ERRORS.FAILED_PROCESS_RESPONSE.format(
                handler_list=handler_types,
                url=response.url,
                error=e
            ))
            current_time = time.time()
            for handler in handlers:
                self.handler_errors[handler.slug] = HandlerSearchFailed(
                    rejected_responses=self.rejected_responses,
                    duration=current_time - self.start_time,
                    handler_slug=handler.slug,
                )
            self._check_completion()
            return None

    def _handle_rejected_response(self, response, request, response_time: float):
        """Processes rejected response"""
        # Сохраняем отклоненные ответы для анализа
        duration = response_time - self.start_time
        self.rejected_responses.append(Response(
            status=response.status,
            request_headers=request.headers,
            response_headers=response.headers,
            content=b"",  # Пустое содержимое для отклоненных ответов
            duration=duration,
            url=response.url
        ))
    
    def _check_completion(self):
        """Checks if all handlers are completed"""
        if self.completion_future.done():
            return
            
        # Проверяем каждый хандлер
        all_completed = True
        for handler in self.handlers:
            if handler.slug in self.handler_errors:
                continue  # Уже завершен с ошибкой

            done_return = True
            done_modify = True
            if handler.execute.action in (ExecuteAction.RETURN, ExecuteAction.ALL):
                if handler.execute.max_responses is None or len(self.handler_results[handler.slug]) < handler.execute.max_responses:
                    done_return = False
            if handler.execute.action in (ExecuteAction.MODIFY, ExecuteAction.ALL):
                if handler.execute.max_modifications is None or self.handler_modifications[handler.slug] < handler.execute.max_modifications:
                    done_modify = False

            if not (done_return and done_modify):
                all_completed = False
                break
        
        # Если все хандлеры достигли своих лимитов, завершаем работу
        if all_completed:
            self.api._logger.info(CFG.LOGS.ALL_HANDLERS_COMPLETED)
            self._complete_all_handlers()
    
    def _complete_all_handlers(self):
        """Завершает работу всех хандлеров"""
        if self.completion_future.done():
            return
            
        # Формируем результат
        result = []
        current_time = time.time()
        
        for handler in self.handlers:
            if handler.slug in self.handler_errors:
                result.append(self.handler_errors[handler.slug])
            elif self.handler_results[handler.slug] or (
                handler.execute.action == ExecuteAction.MODIFY and self.handler_modifications[handler.slug] > 0
            ):
                duration = current_time - self.start_time
                result.append(HandlerSearchSuccess(
                    responses=self.handler_results[handler.slug],
                    duration=duration,
                    handler_slug=handler.slug
                ))
            else:
                # Хандлер не получил ни одного ответа
                duration = current_time - self.start_time
                error = HandlerSearchFailed(
                    rejected_responses=self.rejected_responses,
                    duration=duration,
                    handler_slug=handler.slug
                )
                result.append(error)
        
        self.completion_future.set_result(result)
    
    async def wait_for_results(self, timeout: float) -> List[Union[HandlerSearchSuccess, HandlerSearchFailed]]:
        """Ожидает результатов всех хандлеров с таймаутом"""
        # Устанавливаем таймаут
        self.timeout_task = asyncio.create_task(asyncio.sleep(timeout))
        
        # Ожидаем либо завершения всех хандлеров, либо таймаута
        done, _pending = await asyncio.wait(
            [self.completion_future, self.timeout_task],
            return_when=asyncio.FIRST_COMPLETED
        )
        
        if self.completion_future in done:
            # Все хандлеры завершились
            self.timeout_task.cancel()
            return await self.completion_future
        else:
            # Таймаут
            duration = time.time() - self.start_time
            self.api._logger.warning(CFG.LOGS.TIMEOUT_REACHED.format(base_url=self.base_url, duration=duration))
            
            # Формируем результат с тем, что успели получить
            result = []
            for handler in self.handlers:
                if self.handler_results[handler.slug] or (
                    handler.execute.action == ExecuteAction.MODIFY and self.handler_modifications[handler.slug] > 0
                ):
                    result.append(
                        HandlerSearchSuccess(
                            responses=self.handler_results[handler.slug],
                            duration=duration,
                            handler_slug=handler.slug,
                        )
                    )
                else:
                    result.append(
                        HandlerSearchFailed(
                            rejected_responses=self.rejected_responses,
                            duration=duration,
                            handler_slug=handler.slug,
                        )
                    )

            return result


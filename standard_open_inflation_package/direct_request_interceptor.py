import asyncio
import time
from beartype import beartype
from beartype.typing import Union, List, Dict
from .content_loader import parse_response_data
from . import config as CFG
from .models import Response
from .handler import Handler, HandlerSearchFailed, HandlerSearchSuccess


@beartype
class MockResponse:
    def __init__(self, status, headers, url, method):
        self.status = status
        self.headers = headers
        self.url = url
        self.request = type('MockRequest', (), {'method': method})()


@beartype
class MultiRequestInterceptor:
    """Класс для перехвата HTTP-запросов с поддержкой множественных хандлеров"""
    
    def __init__(self, api, handlers: List[Handler], base_url: str, start_time: float):
        self.api = api
        self.handlers = handlers
        self.base_url = base_url
        self.start_time = start_time
        self.rejected_responses = []
        self.loop = asyncio.get_running_loop()
        
        # Словарь для хранения результатов каждого хандлера (используем slug как ключ)
        self.handler_results: Dict[str, List[Response]] = {handler.slug: [] for handler in handlers}
        self.handler_errors: Dict[str, HandlerSearchFailed] = {}
        
        # Future для завершения работы
        self.completion_future = self.loop.create_future()
        self.timeout_task = None
    
    async def handle_route(self, route):
        """Обработчик маршрута для перехвата запросов"""
        request = route.request
        
        # Выполняем запрос
        response = await route.fetch()
        response_time = time.time()
        
        # Создаем мок-объект для проверки хандлеров
        mock_response = MockResponse(response.status, response.headers, response.url, request.method)

        # Сначала определяем какие хендлеры должны захватить этот ответ
        capturing_handlers = []
        for handler in self.handlers:
            if handler.slug in self.handler_errors:
                continue  # Пропускаем хандлеры, которые уже завершились с ошибкой
                
            # Проверяем, не достиг ли хендлер уже своего лимита
            if handler.max_responses is not None and len(self.handler_results[handler.slug]) >= handler.max_responses:
                continue  # Хендлер уже получил максимальное количество ответов
                
            if handler.should_capture(mock_response, self.base_url):
                capturing_handlers.append(handler)
                self.api._logger.debug(CFG.LOGS.HANDLER_WILL_CAPTURE.format(handler_type=handler.expected_content, url=response.url))
            else:
                self.api._logger.debug(CFG.LOGS.HANDLER_REJECTED.format(handler_type=handler.expected_content, url=response.url, content_type=response.headers.get('content-type', CFG.PARAMETERS.DEFAULT_CONTENT_TYPE)))
        
        # Если есть хендлеры для захвата, обрабатываем ответ один раз
        if capturing_handlers:
            await self._handle_captured_response(capturing_handlers, response, request, response_time)
        else:
            self._handle_rejected_response(response, request, response_time)
            self.api._logger.debug(CFG.LOGS.ALL_HANDLERS_REJECTED.format(url=response.url))

        # Проверяем, завершены ли все хандлеры
        self._check_completion()
        
        # Возвращаем оригинальный ответ
        await route.fulfill(response=response)
    
    async def _handle_captured_response(self, handlers: List[Handler], response, request, response_time: float):
        """Обрабатывает захваченный response для множественных хандлеров оптимально"""
        try:
            # Получаем тело ответа ТОЛЬКО ОДИН РАЗ
            raw_data = await response.body()

            content_type = response.headers.get("content-type", "").lower()
            parsed_data = parse_response_data(raw_data, content_type)
            
            # Создаем Response объект для каждого хендлера
            result = Response(
                status=response.status,
                request_headers=request.headers,
                response_headers=response.headers,
                response=parsed_data,  # Переиспользуем уже распарсенные данные
                duration=response_time - self.start_time,
                url=response.url
            )

            for handler in handlers:    
                # Добавляем результат к хандлеру
                self.handler_results[handler.slug].append(result)
                
                max_responses_text = handler.max_responses or CFG.LOGS.UNLIMITED_SIZE
                self.api._logger.info(CFG.LOGS.HANDLER_CAPTURED_RESPONSE.format(
                    handler_type=handler.expected_content,
                    url=response.url,
                    current_count=len(self.handler_results[handler.slug]),
                    max_responses=max_responses_text
                ))
                
        except Exception as e:
            # Если произошла ошибка, логируем для всех хендлеров
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

    def _handle_rejected_response(self, response, request, response_time: float):
        """Обрабатывает отклоненный response"""
        # Сохраняем отклоненные ответы для анализа
        duration = response_time - self.start_time
        self.rejected_responses.append(Response(
            status=response.status,
            request_headers=request.headers,
            response_headers=response.headers,
            response=None,
            duration=duration,
            url=response.url
        ))
    
    def _check_completion(self):
        """Проверяет, завершены ли все хандлеры"""
        if self.completion_future.done():
            return
            
        # Проверяем каждый хандлер
        all_completed = True
        for handler in self.handlers:
            if handler.slug in self.handler_errors:
                continue  # Уже завершен с ошибкой
                
            # Если хандлер достиг лимита ответов, он завершен
            if handler.max_responses is not None and len(self.handler_results[str(handler.slug)]) >= handler.max_responses:
                continue
            
            # Если хандлер еще не завершен, продолжаем ожидание
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
            elif self.handler_results[handler.slug]:
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
                if self.handler_results[str(handler.slug)]:
                    result.append(HandlerSearchSuccess(
                        responses=self.handler_results[handler.slug],
                        duration=duration,
                        handler_slug=handler.slug
                    ))
                else:
                    result.append(HandlerSearchFailed(
                        rejected_responses=self.rejected_responses,
                        duration=duration,
                        handler_slug=handler.slug
                    ))

            return result


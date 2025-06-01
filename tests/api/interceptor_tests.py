import pytest
from standard_open_inflation_package import BaseAPI, Handler, Response, NetworkError, Request, HandlerSearchFailedError, HttpMethod, Page, parse_content_type
from io import BytesIO
from asyncio.exceptions import TimeoutError


# Тестовые страницы, которые загружают различные типы ресурсов как субфайлы
CHECK_HTML_PAGE = "https://httpbin.org/"
CHECK_JSON_PAGE = "https://google.com/"  # Страница с AJAX запросами JSON
CHECK_IMAGE_PAGE = "https://picsum.photos/"  # Страница с изображениями
CHECK_CSS_PAGE = "https://youtube.com/"  # Страница с CSS файлами
CHECK_JS_PAGE = "https://ya.ru/"  # Страница с JavaScript файлами
CHECK_VIDEO_PAGE = "https://github.com/home"  # Страница с видео
CHECK_AUDIO_PAGE = "https://developer.mozilla.org/ru/docs/Web/HTML/Reference/Elements/audio"  # Страница с аудио
CHECK_FONT_PAGE = "https://fonts.google.com/"  # Страница с веб-шрифтами
CHECK_TEXT_PAGE = "https://google.com/"  # Прямая ссылка на текстовый файл

TIMEOUT = 15.0  # Оптимальный таймаут для параллельного выполнения


@pytest.mark.asyncio
async def test_interceptor_html():
    api = BaseAPI(timeout=TIMEOUT)
    await api.new_session()

    result = await api.new_direct_fetch(CHECK_HTML_PAGE, handler=Handler.MAIN())
    standard_check(result, str)
    assert result.response.startswith("<!DOCTYPE html>"), "Response should start with HTML doctype"

    await api.close()

@pytest.mark.asyncio
async def test_interceptor_json():
    api = BaseAPI(timeout=TIMEOUT)
    await api.new_session()
    
    result = await api.new_direct_fetch(CHECK_JSON_PAGE, handler=Handler.JSON())
    standard_check(result, (dict, list))

    await api.close()

@pytest.mark.asyncio
async def test_interceptor_js():
    api = BaseAPI(timeout=TIMEOUT)
    await api.new_session()

    result = await api.new_direct_fetch(CHECK_JS_PAGE, handler=Handler.JS())
    standard_check(result, str)

    await api.close()

@pytest.mark.asyncio
async def test_interceptor_css():
    api = BaseAPI(timeout=TIMEOUT)
    await api.new_session()

    result = await api.new_direct_fetch(CHECK_CSS_PAGE, handler=Handler.CSS())
    standard_check(result, str)

    await api.close()

@pytest.mark.asyncio
async def test_interceptor_image():
    api = BaseAPI(timeout=TIMEOUT)
    await api.new_session()

    result = await api.new_direct_fetch(CHECK_IMAGE_PAGE, handler=Handler.IMAGE())
    standard_check(result, BytesIO)

    await api.close()

@pytest.mark.asyncio
async def test_interceptor_video():
    api = BaseAPI(timeout=TIMEOUT)
    await api.new_session()

    result = await api.new_direct_fetch(CHECK_VIDEO_PAGE, handler=Handler.VIDEO())
    standard_check(result, BytesIO)

    await api.close()

@pytest.mark.asyncio
async def test_interceptor_audio():
    api = BaseAPI(timeout=TIMEOUT)
    await api.new_session()

    result = await api.new_direct_fetch(CHECK_AUDIO_PAGE, handler=Handler.AUDIO())
    standard_check(result, BytesIO)

    await api.close()

@pytest.mark.asyncio
async def test_interceptor_font():
    api = BaseAPI(timeout=TIMEOUT)
    await api.new_session()

    result = await api.new_direct_fetch(CHECK_FONT_PAGE, handler=Handler.FONT())
    standard_check(result, BytesIO)

    await api.close()

@pytest.mark.asyncio
async def test_interceptor_text():
    api = BaseAPI(timeout=TIMEOUT)
    await api.new_session()

    result = await api.new_direct_fetch(CHECK_TEXT_PAGE, handler=Handler.TEXT())
    standard_check(result, str)

    await api.close()

@pytest.mark.asyncio
async def test_interceptor_any():
    api = BaseAPI(timeout=TIMEOUT)
    await api.new_session()

    result = await api.new_direct_fetch(CHECK_HTML_PAGE, handler=Handler.ANY())
    standard_check(result, (dict, str, BytesIO))

    await api.close()

@pytest.mark.asyncio
async def test_interceptor_nonexistent_url():
    api = BaseAPI(timeout=TIMEOUT)
    await api.new_session()

    result = await api.new_direct_fetch(CHECK_HTML_PAGE, handler=Handler.NONE())

    assert isinstance(result, HandlerSearchFailedError), "Result should be an instance of HandlerSearchFailedError"
    assert len(result.rejected_responses) > 0, "There should be rejected responses"
    assert abs(result.duration-TIMEOUT) < 1, "Duration should match the timeout"
    
    resp = []
    for response in result.rejected_responses:
        d = parse_content_type(response.response_headers.get('content-type', 'unknown'))
        resp.append(d["content_type"])

    api._logger.info(f"Rejected responses: {', '.join(resp)}")

    await api.close()

def standard_check(result: Response | HandlerSearchFailedError, expected_type: type | tuple):
    assert isinstance(result, Response), "Result should be an instance of Response"
    assert str(result.status).startswith("2"), f"Expected status 2xx, got {result.status}"
    assert isinstance(result.response, expected_type), f"Response should be a {expected_type}"

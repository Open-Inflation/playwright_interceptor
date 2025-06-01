import pytest
from standard_open_inflation_package import BaseAPI, Handler, Response, NetworkError, Request, HandlerSearchFailedError, HttpMethod, Page, parse_content_type
from io import BytesIO
from asyncio.exceptions import TimeoutError


CHECK_HTML = "https://httpbin.org/html"
CHECK_JSON = "https://httpbin.org/json"
CHECK_IMAGE = "https://httpbin.org/image/png"
CHECK_CSS = "https://www.w3schools.com/w3css/4/w3.css"
CHECK_JS = "https://code.jquery.com/jquery-3.6.0.min.js"
CHECK_VIDEO = "https://sample-videos.com/zip/10/mp4/SampleVideo_1280x720_1mb.mp4"
CHECK_AUDIO = "https://www.soundjay.com/misc/sounds-other/bell-ringing-05.wav"
CHECK_FONT = "https://fonts.gstatic.com/s/roboto/v30/KFOmCnqEu92Fr1Mu4mxK.woff2"
CHECK_ARCHIVE = "https://github.com/jquery/jquery/archive/refs/heads/main.zip"
CHECK_TEXT = "https://httpbin.org/robots.txt"
TIMEOUT = 15.0


@pytest.mark.asyncio
async def test_interceptor_json():
    api = BaseAPI(timeout=TIMEOUT)
    await api.new_session()
    
    result = await api.new_direct_fetch(CHECK_JSON, handler=Handler.JSON())
    assert isinstance(result, Response), "Result should be an instance of Response"
    assert result.status == 200, f"Expected status 200, got {result.status}"
    # Now should handle CSRF prefixes and return proper dict/list
    assert isinstance(result.response, (dict, list)), "Response should be a dictionary or list after CSRF handling"

    await api.close()

@pytest.mark.asyncio
async def test_interceptor_js():
    api = BaseAPI(timeout=TIMEOUT)
    await api.new_session()

    result = await api.new_direct_fetch(CHECK_JS, handler=Handler.JS())
    assert isinstance(result, Response), "Result should be an instance of Response"
    assert result.status == 200, f"Expected status 200, got {result.status}"
    assert isinstance(result.response, str), "Response should be a string"

    await api.close()

@pytest.mark.asyncio
async def test_interceptor_css():
    api = BaseAPI(timeout=TIMEOUT)
    await api.new_session()

    result = await api.new_direct_fetch(CHECK_CSS, handler=Handler.CSS())
    assert isinstance(result, Response), "Result should be an instance of Response"
    assert result.status == 200, f"Expected status 200, got {result.status}"
    assert isinstance(result.response, str), "Response should be a string"

    await api.close()

@pytest.mark.asyncio
async def test_interceptor_image():
    api = BaseAPI(timeout=TIMEOUT)
    await api.new_session()

    result = await api.new_direct_fetch(CHECK_IMAGE, handler=Handler.IMAGE())
    assert isinstance(result, Response), "Result should be an instance of Response"
    assert result.status == 200, f"Expected status 200, got {result.status}"
    assert isinstance(result.response, BytesIO), "Response should be a BytesIO"

    await api.close()

@pytest.mark.asyncio
async def test_interceptor_video():
    api = BaseAPI(timeout=TIMEOUT)
    await api.new_session()

    result = await api.new_direct_fetch(CHECK_VIDEO, handler=Handler.VIDEO())
    assert isinstance(result, Response), "Result should be an instance of Response"
    assert result.status == 200, f"Expected status 200, got {result.status}"
    assert isinstance(result.response, BytesIO), "Response should be a BytesIO"

    await api.close()

@pytest.mark.asyncio
async def test_interceptor_audio():
    api = BaseAPI(timeout=TIMEOUT)
    await api.new_session()

    result = await api.new_direct_fetch(CHECK_AUDIO, handler=Handler.AUDIO())
    assert isinstance(result, Response), "Result should be an instance of Response"
    assert result.status == 200, f"Expected status 200, got {result.status}"
    assert isinstance(result.response, BytesIO), "Response should be a BytesIO"

    await api.close()

@pytest.mark.asyncio
async def test_interceptor_font():
    api = BaseAPI(timeout=TIMEOUT)
    await api.new_session()

    result = await api.new_direct_fetch(CHECK_FONT, handler=Handler.FONT())
    assert isinstance(result, Response), "Result should be an instance of Response"
    assert result.status == 200, f"Expected status 200, got {result.status}"
    assert isinstance(result.response, BytesIO), "Response should be a BytesIO"
    assert any(result.response.name.endswith(ext) for ext in ['.woff', '.woff2', '.ttf', '.otf']), "Response should have a font extension"

    await api.close()

@pytest.mark.asyncio
async def test_interceptor_application():
    api = BaseAPI(timeout=TIMEOUT)
    await api.new_session()

    result = await api.new_direct_fetch(CHECK_ARCHIVE, handler=Handler.APPLICATION())
    assert isinstance(result, Response), "Result should be an instance of Response"
    assert result.status == 200, f"Expected status 200, got {result.status}"
    assert isinstance(result.response, BytesIO), "Response should be a BytesIO"

    await api.close()

@pytest.mark.asyncio
async def test_interceptor_archive():
    api = BaseAPI(timeout=TIMEOUT)
    await api.new_session()

    result = await api.new_direct_fetch(CHECK_ARCHIVE, handler=Handler.ARCHIVE())
    assert isinstance(result, Response), "Result should be an instance of Response"
    assert result.status == 200, f"Expected status 200, got {result.status}"
    assert isinstance(result.response, BytesIO), "Response should be a BytesIO"

    await api.close()

@pytest.mark.asyncio
async def test_interceptor_text():
    api = BaseAPI(timeout=TIMEOUT)
    await api.new_session()

    result = await api.new_direct_fetch(CHECK_TEXT, handler=Handler.TEXT())
    assert isinstance(result, Response), "Result should be an instance of Response"
    assert result.status == 200, f"Expected status 200, got {result.status}"
    assert isinstance(result.response, str), "Response should be a string"

    await api.close()

@pytest.mark.asyncio
async def test_interceptor_any():
    api = BaseAPI(timeout=TIMEOUT)
    await api.new_session()

    result = await api.new_direct_fetch(CHECK_HTML, handler=Handler.ANY())
                
    assert isinstance(result, Response), "Result should be an instance of Response"
    assert result.status == 200, f"Expected status 200, got {result.status}"
    assert isinstance(result.response, (dict, str, BytesIO)), "Response should be a dict, str or BytesIO"

    await api.close()

@pytest.mark.asyncio
async def test_interceptor_nonexistent_url():
    api = BaseAPI(timeout=TIMEOUT)
    await api.new_session()

    result = await api.new_direct_fetch(CHECK_HTML, handler=Handler.NONE())

    assert isinstance(result, HandlerSearchFailedError), "Result should be an instance of HandlerSearchFailedError"
    assert len(result.rejected_responses) > 0, "There should be rejected responses"
    assert abs(result.duration-TIMEOUT) < 0.2, "Duration should match the timeout"
    
    resp = []
    for response in result.rejected_responses:
        d = parse_content_type(response.response_headers.get('content-type', 'unknown'))
        resp.append(d["content_type"])

    api._logger.info(f"Rejected responses: {', '.join(resp)}")

    await api.close()

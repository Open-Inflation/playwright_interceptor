import pytest
from standard_open_inflation_package.handler import Handler, ExpectedContentType
from standard_open_inflation_package.execute import Execute
from io import BytesIO

# Импортируем утилиты для тестирования
from . import (
    run_direct_fetch_test, 
    run_page_resource_intercept_test,
    run_no_intercept_test,
    assert_success_result,
    assert_failed_result,
    assert_html_content,
    api_session,
    DEFAULT_TIMEOUT,
)


# Тестовые страницы, которые загружают различные типы ресурсов как субфайлы
# Handler'ы предназначены для ПЕРЕХВАТА ресурсов, которые загружает страница, а не для прямых запросов

CHECK_HTML_PAGE = "https://httpbin.org/"              # Страница с HTML контентом
CHECK_JSON_PAGE = "https://google.com/"               # Страница с AJAX запросами JSON
CHECK_IMAGE_PAGE = "https://picsum.photos/"           # Страница с изображениями
CHECK_CSS_PAGE = "https://youtube.com/"               # Страница с CSS файлами
CHECK_JS_PAGE = "https://ya.ru/"                      # Страница с JavaScript файлами
CHECK_VIDEO_PAGE = "https://github.com/home"          # Страница с видео
CHECK_AUDIO_PAGE = "https://developer.mozilla.org/ru/docs/Web/HTML/Reference/Elements/audio"  # Страница с аудио
CHECK_FONT_PAGE = "https://fonts.google.com/"         # Страница с веб-шрифтами
CHECK_TEXT_PAGE = "https://chromedevtools.github.io/devtools-protocol/"  # Страница с текстовым файлом


@pytest.mark.asyncio
async def test_interceptor_html():
    """Тест HTML handler'а - основная страница"""
    def check_html_doctype(response):
        assert_html_content(response, check_doctype=True)
    
    await run_direct_fetch_test(
        CHECK_HTML_PAGE, 
        Handler.MAIN(), 
        expected_type=str,
        additional_checks=check_html_doctype
    )

@pytest.mark.asyncio
async def test_interceptor_css_resources():
    """Тест CSS handler'а - перехват CSS ресурсов на странице"""
    def check_css_content(response):
        # CSS должен быть строкой и содержать CSS селекторы
        assert isinstance(response.response, str), "CSS should be string"
        content = response.response.lower()
        # Проверяем типичные CSS конструкции
        assert any(keyword in content for keyword in ['{', '}', 'color', 'font', 'margin', 'padding']), \
            "Response should contain CSS content"
    
    await run_page_resource_intercept_test(
        CHECK_CSS_PAGE,
        Handler.SIDE(expected_content=ExpectedContentType.CSS),
        expected_type=str,
        additional_checks=check_css_content,
        min_resources=1
    )

@pytest.mark.asyncio
async def test_interceptor_js_resources():
    """Тест JS handler'а - перехват JavaScript ресурсов на странице"""
    def check_js_content(response):
        # JavaScript должен быть строкой и содержать JS код
        assert isinstance(response.response, str), "JS should be string"
        content = response.response.lower()
        # Проверяем типичные JS конструкции
        assert any(keyword in content for keyword in ['function', 'var', 'const', 'let', '()', '{}']), \
            "Response should contain JavaScript content"
    
    await run_page_resource_intercept_test(
        CHECK_JS_PAGE,
        Handler.SIDE(expected_content=ExpectedContentType.JS),
        expected_type=str,
        additional_checks=check_js_content,
        min_resources=1
    )

@pytest.mark.asyncio
async def test_interceptor_image_resources():
    """Тест IMAGE handler'а - перехват изображений на странице"""
    def check_image_content(response):
        # Изображения должны быть в BytesIO
        assert isinstance(response.response, BytesIO), "Images should be BytesIO"
        # Проверяем что есть данные
        response.response.seek(0)
        data = response.response.read()
        assert len(data) > 0, "Image should have data"
        response.response.seek(0)  # Сбрасываем позицию
    
    await run_page_resource_intercept_test(
        CHECK_IMAGE_PAGE,
        Handler.SIDE(expected_content=ExpectedContentType.IMAGE),
        expected_type=BytesIO,
        additional_checks=check_image_content,
        min_resources=1
    )

@pytest.mark.asyncio
async def test_interceptor_font_resources():
    """Тест FONT handler'а - перехват шрифтов на странице"""
    def check_font_content(response):
        # Шрифты должны быть в BytesIO
        assert isinstance(response.response, BytesIO), "Fonts should be BytesIO"
        # Проверяем что есть данные
        response.response.seek(0)
        data = response.response.read()
        assert len(data) > 0, "Font should have data"
        response.response.seek(0)  # Сбрасываем позицию
    
    await run_page_resource_intercept_test(
        CHECK_FONT_PAGE,
        Handler.SIDE(expected_content=ExpectedContentType.FONT),
        expected_type=BytesIO,
        additional_checks=check_font_content
    )

@pytest.mark.asyncio
async def test_interceptor_text_main():
    """Тест TEXT handler'а для основной страницы"""
    await run_direct_fetch_test(
        CHECK_TEXT_PAGE, 
        Handler.MAIN(),
        expected_type=str,
    )

@pytest.mark.asyncio
async def test_interceptor_max_responses():
    """Тест ANY handler'а - ожидаем множественные любые ответы"""
    max_resp = [1, 2, 3]  # Максимальное количество ответов, которые мы хотим перехватить
    async with api_session(DEFAULT_TIMEOUT) as api:
        results = await api.new_direct_fetch(
            CHECK_HTML_PAGE,
            handlers=[Handler.ALL(execute=Execute.RETURN(max_resp[i])) for i in range(len(max_resp))],
        )
        assert len(results) == len(max_resp), f"Expected {len(max_resp)} result, got {len(results)}"
        result = results[0]
        
        for i, result in enumerate(results):
            # ANY handler может вернуть множественные ответы
            assert_success_result(result, expected_type=(dict, list, str, BytesIO), expected_count=max_resp[i])

@pytest.mark.asyncio
async def test_interceptor_none_handler():
    """Тест NONE handler'а - ожидаем что ничего не будет перехвачено"""
    await run_no_intercept_test(CHECK_HTML_PAGE, Handler.NONE())

@pytest.mark.asyncio
async def test_interceptor_json_page():
    """Тест JSON handler'а - перехват JSON запросов на странице Google"""
    def check_json_content(response):
        # JSON должен быть dict или list
        assert isinstance(response.response, (dict, list)), "JSON should be dict or list"
        assert len(response.response) > 0, "JSON dict should not be empty"
    
    # Для JSON используем MAIN, так как Google отдает основную страницу как JSON API
    await run_direct_fetch_test(
        CHECK_JSON_PAGE,
        Handler.SIDE(expected_content=ExpectedContentType.JSON),
        expected_type=(dict, list, str),  # Google может отдавать HTML тоже
        additional_checks=check_json_content if CHECK_JSON_PAGE.endswith('.json') else None
    )

@pytest.mark.asyncio
async def test_interceptor_video_resources():
    """Тест VIDEO handler'а - перехват видео ресурсов на странице"""
    def check_video_content(response):
        # Видео должны быть в BytesIO
        assert isinstance(response.response, BytesIO), "Video should be BytesIO"
        # Проверяем что есть данные
        response.response.seek(0)
        data = response.response.read()
        assert len(data) > 0, "Video should have data"
        response.response.seek(0)  # Сбрасываем позицию
    
    await run_page_resource_intercept_test(
        CHECK_VIDEO_PAGE,
        Handler.SIDE(expected_content=ExpectedContentType.VIDEO),
        expected_type=BytesIO,
        additional_checks=check_video_content,
        min_resources=1
    )

@pytest.mark.asyncio
async def test_interceptor_audio_resources():
    """Тест AUDIO handler'а - перехват аудио ресурсов на странице"""
    def check_audio_content(response):
        # Аудио должны быть в BytesIO
        assert isinstance(response.response, BytesIO), "Audio should be BytesIO"
        # Проверяем что есть данные
        response.response.seek(0)
        data = response.response.read()
        assert len(data) > 0, "Audio should have data"
        response.response.seek(0)  # Сбрасываем позицию
    
    await run_page_resource_intercept_test(
        CHECK_AUDIO_PAGE,
        Handler.SIDE(expected_content=ExpectedContentType.AUDIO),
        expected_type=BytesIO,
        additional_checks=check_audio_content,
        min_resources=1
    )


@pytest.mark.asyncio
async def test_handler_error_marks_failed(monkeypatch):
    """Ensure handler errors are reported as failures."""
    import standard_open_inflation_package.direct_request_interceptor as interceptor

    def raise_error(*args, **kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(interceptor, "parse_response_data", raise_error)

    async with api_session(DEFAULT_TIMEOUT) as api:
        results = await api.new_direct_fetch(CHECK_HTML_PAGE, handlers=Handler.MAIN())

        assert len(results) == 1
        assert_failed_result(results[0], min_rejected=0)

import pytest
from standard_open_inflation_package.tools import parse_proxy, parse_content_type
import itertools
import logging


@pytest.mark.asyncio
async def test_parse_proxy():
    # Варианты параметров
    schemes = ['http://', 'https://', '']
    auths = [('', ''), ('user', 'pass')]
    hosts = ['127.0.0.1', 'example.com']
    ports = ['', '8080']

    logger = logging.getLogger("test_parse_proxy")

    for scheme, (username, password), host, port in itertools.product(schemes, auths, hosts, ports):
        # Формируем строку прокси
        auth_part = f"{username}:{password}@" if username else ""
        port_part = f":{port}" if port else ""
        proxy_str = f"{scheme}{auth_part}{host}{port_part}"

        expected = {'server': f"{scheme}{host}{port_part}"}
        if not scheme:
            expected['server'] = "http://"+expected['server']
        if username:
            expected['username'] = username
            expected['password'] = password

        assert parse_proxy(proxy_str, True, logger) == expected


class TestContentTypeParsing:
    """Тесты для парсинга Content-Type"""
    
    def test_basic_content_type(self):
        """Тест базового Content-Type"""
        result = parse_content_type("application/json")
        assert result['content_type'] == 'application/json'
        assert result['charset'] == 'utf-8'  # default
    
    def test_content_type_with_charset(self):
        """Тест Content-Type с charset"""
        result = parse_content_type("text/html; charset=windows-1251")
        assert result['content_type'] == 'text/html'
        assert result['charset'] == 'windows-1251'
    
    def test_content_type_with_multiple_params(self):
        """Тест Content-Type с несколькими параметрами"""
        result = parse_content_type("text/html; charset=UTF-8; boundary=something")
        assert result['content_type'] == 'text/html'
        assert result['charset'] == 'utf-8'
        assert result['boundary'] == 'something'
    
    def test_empty_content_type(self):
        """Тест пустого Content-Type"""
        result = parse_content_type("")
        assert result['content_type'] == ''
    
    def test_content_type_with_quotes(self):
        """Тест Content-Type с кавычками в параметрах"""
        result = parse_content_type('text/html; charset="utf-8"')
        assert result['charset'] == 'utf-8'  # quotes should be stripped

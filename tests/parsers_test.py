import pytest
from standard_open_inflation_package.parsers import parse_response_data, parse_content_type, _remove_csrf_prefixes
import json
from io import BytesIO


class TestCSRFRemoval:
    """Тесты для универсального удаления CSRF-префиксов"""
    
    def test_google_style_prefixes(self):
        """Тест Google-стиля префиксов"""
        test_cases = [
            (")]}'\\n{\"data\": \"test\"}", {"data": "test"}),
            (")]}{\"data\": \"test\"}", {"data": "test"}),
        ]
        
        for input_data, expected in test_cases:
            result = parse_response_data(input_data, "application/json")
            assert result == expected, f"Failed for input: {input_data}"
    
    def test_facebook_style_prefixes(self):
        """Тест Facebook-стиля префиксов"""
        test_cases = [
            ("while(1);{\"data\": \"test\"}", {"data": "test"}),
            ("for(;;);{\"data\": \"test\"}", {"data": "test"}),
        ]
        
        for input_data, expected in test_cases:
            result = parse_response_data(input_data, "application/json")
            assert result == expected, f"Failed for input: {input_data}"
    
    def test_unknown_prefixes(self):
        """Тест неизвестных CSRF-префиксов"""
        test_cases = [
            ('SECURITY_PREFIX_123{"data": "test"}', {"data": "test"}),
            ('/*some comment*/{"data": "test"}', {"data": "test"}),
            ('random_text_here{"data": "test"}', {"data": "test"}),
            ('12345{"data": "test"}', {"data": "test"}),
            ('🔒SECURITY🔒{"data": "test"}', {"data": "test"}),
            (';;;;;;;{"data": "test"}', {"data": "test"}),
        ]
        
        for input_data, expected in test_cases:
            result = parse_response_data(input_data, "application/json")
            assert result == expected, f"Failed for input: {input_data}"
    
    def test_array_responses(self):
        """Тест массивов с CSRF-префиксами"""
        test_cases = [
            (')]}\\\'\\n[1,2,3]', [1,2,3]),
            ('prefix[{"a":1},{"b":2}]', [{"a":1},{"b":2}]),
            (')]}\\\'\\n[[[["test"]]]]', [[[["test"]]]]),
        ]
        
        for input_data, expected in test_cases:
            result = parse_response_data(input_data, "application/json")
            assert result == expected, f"Failed for input: {input_data}"
    
    def test_complex_structures(self):
        """Тест сложных JSON структур"""
        test_cases = [
            (')]}\\\'\\n{"nested": {"data": [1,2,3]}}', {"nested": {"data": [1,2,3]}}),
            ('prefix{"users": [{"id": 1, "name": "John"}]}', {"users": [{"id": 1, "name": "John"}]}),
        ]
        
        for input_data, expected in test_cases:
            result = parse_response_data(input_data, "application/json")
            assert result == expected, f"Failed for input: {input_data}"
    
    def test_no_prefix(self):
        """Тест JSON без префиксов"""
        test_cases = [
            ('{"data": "test"}', {"data": "test"}),
            ('[1,2,3]', [1,2,3]),
        ]
        
        for input_data, expected in test_cases:
            result = parse_response_data(input_data, "application/json")
            assert result == expected, f"Failed for input: {input_data}"
    
    def test_with_spaces(self):
        """Тест с пробелами в начале"""
        test_cases = [
            ('  )]"}\'\\n  {"data": "test"}', {"data": "test"}),
            ('\\t\\n  prefix{"data": "test"}', {"data": "test"}),
        ]
        
        for input_data, expected in test_cases:
            result = parse_response_data(input_data, "application/json")
            assert result == expected, f"Failed for input: {input_data}"
    
    def test_bytes_input(self):
        """Тест с bytes на входе"""
        input_data = b')]}\\\'\\n{"data": "test"}'
        expected = {"data": "test"}
        result = parse_response_data(input_data, "application/json")
        assert result == expected
    
    def test_multiple_json_objects(self):
        """Тест что возвращается первый валидный JSON"""
        input_data = 'prefix{"first": 1}{"second": 2}'
        result = parse_response_data(input_data, "application/json")
        assert result == {"first": 1}
    
    def test_malformed_json(self):
        """Тест обработки невалидного JSON"""
        input_data = 'prefix{invalid json}'
        result = parse_response_data(input_data, "application/json")
        assert isinstance(result, str)  # Should return as string
        assert result == input_data
    
    def test_no_json_found(self):
        """Тест когда JSON не найден в ответе"""
        input_data = 'just some text without json'
        result = parse_response_data(input_data, "application/json")
        assert result == input_data  # Should return original string


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
        result = parse_content_type("text/html; charset=utf-8; boundary=something")
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


class TestResponseDataParsing:
    """Тесты для парсинга различных типов данных ответа"""
    
    def test_json_parsing(self):
        """Тест парсинга JSON данных"""
        data = '{"key": "value"}'
        result = parse_response_data(data, "application/json")
        assert result == {"key": "value"}
    
    def test_text_parsing(self):
        """Тест парсинга текстовых данных"""
        data = "Hello, world!"
        result = parse_response_data(data, "text/plain")
        assert result == "Hello, world!"
    
    def test_binary_data_parsing(self):
        """Тест парсинга бинарных данных"""
        data = b"\\x89PNG\\r\\n\\x1a\\n"  # PNG header
        result = parse_response_data(data, "image/png")
        assert isinstance(result, BytesIO)
        assert result.name.endswith('.png')
    
    def test_bytes_to_string_conversion(self):
        """Тест конвертации bytes в string"""
        data = b"Hello, world!"
        result = parse_response_data(data, "text/plain")
        assert result == "Hello, world!"
    
    def test_unicode_handling(self):
        """Тест обработки Unicode"""
        data = "Привет, мир! 🌍"
        result = parse_response_data(data, "text/plain")
        assert result == "Привет, мир! 🌍"


class TestCSRFPrefixFunction:
    """Тесты для внутренней функции _remove_csrf_prefixes"""
    
    def test_direct_csrf_removal(self):
        """Прямое тестирование функции удаления CSRF"""
        test_cases = [
            (')]}\\\'\\n{"test": true}', '{"test": true}'),
            ('while(1);[1,2,3]', '[1,2,3]'),
            ('prefix{"data": "value"}', '{"data": "value"}'),
            ('{"clean": "json"}', '{"clean": "json"}'),  # no prefix
        ]
        
        for input_text, expected in test_cases:
            result = _remove_csrf_prefixes(input_text)
            # Parse both to ensure they're equivalent JSON
            assert json.loads(result) == json.loads(expected)


if __name__ == "__main__":
    pytest.main([__file__])

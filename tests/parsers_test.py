import pytest
from playwright_interceptor.content_loader import parse_response_data, _remove_csrf_prefixes
import json
from io import BytesIO


class TestCSRFRemoval:
    """Tests for universal CSRF prefix removal"""
    
    def test_google_style_prefixes(self):
        """Test Google-style prefixes"""
        test_cases = [
            (")]}'\\n{\"data\": \"test\"}", {"data": "test"}),
            (")]}{\"data\": \"test\"}", {"data": "test"}),
        ]
        
        for input_data, expected in test_cases:
            result = parse_response_data(input_data, "application/json")
            assert result == expected, f"Failed for input: {input_data}"
    
    def test_facebook_style_prefixes(self):
        """Test Facebook-style prefixes"""
        test_cases = [
            ("while(1);{\"data\": \"test\"}", {"data": "test"}),
            ("for(;;);{\"data\": \"test\"}", {"data": "test"}),
        ]
        
        for input_data, expected in test_cases:
            result = parse_response_data(input_data, "application/json")
            assert result == expected, f"Failed for input: {input_data}"
    
    def test_unknown_prefixes(self):
        """Test unknown CSRF prefixes"""
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
        """Test arrays with CSRF prefixes"""
        test_cases = [
            (')]}\\\'\\n[1,2,3]', [1,2,3]),
            ('prefix[{"a":1},{"b":2}]', [{"a":1},{"b":2}]),
            (')]}\\\'\\n[[[["test"]]]]', [[[["test"]]]]),
        ]
        
        for input_data, expected in test_cases:
            result = parse_response_data(input_data, "application/json")
            assert result == expected, f"Failed for input: {input_data}"
    
    def test_complex_structures(self):
        """Test complex JSON structures"""
        test_cases = [
            (')]}\\\'\\n{"nested": {"data": [1,2,3]}}', {"nested": {"data": [1,2,3]}}),
            ('prefix{"users": [{"id": 1, "name": "John"}]}', {"users": [{"id": 1, "name": "John"}]}),
        ]
        
        for input_data, expected in test_cases:
            result = parse_response_data(input_data, "application/json")
            assert result == expected, f"Failed for input: {input_data}"
    
    def test_no_prefix(self):
        """Test JSON without prefixes"""
        test_cases = [
            ('{"data": "test"}', {"data": "test"}),
            ('[1,2,3]', [1,2,3]),
        ]
        
        for input_data, expected in test_cases:
            result = parse_response_data(input_data, "application/json")
            assert result == expected, f"Failed for input: {input_data}"
    
    def test_with_spaces(self):
        """Test with leading spaces"""
        test_cases = [
            ('  )]"}\'\\n  {"data": "test"}', {"data": "test"}),
            ('\\t\\n  prefix{"data": "test"}', {"data": "test"}),
        ]
        
        for input_data, expected in test_cases:
            result = parse_response_data(input_data, "application/json")
            assert result == expected, f"Failed for input: {input_data}"
    
    def test_bytes_input(self):
        """Test with bytes input"""
        input_data = b')]}\\\'\\n{"data": "test"}'
        expected = {"data": "test"}
        result = parse_response_data(input_data, "application/json")
        assert result == expected
    
    def test_multiple_json_objects(self):
        """Test that first valid JSON is returned"""
        input_data = 'prefix{"first": 1}{"second": 2}'
        result = parse_response_data(input_data, "application/json")
        assert result == {"first": 1}
    
    def test_malformed_json(self):
        """Test handling of invalid JSON"""
        input_data = 'prefix{invalid json}'
        result = parse_response_data(input_data, "application/json")
        assert isinstance(result, str)  # Should return as string
        assert result == input_data
    
    def test_no_json_found(self):
        """Test when JSON is not found in response"""
        input_data = 'just some text without json'
        result = parse_response_data(input_data, "application/json")
        assert result == input_data  # Should return original string


class TestResponseDataParsing:
    """Tests for parsing various response data types"""
    
    def test_json_parsing(self):
        """Test JSON data parsing"""
        data = '{"key": "value"}'
        result = parse_response_data(data, "application/json")
        assert result == {"key": "value"}
    
    def test_text_parsing(self):
        """Test text data parsing"""
        data = "Hello, world!"
        result = parse_response_data(data, "text/plain")
        assert result == "Hello, world!"
    
    def test_binary_data_parsing(self):
        """Test binary data parsing"""
        data = b"\\x89PNG\\r\\n\\x1a\\n"  # PNG header
        result = parse_response_data(data, "image/png")
        assert isinstance(result, BytesIO)
        assert result.name.endswith('.png')
    
    def test_bytes_to_string_conversion(self):
        """Test bytes to string conversion"""
        data = b"Hello, world!"
        result = parse_response_data(data, "text/plain")
        assert result == "Hello, world!"
    
    def test_unicode_handling(self):
        """Test Unicode handling"""
        data = "Привет, мир! 🌍"
        result = parse_response_data(data, "text/plain")
        assert result == "Привет, мир! 🌍"


class TestCSRFPrefixFunction:
    """Tests for internal _remove_csrf_prefixes function"""
    
    def test_direct_csrf_removal(self):
        """Direct testing of CSRF removal function"""
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

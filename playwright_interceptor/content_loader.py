import json
from typing import Union
from io import BytesIO
from beartype import beartype
from . import config as CFG
from .tools import parse_content_type


@beartype
def _remove_csrf_prefixes(text: str) -> str:
    """
    Universally removes CSRF prefixes from JSON responses.
    
    Principle: find the first valid JSON object/array in the string,
    ignoring any CSRF prefixes.
    """
    # Remove leading spaces
    text = text.lstrip()
    
    # Find beginning of JSON (object or array)
    json_start_chars = ['{', '[']
    
    for i, char in enumerate(text):
        if char in json_start_chars:
            # Use stack for tracking brackets
            stack = []
            in_string = False
            escaped = False
            
            for j in range(i, len(text)):
                current = text[j]
                
                if escaped:
                    escaped = False
                    continue
                    
                if current == '\\':
                    escaped = True
                    continue
                    
                if current == '"' and not escaped:
                    in_string = not in_string
                    continue
                    
                if in_string:
                    continue
                    
                if current in ['{', '[']:
                    stack.append(current)
                elif current in ['}', ']']:
                    if not stack:
                        break
                    expected = '{' if current == '}' else '['
                    if stack[-1] == expected:
                        stack.pop()
                        if not stack:  # Stack is empty - JSON is complete
                            candidate = text[i:j+1]
                            try:
                                json.loads(candidate)
                                return candidate
                            except json.JSONDecodeError:
                                break
                    else:
                        break
    
    # If no valid JSON found, return original
    return text

@beartype
def parse_response_data(data: Union[str, bytes], content_type: str) -> Union[dict, list, str, BytesIO]:
    """
    Parses response data based on content-type with universal CSRF prefix handling.
    
    Args:
        data: Raw data as string or bytes
        content_type: Content-Type from response headers
    
    Returns:
        Parsed data of appropriate type
    """
    pct = parse_content_type(content_type)

    if pct['content_type'] in CFG.NETWORK.JSON_EXTENSIONS:
        try:
            # Convert bytes to string if needed
            if isinstance(data, bytes):
                text_data = data.decode(pct['charset'], errors='replace')
            else:
                text_data = data
            
            # Universal CSRF prefix removal
            clean_json = _remove_csrf_prefixes(text_data)
            return json.loads(clean_json)
            
        except (json.JSONDecodeError, UnicodeDecodeError):
            # If JSON parsing fails, return as string
            return data.decode(pct['charset'], errors='replace') if isinstance(data, bytes) else data
    
    for types in [
        CFG.NETWORK.IMAGE_EXTENSIONS,
        CFG.NETWORK.VIDEO_EXTENSIONS,
        CFG.NETWORK.AUDIO_EXTENSIONS,
        CFG.NETWORK.FONT_EXTENSIONS,
        CFG.NETWORK.APPLICATION_EXTENSIONS,
        CFG.NETWORK.ARCHIVE_EXTENSIONS
    ]:
        if pct['content_type'] in types:
            # Create BytesIO object for files
            if isinstance(data, bytes):
                parsed_data = BytesIO(data)
            else:
                # If data came as string (shouldn't happen for binary files, but just in case)
                parsed_data = BytesIO(data.encode(pct['charset']))
            
            # Determine extension by content-type
            parsed_data.name = f"file{types[pct['content_type']]}"
            return parsed_data
    
    # For all other types return as text
    if isinstance(data, bytes):
        try:
            return data.decode(pct['charset'])
        except UnicodeDecodeError:
            # If unable to decode, create BytesIO
            return BytesIO(data)
    else:
        return data

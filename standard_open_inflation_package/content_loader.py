import json
from typing import Union
from io import BytesIO
from beartype import beartype
from . import config as CFG
from .tools import parse_content_type


@beartype
def _remove_csrf_prefixes(text: str) -> str:
    """
    Универсально удаляет CSRF-префиксы из JSON ответов.
    
    Принцип: ищем первый валидный JSON объект/массив в строке,
    игнорируя любые CSRF-префиксы.
    """
    # Убираем пробелы в начале
    text = text.lstrip()
    
    # Ищем начало JSON (объект или массив)
    json_start_chars = ['{', '[']
    
    for i, char in enumerate(text):
        if char in json_start_chars:
            # Используем стек для отслеживания скобок
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
                        if not stack:  # Стек пуст - JSON завершен
                            candidate = text[i:j+1]
                            try:
                                json.loads(candidate)
                                return candidate
                            except json.JSONDecodeError:
                                break
                    else:
                        break
    
    # Если не нашли валидный JSON, возвращаем оригинал
    return text

@beartype
def parse_response_data(data: Union[str, bytes], content_type: str) -> Union[dict, list, str, BytesIO]:
    """
    Парсит данные ответа на основе content-type с универсальной обработкой CSRF-префиксов.
    
    Args:
        data: Сырые данные как строка или байты
        content_type: Content-Type из заголовков ответа
    
    Returns:
        Распарсенные данные соответствующего типа
    """
    pct = parse_content_type(content_type)

    if pct['content_type'] in CFG.JSON_EXTENSIONS:
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
        CFG.IMAGE_EXTENSIONS,
        CFG.VIDEO_EXTENSIONS,
        CFG.AUDIO_EXTENSIONS,
        CFG.FONT_EXTENSIONS,
        CFG.APPLICATION_EXTENSIONS,
        CFG.ARCHIVE_EXTENSIONS
    ]:
        if pct['content_type'] in types:
            # Для файлов создаем BytesIO объект
            if isinstance(data, bytes):
                parsed_data = BytesIO(data)
            else:
                # Если данные пришли как строка (не должно происходить для бинарных файлов, но на всякий случай)
                parsed_data = BytesIO(data.encode(pct['charset']))
            
            # Определяем расширение по content-type
            parsed_data.name = f"file{types[pct['content_type']]}"
            return parsed_data
    
    # Для всех остальных типов возвращаем как текст
    if isinstance(data, bytes):
        try:
            return data.decode(pct['charset'])
        except UnicodeDecodeError:
            # Если не удается декодировать, создаем BytesIO
            return BytesIO(data)
    else:
        return data

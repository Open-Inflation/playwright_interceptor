from beartype import beartype
from . import config as CFG


@beartype
def parse_content_type(content_type: str) -> dict[str, str]:
    """
    Парсит строку Content-Type и возвращает словарь с основным типом и параметрами.
    
    Args:
        content_type: Content-Type из заголовков ответа (например, "text/html; charset=utf-8")
    
    Returns:
        Словарь с ключом 'content_type' для основного типа и всеми дополнительными параметрами
    """
    if not content_type:
        return {'content_type': '', 'charset': 'utf-8'}
    
    # Разбиваем строку на части и убираем лишние пробелы
    parts = [p.strip() for p in content_type.split(';')]

    # Основной тип контента всегда в нижнем регистре
    result = {
        'content_type': parts[0].lower(),
        'charset': 'utf-8'  # По умолчанию устанавливаем utf-8
    }

    # Обработка дополнительных параметров
    for part in parts[1:]:
        if not part:
            continue

        if '=' in part:
            key, value = part.split('=', 1)
            key = key.strip().lower()
            # Удаление кавычек, если они есть
            value = value.strip().strip('"\'')
            if key == 'charset':
                value = value.lower()
                result['charset'] = value
            else:
                result[key] = value
        else:
            # Для параметров без значений
            result[part.lower()] = ''
    
    return result


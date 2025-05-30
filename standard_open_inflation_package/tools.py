import os
import re
import logging
import json
from beartype.typing import Dict, Union
from beartype import beartype
from io import BytesIO
from . import patterns as Patterns

@beartype
def get_env_proxy() -> Union[str, None]:
    """
    Получает прокси из переменных окружения.
    :return: Прокси-строка или None.
    """
    proxy = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy") or os.environ.get("HTTP_PROXY") or os.environ.get("http_proxy")
    return proxy if proxy else None

@beartype
def parse_proxy(proxy_str: Union[str, None], trust_env: bool, logger: logging.Logger) -> Union[Dict[str, str], None]:
    logger.debug(f"Parsing proxy string: {proxy_str}")

    if not proxy_str:
        if trust_env:
            logger.debug("Proxy string not provided, checking environment variables for HTTP(S)_PROXY")
            proxy_str = get_env_proxy()
        
        if not proxy_str:
            logger.info("No proxy string found, returning None")
            return None
        else:
            logger.info(f"Proxy string found in environment variables")

    # Example: user:pass@host:port or just host:port
    match = re.match(Patterns.PROXY, proxy_str)
    
    proxy_dict = {}
    if not match:
        logger.warning(f"Proxy string did not match expected pattern, using basic formating")
        proxy_dict['server'] = proxy_str
        
        if not proxy_str.startswith('http://') and not proxy_str.startswith('https://'):
            logger.warning("Proxy string missing protocol, prepending 'http://'")
            proxy_dict['server'] = f"http://{proxy_str}"
        
        logger.info(f"Proxy parsed as basic")
        return proxy_dict
    else:
        match_dict = match.groupdict()
        proxy_dict['server'] = f"{match_dict['scheme'] or 'http://'}{match_dict['host']}"
        if match_dict['port']:
            proxy_dict['server'] += f":{match_dict['port']}"
        
        for key in ['username', 'password']:
            if match_dict[key]:
                proxy_dict[key] = match_dict[key]
        
        logger.info(f"Proxy WITH{'OUT' if 'username' not in proxy_dict else ''} credentials")
        
        logger.info(f"Proxy parsed as regex")
        return proxy_dict

@beartype
def parse_response_data(data: str, content_type: str) -> Union[dict, list, str, BytesIO]:
    """
    Парсит данные ответа на основе content-type.
    
    Args:
        data: Сырые данные как строка
        content_type: Content-Type из заголовков ответа
    
    Returns:
        Распарсенные данные соответствующего типа
    """
    content_type = content_type.lower()
    
    if "application/json" in content_type:
        try:
            return json.loads(data)
        except json.JSONDecodeError:
            # Если не удалось распарсить как JSON, возвращаем как есть
            return data
    elif "image/" in content_type:
        # Для изображений создаем BytesIO объект
        # Примечание: для inject_fetch бинарные данные могут быть не корректными
        parsed_data = BytesIO(data.encode('utf-8'))
        
        # Определяем расширение по content-type
        ext_map = {
            'image/jpeg': '.jpg',
            'image/jpg': '.jpg', 
            'image/png': '.png',
            'image/gif': '.gif',
            'image/webp': '.webp',
            'image/svg+xml': '.svg'
        }
        ext = ext_map.get(content_type.split(';')[0], '.img')
        parsed_data.name = f"image{ext}"
        
        return parsed_data
    else:
        # Для всех остальных типов возвращаем как текст
        return data

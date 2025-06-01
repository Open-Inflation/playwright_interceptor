import os
import re
import logging
from beartype.typing import Dict, Union
from beartype import beartype
from . import config as CFG

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
    match = re.match(CFG.PROXY, proxy_str)
    
    proxy_dict = {}
    if not match:
        logger.warning(f"Proxy string did not match expected pattern, using basic formating")
        proxy_dict['server'] = proxy_str
        
        if not proxy_str.startswith(CFG.PROXY_HTTP_SCHEMES[0]) and not proxy_str.startswith(CFG.PROXY_HTTP_SCHEMES[1]):
            logger.warning("Proxy string missing protocol, prepending 'http://'")
            proxy_dict['server'] = f"{CFG.DEFAULT_HTTP_SCHEME}{proxy_str}"
        
        logger.info(f"Proxy parsed as basic")
        return proxy_dict
    else:
        match_dict = match.groupdict()
        proxy_dict['server'] = f"{match_dict['scheme'] or CFG.DEFAULT_HTTP_SCHEME}{match_dict['host']}"
        if match_dict['port']:
            proxy_dict['server'] += f":{match_dict['port']}"
        
        for key in ['username', 'password']:
            if match_dict[key]:
                proxy_dict[key] = match_dict[key]
        
        logger.info(f"Proxy WITH{'OUT' if 'username' not in proxy_dict else ''} credentials")
        
        logger.info(f"Proxy parsed as regex")
        return proxy_dict


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
        return {'content_type': ''}
    
    # Нормализация и разделение на части
    parts = content_type.lower().replace(' ', '').split(';')
    
    # Основной тип контента
    result = {
        'content_type': parts[0],
        'charset': 'utf-8'  # По умолчанию устанавливаем utf-8
    }

    # Обработка дополнительных параметров
    for part in parts[1:]:
        if not part:
            continue
        
        if '=' in part:
            key, value = part.split('=', 1)
            # Удаление кавычек, если они есть
            value = value.strip('"\'')
            result[key] = value
        else:
            # Для параметров без значений
            result[part] = ''
    
    return result


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
    logger.debug(CFG.LOGS.PARSING_PROXY.format(proxy_string=proxy_str))

    if not proxy_str:
        if trust_env:
            logger.debug(CFG.LOGS.PROXY_NOT_PROVIDED)
            proxy_str = get_env_proxy()
        
        if not proxy_str:
            logger.info(CFG.LOGS.NO_PROXY_FOUND)
            return None
        else:
            logger.info(CFG.LOGS.PROXY_FOUND_IN_ENV)

    # Example: user:pass@host:port or just host:port
    match = re.match(CFG.NETWORK.PROXY, proxy_str)
    
    proxy_dict = {}
    if not match:
        logger.warning(CFG.ERRORS.PROXY_PATTERN_MISMATCH)
        proxy_dict['server'] = proxy_str
        
        if not proxy_str.startswith(CFG.NETWORK.PROXY_HTTP_SCHEMES[0]) and not proxy_str.startswith(CFG.NETWORK.PROXY_HTTP_SCHEMES[1]):
            logger.warning(CFG.ERRORS.PROXY_MISSING_PROTOCOL)
            proxy_dict['server'] = f"{CFG.NETWORK.DEFAULT_HTTP_SCHEME}{proxy_str}"
        
        logger.info(CFG.LOGS.PROXY_PARSED_BASIC)
        return proxy_dict
    else:
        match_dict = match.groupdict()
        proxy_dict['server'] = f"{match_dict['scheme'] or CFG.NETWORK.DEFAULT_HTTP_SCHEME}{match_dict['host']}"
        if match_dict['port']:
            proxy_dict['server'] += f":{match_dict['port']}"
        
        for key in ['username', 'password']:
            if match_dict[key]:
                proxy_dict[key] = match_dict[key]
        
        logger.info(CFG.LOGS.PROXY_WITH_CREDENTIALS if 'username' in proxy_dict else CFG.LOGS.PROXY_WITHOUT_CREDENTIALS)
        
        logger.info(CFG.LOGS.PROXY_PARSED_REGEX)
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


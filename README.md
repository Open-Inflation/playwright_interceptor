# Standard Open Inflation Package

[![GitHub Actions](https://github.com/Open-Inflation/standard_open_inflation_package/workflows/API%20Tests/badge.svg)](https://github.com/Open-Inflation/standard_open_inflation_package/actions/workflows/check_tests.yml?query=branch%3Amain)
![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)
![PyPI - Package Version](https://img.shields.io/pypi/v/standard_open_inflation_package?color=blue)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/standard_open_inflation_package?label=PyPi%20downloads)](https://pypi.org/project/standard_open_inflation_package/)
![License](https://img.shields.io/badge/license-MIT-green)
[![Discord](https://img.shields.io/discord/792572437292253224?label=Discord&labelColor=%232c2f33&color=%237289da)](https://discord.gg/UnJnGHNbBp)
[![Telegram](https://img.shields.io/badge/Telegram-24A1DE)](https://t.me/miskler_dev)

Стандартный пакет для всех API Open Inflation, включающий инструменты для работы с прокси и генерации документации.

## Установка

```bash
pip install standard-open-inflation-package
```

## Использование

### Работа с прокси

```python
from standard_open_inflation_package import get_env_proxy, parse_proxy
import logging

# Получение прокси из переменных окружения
proxy = get_env_proxy()

# Парсинг прокси-строки
logger = logging.getLogger(__name__)
result = parse_proxy("user:pass@proxy.example.com:8080", trust_env=True, logger=logger)
```

### Генерация документации

```python
from standard_open_inflation_package import generate_docs_index

# Генерация индексной страницы
success = generate_docs_index("docs")
```

Или через командную строку:

```bash
generate-docs-index docs
```

## API

### `get_env_proxy() -> Union[str, None]`
Получает прокси из переменных окружения (HTTP_PROXY, HTTPS_PROXY, http_proxy, https_proxy).

### `parse_proxy(proxy_str, trust_env, logger) -> Union[Dict[str, str], None]`
Парсит строку прокси в словарь. Поддерживает форматы: `host:port`, `http://user:pass@host:port` и др. (для camoufox)

### `generate_docs_index(docs_dir: str = "docs") -> bool`
Генерирует HTML индексную страницу для директории с документацией.

## Разработка

```bash
git clone https://github.com/Open-Inflation/standard_open_inflation_package.git
cd standard_open_inflation_package
pip install -e .
pytest
```

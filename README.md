# NetworkInterceptor

[![GitHub Actions](https://github.com/Open-Inflation/standard_open_inflation_package/workflows/API%20Tests/badge.svg)](https://github.com/Open-Inflation/standard_open_inflation_package/actions/workflows/check_tests.yml?query=branch%3Amain)
![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)
![PyPI - Package Version](https://img.shields.io/pypi/v/standard_open_inflation_package?color=blue)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/standard_open_inflation_package?label=PyPi%20downloads)](https://pypi.org/project/standard_open_inflation_package/)
![License](https://img.shields.io/badge/license-MIT-green)
[![Discord](https://img.shields.io/discord/792572437292253224?label=Discord&labelColor=%232c2f33&color=%237289da)](https://discord.gg/UnJnGHNbBp)
[![Telegram](https://img.shields.io/badge/Telegram-24A1DE)](https://t.me/miskler_dev)

Addon for Playwright providing advanced request interception and modification.

## Installation

```bash
pip install standard-open-inflation-package
```

## Usage

```python
from playwright.async_api import async_playwright
from standard_open_inflation_package import NetworkInterceptor, Handler, Execute

async def main():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch()
        page = await browser.new_page()
        await page.goto("https://example.com")

        interceptor = NetworkInterceptor(page)
        results = await interceptor.execute(Handler.ALL(execute=Execute.RETURN()))
        print(results)
        await browser.close()

```

## License

MIT

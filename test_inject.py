#!/usr/bin/env python3
import asyncio
import traceback
import json

async def test_inject_fetch():
    try:
        from standard_open_inflation_package import BaseAPI
        
        api = BaseAPI(debug=True, timeout=30.0)
        await api.new_session(include_browser=True)
        page = await api.new_page()
        
        # Заходим на тестовую страницу
        await page.direct_fetch("https://httpbin.org/")
        
        print("Testing inject_fetch...")
        
        # Тестируем inject_fetch
        resp = await page.inject_fetch("https://httpbin.org/get")
        print(f"Status: {resp.status}")
        print(f"Headers: {resp.headers}")
        print(f"Response type: {resp.response}")
        print(f"Duration: {resp.duration:.3f}s")
        
        await api.close(include_browser=True)
        print("✓ Test successful")
        
    except Exception as e:
        print(f"✗ Error: {e}")
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    import sys
    success = asyncio.run(test_inject_fetch())
    sys.exit(0 if success else 1)

#!/usr/bin/env python3
"""
最小限Playwrightテスト
"""
import asyncio
from playwright.async_api import async_playwright

async def test_minimal_playwright():
    """最小限Playwrightテスト"""
    print("🔍 最小限Playwrightテスト開始")
    print("=" * 50)
    
    try:
        async with async_playwright() as p:
            print("✅ Playwright起動成功")
            
            browser = await p.chromium.launch(headless=True)
            print("✅ Chromiumブラウザ起動成功")
            
            page = await browser.new_page()
            print("✅ ページ作成成功")
            
            # 簡単なテスト
            await page.goto("https://www.google.com", timeout=30000)
            print("✅ Google アクセス成功")
            
            title = await page.title()
            print(f"✅ ページタイトル: {title}")
            
            await browser.close()
            print("✅ ブラウザクローズ成功")
        
        print("\n🎉 最小限Playwrightテスト成功！")
        print("🚀 根本解決確認：Playwright動作確認完了")
        return True
        
    except Exception as e:
        print(f"❌ テストエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    import sys
    success = asyncio.run(test_minimal_playwright())
    sys.exit(0 if success else 1)
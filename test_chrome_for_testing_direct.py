#!/usr/bin/env python3
"""
Chrome for Testing直接起動テスト - Playwright統合版
Chrome for Testing Direct Launch Test - Playwright Integration
"""
import asyncio
from playwright.async_api import async_playwright

async def test_chrome_for_testing_direct():
    """Chrome for Testingを直接指定してPlaywright起動テスト"""
    print("🧪 Chrome for Testing 直接起動テスト開始")
    print("=" * 50)
    
    try:
        async with async_playwright() as p:
            print("✅ Playwright初期化完了")
            
            # Chrome for Testingを直接指定して起動
            browser = await p.chromium.launch(
                executable_path='/opt/chrome-for-testing/chrome-linux64/chrome',
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor',
                    '--single-process',  # WSL2での安定性向上
                    '--disable-software-rasterizer',
                    '--disable-background-timer-throttling',
                    '--disable-backgrounding-occluded-windows',
                    '--disable-renderer-backgrounding'
                ]
            )
            print("✅ Chrome for Testing起動成功")
            
            # ブラウザコンテキスト作成
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36'
            )
            print("✅ ブラウザコンテキスト作成完了")
            
            # ページ作成
            page = await context.new_page()
            page.set_default_timeout(60000)  # 60秒タイムアウト
            print("✅ ページ作成完了")
            
            # シンプルなHTMLテスト
            print("\n🌐 基本動作テスト実行...")
            test_html = """
            <html>
                <head><title>Chrome for Testing WSL2テスト</title></head>
                <body>
                    <h1>Chrome for Testing 動作確認</h1>
                    <p>WSL2環境でのPlaywright統合テスト</p>
                    <div id="test-element">テスト要素発見</div>
                    <button id="test-button">テストボタン</button>
                </body>
            </html>
            """
            
            await page.set_content(test_html)
            print("✅ HTMLコンテンツ設定完了")
            
            # ページ情報取得
            title = await page.title()
            print(f"📖 ページタイトル: {title}")
            
            # 要素検索テスト
            element = await page.wait_for_selector('#test-element', timeout=10000)
            if element:
                text = await element.text_content()
                print(f"🎯 要素テキスト: {text}")
            
            # ボタンクリックテスト
            button = await page.wait_for_selector('#test-button', timeout=10000)
            if button:
                await button.click()
                print("✅ ボタンクリックテスト成功")
            
            # JavaScript実行テスト
            result = await page.evaluate('() => document.title')
            print(f"⚡ JavaScript実行結果: {result}")
            
            # 外部サイトアクセステスト
            print("\n🌐 外部サイトアクセステスト...")
            await page.goto("https://httpbin.org/get", wait_until='domcontentloaded')
            print(f"✅ 外部サイトアクセス成功: {page.url}")
            
            # レスポンス内容確認
            content = await page.content()
            if "httpbin" in content.lower():
                print("✅ レスポンス内容確認成功")
            else:
                print("⚠️ レスポンス内容異常")
            
            await browser.close()
            print("\n🎉 Chrome for Testing直接起動テスト成功！")
            return True
            
    except Exception as e:
        print(f"❌ テストエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = asyncio.run(test_chrome_for_testing_direct())
    print(f"\n📊 最終結果: {'✅ 成功' if success else '❌ 失敗'}")
    exit(0 if success else 1)
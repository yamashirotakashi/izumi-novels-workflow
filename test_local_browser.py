#!/usr/bin/env python3
"""
ローカルブラウザテスト - Chrome for Testing動作確認
Local Browser Test - Chrome for Testing Operation Verification
"""
import asyncio
from playwright.async_api import async_playwright

async def test_local_browser():
    """ローカルブラウザ動作テスト"""
    print("🧪 Chrome for Testing ローカル動作テスト")
    print("=" * 50)
    
    try:
        async with async_playwright() as p:
            print("✅ Playwright初期化完了")
            
            # Chrome for Testing起動（WSL2最適化）
            browser = await p.chromium.launch(
                executable_path='/opt/chrome-for-testing/chrome-linux64/chrome',
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage', 
                    '--disable-gpu',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor',
                    '--single-process'  # WSL2での安定性向上
                ]
            )
            print("✅ Chrome for Testing起動成功")
            
            # ページ作成
            page = await browser.new_page()
            print("✅ ページ作成完了")
            
            # ローカルHTMLテスト
            test_html = """
            <html>
                <head><title>Chrome for Testing 動作確認</title></head>
                <body>
                    <h1>Chrome for Testing WSL2動作テスト</h1>
                    <p>ブラウザが正常に動作しています</p>
                    <div id="test-element">テスト要素</div>
                </body>
            </html>
            """
            
            await page.set_content(test_html)
            print("✅ HTMLコンテンツ設定完了")
            
            # ページ情報取得
            title = await page.title()
            print(f"📖 ページタイトル: {title}")
            
            # 要素検索テスト
            element = await page.query_selector('#test-element')
            if element:
                text = await element.text_content()
                print(f"🎯 要素テキスト: {text}")
            
            # JavaScript実行テスト
            result = await page.evaluate('() => document.title')
            print(f"⚡ JavaScript実行結果: {result}")
            
            # スクリーンショット取得テスト（オプション）
            try:
                await page.screenshot(path='test_screenshot.png')
                print("📸 スクリーンショット保存完了")
            except Exception as e:
                print(f"⚠️ スクリーンショット取得エラー: {e}")
            
            await browser.close()
            print("✅ ブラウザクローズ完了")
            
            print("\n🎉 Chrome for Testing ローカル動作テスト成功！")
            print("🚀 Amazon Kindleスクレイパー実装準備完了")
            return True
            
    except Exception as e:
        print(f"❌ テストエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = asyncio.run(test_local_browser())
    print(f"\n📊 最終結果: {'✅ 成功' if success else '❌ 失敗'}")
    exit(0 if success else 1)
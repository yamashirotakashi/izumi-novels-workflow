#!/usr/bin/env python3
"""
Amazon Kindle検索デバッグスクリプト - 詳細ログ出力版
Amazon Kindle Search Debug Script - Detailed Logging Version
"""
import asyncio
import sys
from pathlib import Path
from playwright.async_api import async_playwright

async def debug_amazon_search():
    """Amazon検索プロセスの詳細デバッグ"""
    print("🔍 Amazon Kindle検索デバッグ開始")
    print("=" * 50)
    
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True, 
                args=['--no-sandbox', '--disable-dev-shm-usage']
            )
            
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
            )
            
            page = await context.new_page()
            page.set_default_timeout(60000)  # 60秒タイムアウト
            
            print("✅ ブラウザ起動完了")
            
            # Amazon.co.jpアクセス
            print("🌐 Amazon.co.jpアクセス中...")
            await page.goto("https://www.amazon.co.jp", wait_until='domcontentloaded')
            print(f"✅ ページタイトル: {await page.title()}")
            print(f"✅ 現在URL: {page.url}")
            
            # 検索ボックス要素の確認
            print("\n🔍 検索ボックス要素確認...")
            search_selectors = [
                "#twotabsearchtextbox",
                'input[placeholder*="検索"]',
                'input[name="field-keywords"]'
            ]
            
            search_element = None
            for selector in search_selectors:
                try:
                    element = await page.wait_for_selector(selector, timeout=10000)
                    if element:
                        search_element = element
                        print(f"✅ 検索ボックス発見: {selector}")
                        break
                except Exception as e:
                    print(f"❌ セレクタ失敗: {selector} - {e}")
                    continue
            
            if not search_element:
                print("❌ 検索ボックスが見つかりません")
                return False
            
            # 検索クエリ入力
            query = "Python プログラミング"
            print(f"\n⌨️ 検索クエリ入力: '{query}'")
            await search_element.fill("")
            await search_element.type(query, delay=100)
            
            # 検索ボタンの確認
            print("\n🔍 検索ボタン要素確認...")
            button_selectors = [
                "#nav-search-submit-button",
                'input[type="submit"][value="検索"]',
                ".nav-search-submit"
            ]
            
            search_button = None
            for selector in button_selectors:
                try:
                    element = await page.wait_for_selector(selector, timeout=10000)
                    if element:
                        search_button = element
                        print(f"✅ 検索ボタン発見: {selector}")
                        break
                except Exception as e:
                    print(f"❌ ボタンセレクタ失敗: {selector} - {e}")
                    continue
            
            if not search_button:
                print("❌ 検索ボタンが見つかりません")
                return False
            
            # 検索実行前のスクリーンショット
            try:
                await page.screenshot(path="debug_before_search.png")
                print("📸 検索前スクリーンショット保存")
            except:
                pass
            
            # 検索実行
            print("\n🚀 検索実行...")
            await search_button.click()
            
            # ページ遷移待機（詳細ログ付き）
            print("⏳ ページ遷移待機中...")
            try:
                await page.wait_for_load_state('networkidle', timeout=30000)
                print("✅ ネットワーク待機完了")
            except Exception as e:
                print(f"⚠️ ネットワーク待機タイムアウト: {e}")
            
            # 結果確認
            print(f"\n📊 検索後URL: {page.url}")
            print(f"📊 検索後タイトル: {await page.title()}")
            
            # 検索結果要素の確認
            result_selectors = [
                '[data-component-type="s-search-result"]',
                '.s-result-item',
                '.a-section.a-spacing-base'
            ]
            
            for selector in result_selectors:
                try:
                    results = await page.query_selector_all(selector)
                    if results:
                        print(f"✅ 検索結果発見: {len(results)}件 ({selector})")
                        
                        # 最初の結果の詳細
                        first_result = results[0]
                        title_element = await first_result.query_selector('h2 a span')
                        if title_element:
                            title = await title_element.text_content()
                            print(f"📚 最初の結果: {title[:50]}...")
                        break
                except Exception as e:
                    print(f"❌ 結果セレクタエラー: {selector} - {e}")
                    continue
            
            # 検索実行後のスクリーンショット
            try:
                await page.screenshot(path="debug_after_search.png")
                print("📸 検索後スクリーンショット保存")
            except:
                pass
            
            await browser.close()
            print("\n🎉 デバッグ完了")
            return True
            
    except Exception as e:
        print(f"❌ デバッグエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = asyncio.run(debug_amazon_search())
    print(f"\n📊 デバッグ結果: {'✅ 成功' if success else '❌ 失敗'}")
    sys.exit(0 if success else 1)
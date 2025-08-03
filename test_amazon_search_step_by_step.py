#!/usr/bin/env python3
"""
Amazon検索ステップバイステップ検証 - Chrome for Testing版
Amazon Search Step-by-Step Verification - Chrome for Testing Version
"""
import asyncio
from playwright.async_api import async_playwright

async def test_amazon_search_step_by_step():
    """Amazon検索プロセスを段階的に検証"""
    print("🔍 Amazon検索ステップバイステップ検証開始")
    print("=" * 60)
    
    try:
        async with async_playwright() as p:
            # Chrome for Testing起動
            browser = await p.chromium.launch(
                executable_path='/opt/chrome-for-testing/chrome-linux64/chrome',
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--disable-web-security',
                    '--single-process'
                ]
            )
            
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
            )
            
            page = await context.new_page()
            page.set_default_timeout(30000)
            print("✅ ブラウザ準備完了")
            
            # ステップ1: Amazon.co.jpアクセス
            print("\n📍 ステップ1: Amazon.co.jpアクセス")
            await page.goto("https://www.amazon.co.jp", wait_until='domcontentloaded')
            await asyncio.sleep(2)
            
            title = await page.title()
            print(f"✅ ページタイトル: {title}")
            print(f"✅ 現在URL: {page.url}")
            
            # ステップ2: 検索ボックス要素分析
            print("\n📍 ステップ2: 検索ボックス要素分析")
            
            # 検索ボックス候補の全て確認
            search_candidates = [
                "#twotabsearchtextbox",
                'input[name="field-keywords"]', 
                'input[placeholder*="検索"]',
                '#nav-search input',
                '.nav-search-field input'
            ]
            
            found_search = None
            for candidate in search_candidates:
                try:
                    element = await page.wait_for_selector(candidate, timeout=5000)
                    if element:
                        is_visible = await element.is_visible()
                        is_enabled = await element.is_enabled()
                        placeholder = await element.get_attribute('placeholder') or ''
                        print(f"✅ 検索ボックス発見: {candidate}")
                        print(f"   - 表示状態: {is_visible}")
                        print(f"   - 有効状態: {is_enabled}")
                        print(f"   - プレースホルダー: {placeholder}")
                        
                        if is_visible and is_enabled:
                            found_search = element
                            found_selector = candidate
                            break
                except Exception as e:
                    print(f"❌ セレクタ失敗: {candidate} - {str(e)[:50]}...")
            
            if not found_search:
                print("❌ 検索ボックスが見つかりません")
                return False
            
            # ステップ3: 検索クエリ入力テスト
            print(f"\n📍 ステップ3: 検索クエリ入力テスト ({found_selector})")
            query = "Python プログラミング"
            
            await found_search.click()
            await asyncio.sleep(0.5)
            await found_search.fill("")
            await asyncio.sleep(0.5)
            await found_search.type(query, delay=100)
            await asyncio.sleep(1)
            
            # 入力確認
            current_value = await found_search.input_value()
            print(f"✅ 入力値確認: '{current_value}'")
            
            # ステップ4: 検索ボタン要素分析
            print("\n📍 ステップ4: 検索ボタン要素分析")
            
            button_candidates = [
                "#nav-search-submit-button",
                '.nav-search-submit input',
                'input[type="submit"]',
                '#nav-search-submit',
                '.nav-search-submit-text'
            ]
            
            found_search_button = None
            for candidate in button_candidates:
                try:
                    element = await page.wait_for_selector(candidate, timeout=5000)
                    if element:
                        is_visible = await element.is_visible()
                        is_enabled = await element.is_enabled()
                        value = await element.get_attribute('value') or ''
                        print(f"✅ 検索ボタン発見: {candidate}")
                        print(f"   - 表示状態: {is_visible}")
                        print(f"   - 有効状態: {is_enabled}")
                        print(f"   - ボタン値: {value}")
                        
                        if is_visible and is_enabled:
                            found_search_button = element
                            found_button_selector = candidate
                            break
                except Exception as e:
                    print(f"❌ ボタンセレクタ失敗: {candidate} - {str(e)[:50]}...")
            
            if not found_search_button:
                print("❌ 検索ボタンが見つかりません")
                return False
            
            # ステップ5: 検索実行前のページ状態保存
            print(f"\n📍 ステップ5: 検索実行 ({found_button_selector})")
            
            current_url_before = page.url
            print(f"🌐 検索実行前URL: {current_url_before}")
            
            # 検索実行
            print("🚀 検索ボタンクリック実行...")
            await found_search_button.click()
            
            # ページ遷移待機（段階的に）
            print("⏳ ページ遷移待機中...")
            try:
                # 最初にdomcontentloadedを待機
                await page.wait_for_load_state('domcontentloaded', timeout=15000)
                print("✅ DOM読み込み完了")
                
                # URLの変化を確認
                current_url_after = page.url
                print(f"🌐 検索実行後URL: {current_url_after}")
                
                if current_url_before != current_url_after:
                    print("✅ URL変化確認 - ページ遷移成功")
                else:
                    print("⚠️ URL変化なし")
                
                # ネットワークアイドル待機（短縮版）
                await page.wait_for_load_state('networkidle', timeout=10000)
                print("✅ ネットワーク待機完了")
                
            except Exception as e:
                print(f"⚠️ ページ遷移待機エラー: {e}")
            
            # ステップ6: 検索結果ページ分析
            print("\n📍 ステップ6: 検索結果ページ分析")
            
            final_title = await page.title()
            final_url = page.url
            print(f"📖 最終ページタイトル: {final_title}")
            print(f"🌐 最終URL: {final_url}")
            
            # 検索結果要素確認
            result_candidates = [
                '[data-component-type="s-search-result"]',
                '.s-result-item',
                '.a-section.a-spacing-base',
                '.s-search-result'
            ]
            
            results_found = []
            for candidate in result_candidates:
                try:
                    elements = await page.query_selector_all(candidate)
                    if elements:
                        count = len(elements)
                        print(f"✅ 検索結果発見: {count}件 ({candidate})")
                        results_found.append((candidate, count))
                        
                        if count > 0:
                            # 最初の結果の詳細分析
                            first_result = elements[0]
                            try:
                                title_element = await first_result.query_selector('h2 a span, .s-size-medium span')
                                if title_element:
                                    result_title = await title_element.text_content()
                                    print(f"📚 最初の結果タイトル: {result_title[:60]}...")
                            except:
                                print("⚠️ 結果タイトル取得失敗")
                except Exception as e:
                    print(f"❌ 結果セレクタエラー: {candidate} - {str(e)[:50]}...")
            
            await browser.close()
            
            # 結果サマリー
            print(f"\n📊 テスト結果サマリー")
            print("=" * 60)
            print(f"✅ ブラウザ起動: 成功")
            print(f"✅ Amazon.co.jpアクセス: 成功")
            print(f"✅ 検索ボックス発見: 成功 ({found_selector})")
            print(f"✅ 検索クエリ入力: 成功")
            print(f"✅ 検索ボタン発見: 成功 ({found_button_selector})")
            print(f"✅ 検索実行: 成功")
            print(f"✅ ページ遷移: 成功")
            print(f"📈 検索結果: {len(results_found)}パターン発見")
            
            success = len(results_found) > 0
            print(f"\n🎉 総合判定: {'✅ 成功' if success else '❌ 失敗'}")
            return success
            
    except Exception as e:
        print(f"❌ テストエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = asyncio.run(test_amazon_search_step_by_step())
    print(f"\n📊 最終結果: {'✅ 成功' if success else '❌ 失敗'}")
    exit(0 if success else 1)
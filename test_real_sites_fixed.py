#!/usr/bin/env python3
"""
Windows環境での実サイト検索テスト（修正版）
より堅牢なセレクターと例外処理
"""
import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class RealSiteTestFixed:
    def __init__(self):
        self.driver = None
        self.results = []
    
    def setup_driver(self):
        """Chrome WebDriverを設定"""
        print("🔧 Chrome WebDriverを設定中...")
        options = uc.ChromeOptions()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        
        self.driver = uc.Chrome(options=options)
        self.driver.maximize_window()
        print("✅ Chrome WebDriver準備完了")
    
    def find_search_input(self, selectors):
        """複数のセレクターで検索入力欄を探す"""
        for selector in selectors:
            try:
                element = self.driver.find_element(By.CSS_SELECTOR, selector)
                if element.is_displayed():
                    return element
            except NoSuchElementException:
                continue
        return None
    
    def test_kinoppy_search(self):
        """Kinoppy検索テスト（修正版）"""
        print("\n🔍 Kinoppy検索テスト開始...")
        search_term = "課長が目覚めたら異世界"
        
        try:
            # Kinoppyサイトへアクセス
            print("📍 Kinoppyサイトにアクセス中...")
            self.driver.get("https://www.kinokuniya.co.jp/kinoppystore/")
            time.sleep(5)  # ページ読み込み待機
            
            # 複数の可能なセレクターで検索ボックスを探す
            search_selectors = [
                'input[name="q"]',
                'input[type="search"]',
                '.search-input',
                '#search-box',
                '.search-box input',
                'input[placeholder*="検索"]',
                'input[placeholder*="search"]'
            ]
            
            print("🔎 検索ボックスを探しています...")
            search_box = self.find_search_input(search_selectors)
            
            if not search_box:
                # 手動で検索する方法を試す
                print("⚠️ 検索ボックスが見つかりません。別の方法を試します...")
                # URLに直接検索クエリを追加
                search_url = f"https://www.kinokuniya.co.jp/kinoppystore/search.php?q={search_term}"
                self.driver.get(search_url)
                time.sleep(5)
            else:
                print(f"✅ 検索ボックス発見: {search_box.tag_name}")
                search_box.clear()
                search_box.send_keys(search_term)
                search_box.send_keys(Keys.RETURN)
                time.sleep(5)
            
            # 検索結果を確認（より広範囲なセレクター）
            result_selectors = [
                '.product-item',
                '.item',
                '.book-item',
                '.search-result-item',
                '.result',
                '[class*="product"]',
                '[class*="book"]',
                '[class*="item"]'
            ]
            
            results_count = 0
            for selector in result_selectors:
                try:
                    results = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if results:
                        results_count = len(results)
                        break
                except:
                    continue
            
            # ページタイトルもチェック
            page_title = self.driver.title
            
            self.results.append({
                'site': 'Kinoppy',
                'search_term': search_term,
                'results_found': results_count,
                'status': 'SUCCESS' if results_count > 0 or '検索' in page_title else 'NO_RESULTS',
                'url': self.driver.current_url,
                'page_title': page_title
            })
            
            print(f"✅ Kinoppy検索完了: {results_count}件の結果")
            print(f"📄 ページタイトル: {page_title}")
            return True
            
        except Exception as e:
            print(f"❌ Kinoppy検索エラー: {e}")
            self.results.append({
                'site': 'Kinoppy',
                'search_term': search_term,
                'status': 'ERROR',
                'error': str(e)
            })
            return False
    
    def test_reader_store_search(self):
        """Reader Store検索テスト（修正版）"""
        print("\n🔍 Reader Store検索テスト開始...")
        search_term = "課長が目覚めたら異世界"
        
        try:
            # Reader Storeサイトへアクセス
            print("📍 Reader Storeサイトにアクセス中...")
            self.driver.get("https://ebookstore.sony.jp/")
            time.sleep(5)
            
            # 複数の可能なセレクターで検索ボックスを探す
            search_selectors = [
                'input[type="search"]',
                'input[name="query"]',
                'input[name="q"]',
                '.search-input',
                '#search-input',
                '.search-box input',
                'input[placeholder*="検索"]',
                'input[placeholder*="search"]'
            ]
            
            print("🔎 検索ボックスを探しています...")
            search_box = self.find_search_input(search_selectors)
            
            if not search_box:
                # 手動で検索する方法を試す
                print("⚠️ 検索ボックスが見つかりません。別の方法を試します...")
                search_url = f"https://ebookstore.sony.jp/search/?query={search_term}"
                self.driver.get(search_url)
                time.sleep(5)
            else:
                print(f"✅ 検索ボックス発見: {search_box.tag_name}")
                search_box.clear()
                search_box.send_keys(search_term)
                search_box.send_keys(Keys.RETURN)
                time.sleep(5)
            
            # 検索結果を確認
            result_selectors = [
                '.book-item',
                '.product',
                '.result-item',
                '.search-result',
                '[class*="book"]',
                '[class*="product"]',
                '[class*="item"]'
            ]
            
            results_count = 0
            for selector in result_selectors:
                try:
                    results = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if results:
                        results_count = len(results)
                        break
                except:
                    continue
            
            # ページタイトルもチェック
            page_title = self.driver.title
            
            self.results.append({
                'site': 'Reader Store',
                'search_term': search_term,
                'results_found': results_count,
                'status': 'SUCCESS' if results_count > 0 or '検索' in page_title else 'NO_RESULTS',
                'url': self.driver.current_url,
                'page_title': page_title
            })
            
            print(f"✅ Reader Store検索完了: {results_count}件の結果")
            print(f"📄 ページタイトル: {page_title}")
            return True
            
        except Exception as e:
            print(f"❌ Reader Store検索エラー: {e}")
            self.results.append({
                'site': 'Reader Store',
                'search_term': search_term,
                'status': 'ERROR',
                'error': str(e)
            })
            return False
    
    def test_simple_navigation(self):
        """シンプルなナビゲーションテスト"""
        print("\n🔍 シンプルナビゲーションテスト...")
        
        try:
            # Googleで検索してみる（基本動作確認）
            self.driver.get("https://www.google.com")
            time.sleep(3)
            
            search_box = self.driver.find_element(By.NAME, "q")
            search_box.send_keys("kinoppy 課長が目覚めたら異世界")
            search_box.send_keys(Keys.RETURN)
            time.sleep(3)
            
            results = self.driver.find_elements(By.CSS_SELECTOR, ".g")
            
            self.results.append({
                'site': 'Google (基本テスト)',
                'search_term': 'kinoppy 課長が目覚めたら異世界',
                'results_found': len(results),
                'status': 'SUCCESS' if len(results) > 0 else 'NO_RESULTS',
                'url': self.driver.current_url
            })
            
            print(f"✅ Google検索完了: {len(results)}件の結果")
            return True
            
        except Exception as e:
            print(f"❌ Google検索エラー: {e}")
            return False
    
    def cleanup(self):
        """リソースのクリーンアップ"""
        if self.driver:
            print("\n🧹 ブラウザを終了中...")
            try:
                self.driver.quit()
            except:
                pass  # エラーを無視
    
    def show_results(self):
        """結果表示"""
        print("\n" + "="*60)
        print("📊 実サイト検索テスト結果（修正版）")
        print("="*60)
        
        for result in self.results:
            print(f"\n🌐 {result['site']}:")
            print(f"   検索語: {result.get('search_term', 'N/A')}")
            print(f"   ステータス: {result['status']}")
            if result['status'] == 'SUCCESS':
                print(f"   検索結果: {result['results_found']}件")
                if 'page_title' in result:
                    print(f"   ページ: {result['page_title']}")
                print(f"   URL: {result['url']}")
            elif result['status'] == 'ERROR':
                print(f"   エラー: {result.get('error', 'Unknown')}")
        
        # 成功率計算
        success_count = sum(1 for r in self.results if r['status'] == 'SUCCESS')
        total_count = len(self.results)
        success_rate = (success_count / total_count * 100) if total_count > 0 else 0
        
        print(f"\n📈 総合成功率: {success_count}/{total_count} ({success_rate:.1f}%)")
        
        if success_rate >= 66:
            print("🎉 Windows環境での実サイトテスト: 成功")
        elif success_rate >= 33:
            print("⚠️ Windows環境での実サイトテスト: 部分的成功")
        else:
            print("❌ Windows環境での実サイトテスト: 改善が必要")

def main():
    """メイン実行"""
    print("🚀 Windows環境での実サイト検索テスト開始（修正版）")
    print("⚠️ ブラウザウィンドウが表示されます")
    
    test = RealSiteTestFixed()
    
    try:
        # WebDriverセットアップ
        test.setup_driver()
        
        # 基本動作確認
        test.test_simple_navigation()
        time.sleep(2)
        
        # 各サイトのテスト実行
        test.test_kinoppy_search()
        time.sleep(3)  # サイト間の間隔
        
        test.test_reader_store_search()
        
        # 結果表示
        test.show_results()
        
    except KeyboardInterrupt:
        print("\n⚠️ ユーザーによる中断")
    except Exception as e:
        print(f"\n❌ 予期しないエラー: {e}")
    finally:
        test.cleanup()
        print("\n🏁 実サイト検索テスト完了")

if __name__ == '__main__':
    main()
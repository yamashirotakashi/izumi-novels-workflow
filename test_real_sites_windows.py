#!/usr/bin/env python3
"""
Windows環境での実サイト検索テスト
Kinoppy & Reader Store
"""
import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class RealSiteTest:
    def __init__(self):
        self.driver = None
        self.results = []
    
    def setup_driver(self):
        """Chrome WebDriverを設定"""
        print("🔧 Chrome WebDriverを設定中...")
        options = uc.ChromeOptions()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        # GUIモードで実行（Windows環境）
        # options.add_argument('--headless')  # コメントアウト = GUI表示
        
        self.driver = uc.Chrome(options=options)
        self.driver.maximize_window()
        print("✅ Chrome WebDriver準備完了")
    
    def test_kinoppy_search(self):
        """Kinoppy検索テスト"""
        print("\n🔍 Kinoppy検索テスト開始...")
        try:
            # Kinoppyサイトへアクセス
            self.driver.get("https://www.kinokuniya.co.jp/kinoppystore/")
            time.sleep(3)
            
            # 検索ボックスを探す
            search_box = self.driver.find_element(By.NAME, "q")
            search_term = "課長が目覚めたら異世界"
            
            print(f"🔎 検索実行: '{search_term}'")
            search_box.clear()
            search_box.send_keys(search_term)
            
            # 検索ボタンをクリック
            search_button = self.driver.find_element(By.CSS_SELECTOR, "input[type='submit']")
            search_button.click()
            
            # 結果を待機
            time.sleep(5)
            
            # 検索結果を確認
            results = self.driver.find_elements(By.CSS_SELECTOR, ".product-item, .item, .book-item")
            
            self.results.append({
                'site': 'Kinoppy',
                'search_term': search_term,
                'results_found': len(results),
                'status': 'SUCCESS' if len(results) > 0 else 'NO_RESULTS',
                'url': self.driver.current_url
            })
            
            print(f"✅ Kinoppy検索完了: {len(results)}件の結果")
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
        """Reader Store検索テスト"""
        print("\n🔍 Reader Store検索テスト開始...")
        try:
            # Reader Storeサイトへアクセス
            self.driver.get("https://ebookstore.sony.jp/")
            time.sleep(3)
            
            # 検索ボックスを探す
            search_box = self.driver.find_element(By.CSS_SELECTOR, "input[type='search'], input[name='query'], .search-input")
            search_term = "課長が目覚めたら異世界"
            
            print(f"🔎 検索実行: '{search_term}'")
            search_box.clear() 
            search_box.send_keys(search_term)
            search_box.submit()
            
            # 結果を待機
            time.sleep(5)
            
            # 検索結果を確認
            results = self.driver.find_elements(By.CSS_SELECTOR, ".book-item, .product, .result-item")
            
            self.results.append({
                'site': 'Reader Store',
                'search_term': search_term,
                'results_found': len(results),
                'status': 'SUCCESS' if len(results) > 0 else 'NO_RESULTS',
                'url': self.driver.current_url
            })
            
            print(f"✅ Reader Store検索完了: {len(results)}件の結果")
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
    
    def cleanup(self):
        """リソースのクリーンアップ"""
        if self.driver:
            print("\n🧹 ブラウザを終了中...")
            self.driver.quit()
    
    def show_results(self):
        """結果表示"""
        print("\n" + "="*50)
        print("📊 実サイト検索テスト結果")
        print("="*50)
        
        for result in self.results:
            print(f"\n🌐 {result['site']}:")
            print(f"   検索語: {result.get('search_term', 'N/A')}")
            print(f"   ステータス: {result['status']}")
            if result['status'] == 'SUCCESS':
                print(f"   検索結果: {result['results_found']}件")
                print(f"   URL: {result['url']}")
            elif result['status'] == 'ERROR':
                print(f"   エラー: {result.get('error', 'Unknown')}")
        
        # 成功率計算
        success_count = sum(1 for r in self.results if r['status'] == 'SUCCESS')
        total_count = len(self.results)
        success_rate = (success_count / total_count * 100) if total_count > 0 else 0
        
        print(f"\n📈 総合成功率: {success_count}/{total_count} ({success_rate:.1f}%)")

def main():
    """メイン実行"""
    print("🚀 Windows環境での実サイト検索テスト開始")
    print("⚠️ ブラウザウィンドウが表示されます")
    
    test = RealSiteTest()
    
    try:
        # WebDriverセットアップ
        test.setup_driver()
        
        # 各サイトのテスト実行
        test.test_kinoppy_search()
        time.sleep(2)  # サイト間の間隔
        
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
#!/usr/bin/env python3
"""
正確なバイナリペアでのWebDriverテスト
ChromeDriver: /snap/bin/chromium.chromedriver
Chrome: /snap/bin/chromium
"""
import sys
import time
from pathlib import Path

# プロジェクトルートを追加
project_root = Path(__file__).parent
sys.path.append(str(project_root / 'src'))

def test_correct_binary_pair():
    """正確なSnap Chromiumバイナリペアテスト"""
    print("🔍 正確なSnap Chromiumバイナリペアテスト")
    print("=" * 50)
    
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service
        
        print("✅ Seleniumインポート成功")
        
        # 正確なバイナリペア使用
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        # 完全にユニークなプロファイルディレクトリ
        unique_profile = f'/tmp/chrome_correct_test_{int(time.time() * 1000)}'
        options.add_argument(f'--user-data-dir={unique_profile}')
        
        # 正確なChrome binary指定
        options.binary_location = "/snap/bin/chromium"
        
        # 正確なChromeDriverサービス指定
        service = Service(executable_path="/snap/bin/chromium.chromedriver")
        
        print("🚀 正確なバイナリペアでWebDriverセッション作成中...")
        print(f"📍 Chrome: /snap/bin/chromium")
        print(f"📍 ChromeDriver: /snap/bin/chromium.chromedriver")
        print(f"📁 プロファイル: {unique_profile}")
        
        driver = webdriver.Chrome(service=service, options=options)
        
        print("✅ WebDriverセッション作成成功！")
        
        # 簡単なテスト
        print("🌐 Googleアクセステスト...")
        driver.get("https://www.google.com")
        title = driver.title
        print(f"✅ ページタイトル: {title}")
        
        # クリーンアップ
        driver.quit()
        print("✅ セッション正常終了")
        
        print("\n🎉 正確なバイナリペア WebDriver テスト成功！")
        return True
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_correct_binary_pair()
    sys.exit(0 if success else 1)
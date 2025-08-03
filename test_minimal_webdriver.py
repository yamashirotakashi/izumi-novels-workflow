#!/usr/bin/env python3
"""
最小限のWebDriverテスト - ChromeDriverとChromiumの互換性確認
"""
import sys
from pathlib import Path

# プロジェクトルートを追加
project_root = Path(__file__).parent
sys.path.append(str(project_root / 'src'))

def test_chromium_compatibility():
    """Snap Chromium + ChromeDriverの互換性テスト"""
    print("🔍 Chromium + ChromeDriver互換性テスト")
    print("=" * 50)
    
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service
        
        print("✅ Seleniumインポート成功")
        
        # Snap Chromiumバイナリを明示的に指定
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        # ユニークなプロファイルディレクトリを作成
        import time
        unique_profile = f'/tmp/chrome_profile_{int(time.time() * 1000)}'
        options.add_argument(f'--user-data-dir={unique_profile}')  # ユニークプロファイル指定
        print(f"📁 プロファイルディレクトリ: {unique_profile}")
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-background-timer-throttling')
        options.add_argument('--disable-backgrounding-occluded-windows')
        options.add_argument('--disable-renderer-backgrounding')
        options.add_argument('--disable-features=TranslateUI')
        options.add_argument('--disable-ipc-flooding-protection')
        
        # Snap Chromiumバイナリパスを指定
        options.binary_location = "/snap/bin/chromium"
        
        # ChromeDriverサービス
        service = Service(executable_path="./chromedriver_local")
        
        print("🚀 Chromium WebDriverセッション作成中...")
        print(f"📍 Chromium: /snap/bin/chromium")
        print(f"📍 ChromeDriver: ./chromedriver_local")
        
        driver = webdriver.Chrome(service=service, options=options)
        
        print("✅ WebDriverセッション作成成功！")
        
        # 簡単なテスト
        print("🌐 テストページアクセス...")
        driver.get("https://www.google.com")
        title = driver.title
        print(f"✅ ページタイトル: {title}")
        
        # クリーンアップ
        driver.quit()
        print("✅ セッション正常終了")
        
        print("\n🎉 Chromium WebDriver テスト成功")
        return True
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_chromium_compatibility()
    sys.exit(0 if success else 1)
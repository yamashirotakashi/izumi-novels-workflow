#!/usr/bin/env python3
"""
デフォルトプロファイル外でのWebDriverテスト
"""
import sys
import time
import tempfile
import os
from pathlib import Path

# プロジェクトルートを追加
project_root = Path(__file__).parent
sys.path.append(str(project_root / 'src'))

def test_no_default_profile():
    """デフォルトプロファイル外でのWebDriverテスト"""
    print("🔍 デフォルトプロファイル外WebDriverテスト")
    print("=" * 50)
    
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service
        
        print("✅ Seleniumインポート成功")
        
        # 完全に独立した一時ディレクトリ使用
        temp_dir = tempfile.mkdtemp(prefix='chrome_selenium_test_')
        print(f"📁 一時ディレクトリ作成: {temp_dir}")
        
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-software-rasterizer')
        
        # 完全に独立したプロファイル
        options.add_argument(f'--user-data-dir={temp_dir}')
        options.add_argument('--no-first-run')
        options.add_argument('--disable-default-apps')
        options.add_argument('--disable-extensions')
        
        # 正確なバイナリ指定
        options.binary_location = "/snap/bin/chromium"
        
        # 正確なChromeDriverサービス
        service = Service(executable_path="/snap/bin/chromium.chromedriver")
        
        print("🚀 独立プロファイルでWebDriverセッション作成中...")
        print(f"📍 Chrome: /snap/bin/chromium")
        print(f"📍 ChromeDriver: /snap/bin/chromium.chromedriver")
        print(f"📁 独立プロファイル: {temp_dir}")
        
        driver = webdriver.Chrome(service=service, options=options)
        
        print("✅ WebDriverセッション作成成功！")
        
        # 簡単なテスト
        print("🌐 Googleアクセステスト...")
        driver.get("https://www.google.com")
        title = driver.title
        print(f"✅ ページタイトル: {title}")
        
        # URL確認
        current_url = driver.current_url
        print(f"📍 現在のURL: {current_url}")
        
        # クリーンアップ
        driver.quit()
        print("✅ セッション正常終了")
        
        # 一時ディレクトリクリーンアップ
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
        print(f"🗑️ 一時ディレクトリクリーンアップ: {temp_dir}")
        
        print("\n🎉 独立プロファイル WebDriver テスト成功！")
        print("🚀 Phase 2 Amazon Kindle実動スクレイパー実装準備完了")
        return True
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()
        
        # エラー時もクリーンアップ試行
        try:
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)
        except:
            pass
            
        return False

if __name__ == '__main__':
    success = test_no_default_profile()
    sys.exit(0 if success else 1)
#!/usr/bin/env python3
"""
シンプルなChrome接続テスト
"""
import sys
from pathlib import Path

# プロジェクトルートを追加
project_root = Path(__file__).parent
sys.path.append(str(project_root / 'src'))

def simple_chrome_test():
    """シンプルなChrome接続テスト"""
    print("🔍 シンプルChrome接続テスト開始")
    print("=" * 50)
    
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service
        
        print("✅ Seleniumインポート成功")
        
        # サービス設定
        service = Service(executable_path="./chromedriver_local")
        print("✅ ChromeDriverサービス設定完了")
        
        # 最小Chrome オプション
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--remote-debugging-port=9222')  # デバッグポート指定
        
        print("✅ Chrome オプション設定完了")
        
        # WebDriver作成テスト
        print("🚀 ChromeDriverセッション作成中...")
        driver = webdriver.Chrome(service=service, options=options)
        
        print("✅ ChromeDriverセッション作成成功")
        
        # 簡単なテスト
        print("🌐 Googleアクセステスト...")
        driver.get("https://www.google.com")
        title = driver.title
        print(f"✅ ページタイトル: {title}")
        
        # クリーンアップ
        driver.quit()
        print("✅ ChromeDriverセッション終了")
        
        print("\n🎉 シンプルChrome接続テスト成功")
        return True
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = simple_chrome_test()
    sys.exit(0 if success else 1)
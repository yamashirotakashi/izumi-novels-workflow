#!/usr/bin/env python3
"""
Chrome/ChromeDriver接続デバッグテスト
"""
import sys
from pathlib import Path

# プロジェクトルートを追加
project_root = Path(__file__).parent
sys.path.append(str(project_root / 'src'))

def debug_chrome_setup():
    """Chrome/ChromeDriverセットアップのデバッグ"""
    print("🔍 Chrome/ChromeDriverデバッグテスト開始")
    print("=" * 50)
    
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        
        print("✅ Seleniumインポート成功")
        
        # Chrome オプション設定（最小構成）
        options = Options()
        options.add_argument('--headless=new')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        print("✅ Chrome オプション設定完了")
        
        # WebDriver作成テスト（undetected-chromedriver使用）
        import undetected_chromedriver as uc
        
        print("🚀 undetected-chromedriver セッション作成中...")
        print("📍 自動検出モード使用")
        
        driver = uc.Chrome(
            options=options,
            driver_executable_path="./chromedriver_local"
        )
        
        print("✅ ChromeDriverセッション作成成功")
        
        # 簡単なテスト
        print("🌐 Googleアクセステスト...")
        driver.get("https://www.google.com")
        title = driver.title
        print(f"✅ ページタイトル: {title}")
        
        # クリーンアップ
        driver.quit()
        print("✅ ChromeDriverセッション終了")
        
        print("\n🎉 Chrome/ChromeDriverデバッグ成功")
        return True
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = debug_chrome_setup()
    sys.exit(0 if success else 1)
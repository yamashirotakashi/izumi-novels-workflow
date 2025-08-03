#!/usr/bin/env python3
"""
Remote Debugging経由のChrome接続テスト
"""
import sys
from pathlib import Path

# プロジェクトルートを追加
project_root = Path(__file__).parent
sys.path.append(str(project_root / 'src'))

def test_remote_debugging():
    """Remote Debugging経由のChrome接続テスト"""
    print("🔍 Remote Debugging Chrome接続テスト")
    print("=" * 50)
    
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        
        print("✅ Seleniumインポート成功")
        
        # Remote Debugging設定
        options = Options()
        options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
        
        print("🚀 Remote Debugging WebDriver接続中...")
        print("📍 Debugging Address: 127.0.0.1:9222")
        
        # Remote WebDriver接続（サービス不要）
        driver = webdriver.Chrome(options=options)
        
        print("✅ Remote WebDriver接続成功！")
        
        # 簡単なテスト
        print("🌐 テストページアクセス...")
        driver.get("https://www.google.com")
        title = driver.title
        print(f"✅ ページタイトル: {title}")
        
        # クリーンアップ
        driver.quit()
        print("✅ セッション正常終了")
        
        print("\n🎉 Remote Debugging Chrome テスト成功")
        return True
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_remote_debugging()
    sys.exit(0 if success else 1)
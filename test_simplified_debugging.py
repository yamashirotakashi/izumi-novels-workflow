#!/usr/bin/env python3
"""
単純化デバッグプロトコルテスト
"""
import sys
import time
import subprocess
import requests
from pathlib import Path

# プロジェクトルートを追加
project_root = Path(__file__).parent
sys.path.append(str(project_root / 'src'))

def test_simplified_debugging():
    """単純化デバッグプロトコルテスト"""
    print("🔍 単純化デバッグプロトコルテスト")
    print("=" * 50)
    
    chrome_process = None
    
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        
        print("✅ Seleniumインポート成功")
        
        # Step 1: 単純なChrome起動
        print("🚀 Chrome起動...")
        chrome_cmd = [
            '/snap/bin/chromium',
            '--headless',
            '--no-sandbox',
            '--disable-dev-shm-usage',
            '--remote-debugging-port=9223',
            '--user-data-dir=/tmp/simple_chrome_test'
        ]
        
        chrome_process = subprocess.Popen(chrome_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Chrome起動確認
        for attempt in range(15):
            try:
                response = requests.get('http://127.0.0.1:9223/json/version', timeout=2)
                if response.status_code == 200:
                    print(f"✅ Chrome起動確認: ポート 9223")
                    break
            except requests.RequestException:
                time.sleep(1)
                continue
        else:
            raise RuntimeError("Chrome起動失敗")
        
        # Step 2: 最小限のWebDriver接続
        print("🔗 WebDriver接続...")
        options = Options()
        options.add_experimental_option("debuggerAddress", "127.0.0.1:9223")
        
        driver = webdriver.Chrome(options=options)
        
        print("✅ WebDriver接続成功！")
        
        # Step 3: 簡単なテスト
        print("🌐 テストページアクセス...")
        driver.get("https://www.google.com")
        title = driver.title
        print(f"✅ ページタイトル: {title}")
        
        # クリーンアップ
        driver.quit()
        print("✅ WebDriverセッション終了")
        
        if chrome_process:
            chrome_process.terminate()
            chrome_process.wait(timeout=10)
            print("✅ Chromeプロセス終了")
        
        print("\n🎉 単純化デバッグプロトコルテスト成功！")
        print("🚀 根本解決確認：Snap制約克服完了")
        return True
        
    except Exception as e:
        print(f"❌ テストエラー: {e}")
        import traceback
        traceback.print_exc()
        
        # エラー時のクリーンアップ
        if chrome_process:
            try:
                chrome_process.terminate()
                chrome_process.wait(timeout=5)
            except:
                try:
                    chrome_process.kill()
                except:
                    pass
        
        return False

if __name__ == '__main__':
    success = test_simplified_debugging()
    sys.exit(0 if success else 1)
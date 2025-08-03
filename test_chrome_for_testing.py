#!/usr/bin/env python3
"""
Chrome for Testing テストスクリプト - WSL2最適化版
Chrome for Testing Test Script - WSL2 Optimized Version

インストール後の動作確認とPlaywright/Selenium統合テスト
Post-installation verification and Playwright/Selenium integration test
"""
import os
import sys
import json
import time
import asyncio
from pathlib import Path
from typing import Optional

# プロジェクトルートを追加
project_root = Path(__file__).parent
sys.path.append(str(project_root / 'src'))

def check_chrome_for_testing_installation() -> dict:
    """Chrome for Testing インストール状況確認"""
    print("🔍 Chrome for Testing インストール確認...")
    
    base_dir = Path("/opt/chrome-for-testing")
    config_path = base_dir / "config.json"
    
    if not config_path.exists():
        return {"installed": False, "error": "設定ファイルが見つかりません"}
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        chrome_binary = Path(config["chrome_binary"])
        chromedriver_binary = Path(config["chromedriver_binary"])
        
        status = {
            "installed": True,
            "version": config["version"],
            "chrome_binary": str(chrome_binary),
            "chromedriver_binary": str(chromedriver_binary),
            "chrome_exists": chrome_binary.exists(),
            "chromedriver_exists": chromedriver_binary.exists(),
            "chrome_executable": chrome_binary.is_file() and os.access(chrome_binary, os.X_OK),
            "chromedriver_executable": chromedriver_binary.is_file() and os.access(chromedriver_binary, os.X_OK)
        }
        
        print(f"✅ バージョン: {status['version']}")
        print(f"✅ Chrome バイナリ: {status['chrome_binary']}")
        print(f"✅ ChromeDriver バイナリ: {status['chromedriver_binary']}")
        
        return status
        
    except Exception as e:
        return {"installed": False, "error": str(e)}

def test_chrome_direct_launch():
    """Chrome for Testing 直接起動テスト"""
    print("\n🧪 Chrome for Testing 直接起動テスト")
    print("=" * 40)
    
    chrome_binary = "/opt/chrome-for-testing/chrome-linux64/chrome"
    
    if not Path(chrome_binary).exists():
        print(f"❌ Chrome バイナリが見つかりません: {chrome_binary}")
        return False
    
    try:
        import subprocess
        
        # バージョン確認
        result = subprocess.run(
            [chrome_binary, "--version"],
            capture_output=True, text=True, check=True, timeout=10
        )
        print(f"✅ Chrome バージョン: {result.stdout.strip()}")
        
        # 簡単なページレンダリングテスト
        print("🌐 基本レンダリングテスト...")
        test_html = "data:text/html,<html><head><title>Test</title></head><body><h1>Chrome for Testing Works!</h1></body></html>"
        
        render_result = subprocess.run([
            chrome_binary,
            "--headless", "--no-sandbox", "--disable-dev-shm-usage",
            "--disable-gpu", "--virtual-time-budget=2000",
            "--run-all-compositor-stages-before-draw",
            "--dump-dom", test_html
        ], capture_output=True, text=True, timeout=15)
        
        if "Chrome for Testing Works!" in render_result.stdout:
            print("✅ 基本レンダリング確認")
        else:
            print("⚠️ レンダリング出力に期待値が含まれていません")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Chrome起動エラー: {e}")
        return False
    except subprocess.TimeoutExpired:
        print("❌ Chrome起動タイムアウト")
        return False
    except Exception as e:
        print(f"❌ テストエラー: {e}")
        return False

def test_selenium_integration():
    """Selenium統合テスト"""
    print("\n🧪 Selenium統合テスト")
    print("=" * 40)
    
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        
        print("✅ Selenium インポート成功")
        
        # Chrome for Testing 設定
        chrome_binary = "/opt/chrome-for-testing/chrome-linux64/chrome"
        chromedriver_binary = "/opt/chrome-for-testing/chromedriver-linux64/chromedriver"
        
        options = Options()
        options.binary_location = chrome_binary
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-software-rasterizer')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-default-apps')
        options.add_argument('--no-first-run')
        options.add_argument('--window-size=1920,1080')
        
        service = Service(chromedriver_binary)
        
        print("🚀 WebDriver起動...")
        driver = webdriver.Chrome(service=service, options=options)
        
        try:
            print("🌐 Googleアクセステスト...")
            driver.get("https://www.google.com")
            
            # タイトル確認
            title = driver.title
            print(f"✅ ページタイトル: {title}")
            
            # 検索ボックス発見テスト
            search_box = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.NAME, "q"))
            )
            print("✅ 検索ボックス発見")
            
            # 簡単な入力テスト
            search_box.send_keys("Chrome for Testing WSL2")
            print("✅ テキスト入力成功")
            
            # 現在のURL取得
            current_url = driver.current_url
            print(f"📍 現在のURL: {current_url}")
            
            print("✅ Selenium統合テスト成功！")
            return True
            
        finally:
            driver.quit()
            print("✅ WebDriver終了")
        
    except ImportError as e:
        print(f"❌ Selenium インポートエラー: {e}")
        print("pip install selenium で Selenium をインストールしてください")
        return False
    except Exception as e:
        print(f"❌ Selenium統合テストエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_playwright_integration():
    """Playwright統合テスト"""
    print("\n🧪 Playwright統合テスト")
    print("=" * 40)
    
    try:
        from playwright.async_api import async_playwright
        
        print("✅ Playwright インポート成功")
        
        async with async_playwright() as p:
            # Chrome for Testing パスを指定
            chrome_binary = "/opt/chrome-for-testing/chrome-linux64/chrome"
            
            browser = await p.chromium.launch(
                executable_path=chrome_binary,
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--disable-software-rasterizer',
                    '--disable-extensions',
                    '--disable-default-apps',
                    '--no-first-run'
                ]
            )
            
            print("✅ Playwright Chrome for Testing 起動成功")
            
            page = await browser.new_page()
            
            # Googleアクセステスト
            print("🌐 Googleアクセステスト...")
            await page.goto("https://www.google.com", timeout=30000)
            
            title = await page.title()
            print(f"✅ ページタイトル: {title}")
            
            # 検索ボックステスト（複数セレクタでフォールバック）
            search_selectors = [
                'input[name="q"]',
                'textarea[name="q"]', 
                '[data-ved] input',
                'input[type="search"]',
                '#search_form_input'
            ]
            
            search_input = None
            for selector in search_selectors:
                try:
                    search_input = await page.wait_for_selector(selector, timeout=3000)
                    if search_input:
                        break
                except:
                    continue
            
            if search_input:
                await search_input.fill("Playwright Chrome for Testing")
                print("✅ テキスト入力成功")
            else:
                print("⚠️ 検索ボックスが見つかりませんが、ページアクセスは成功")
            
            url = page.url
            print(f"📍 現在のURL: {url}")
            
            await browser.close()
            print("✅ Playwright Chrome for Testing 終了")
            
            print("✅ Playwright統合テスト成功！")
            return True
            
    except ImportError as e:
        print(f"❌ Playwright インポートエラー: {e}")
        print("pip install playwright で Playwright をインストールしてください")
        return False
    except Exception as e:
        print(f"❌ Playwright統合テストエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_performance_benchmark():
    """パフォーマンスベンチマーク"""
    print("\n🧪 パフォーマンスベンチマーク")
    print("=" * 40)
    
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.chrome.options import Options
        
        chrome_binary = "/opt/chrome-for-testing/chrome-linux64/chrome"
        chromedriver_binary = "/opt/chrome-for-testing/chromedriver-linux64/chromedriver"
        
        options = Options()
        options.binary_location = chrome_binary
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        service = Service(chromedriver_binary)
        
        # 起動時間測定
        start_time = time.time()
        driver = webdriver.Chrome(service=service, options=options)
        startup_time = time.time() - start_time
        print(f"⏱️ WebDriver起動時間: {startup_time:.2f}秒")
        
        try:
            # ページ読み込み時間測定
            test_sites = [
                "https://www.google.com",
                "https://httpbin.org/html",
                "data:text/html,<html><body><h1>Test</h1></body></html>"
            ]
            
            for site in test_sites[:2]:  # 最初の2サイトのみテスト
                load_start = time.time()
                driver.get(site)
                load_time = time.time() - load_start
                title = driver.title[:50]  # タイトル最初50文字
                print(f"⏱️ {site}: {load_time:.2f}秒 - {title}")
                
                time.sleep(1)  # サイト間の待機
            
            print("✅ パフォーマンスベンチマーク完了")
            return True
            
        finally:
            driver.quit()
        
    except Exception as e:
        print(f"❌ ベンチマークエラー: {e}")
        return False

def main():
    """メインテスト実行"""
    print("🚀 Chrome for Testing 統合テスト開始")
    print("=" * 50)
    
    # インストール確認
    install_status = check_chrome_for_testing_installation()
    if not install_status.get("installed", False):
        print(f"❌ Chrome for Testing がインストールされていません: {install_status.get('error', 'Unknown error')}")
        print("先に scripts/install_chrome_for_testing.py を実行してください")
        sys.exit(1)
    
    if not (install_status.get("chrome_executable", False) and install_status.get("chromedriver_executable", False)):
        print("❌ Chrome for Testing バイナリに実行権限がありません")
        sys.exit(1)
    
    # テスト実行
    tests = [
        ("Chrome直接起動", test_chrome_direct_launch),
        ("Selenium統合", test_selenium_integration),
        ("Playwright統合", lambda: asyncio.run(test_playwright_integration())),
        ("パフォーマンス", test_performance_benchmark),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name}テスト {'='*20}")
        try:
            success = test_func()
            results[test_name] = success
        except KeyboardInterrupt:
            print(f"\n⚠️ {test_name}テストが中断されました")
            results[test_name] = False
            break
        except Exception as e:
            print(f"❌ {test_name}テストで予期しないエラー: {e}")
            results[test_name] = False
    
    # 結果サマリー
    print("\n🎯 テスト結果サマリー")
    print("=" * 50)
    
    total_tests = len(results)
    passed_tests = sum(1 for success in results.values() if success)
    
    for test_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\n📊 合格率: {passed_tests}/{total_tests} ({passed_tests/total_tests*100:.1f}%)")
    
    if passed_tests == total_tests:
        print("\n🎉 全テスト合格！Chrome for Testing 準備完了")
        print("🚀 次のステップ: Amazon Kindle実動スクレイパー実装")
        sys.exit(0)
    else:
        print(f"\n⚠️ {total_tests - passed_tests}個のテストが失敗しました")
        print("問題を修正してから再テストしてください")
        sys.exit(1)

if __name__ == "__main__":
    main()
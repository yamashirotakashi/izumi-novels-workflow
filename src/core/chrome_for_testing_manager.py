#!/usr/bin/env python3
"""
Chrome for Testing マネージャー - WSL2最適化Selenium統合版
Chrome for Testing Manager - WSL2 Optimized Selenium Integration

前回調査で判明したSnapの根本的制約を回避する確実なアプローチ
Definitive approach to overcome fundamental Snap constraints identified in previous investigation
"""
import os
import sys
import json
import time
import signal
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any
import psutil
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.common.exceptions import WebDriverException

class ChromeForTestingManager:
    """Chrome for Testing 統合マネージャー"""
    
    def __init__(self):
        self.driver = None
        self.service = None
        self.config_path = Path("/opt/chrome-for-testing/config.json")
        self.chrome_binary = None
        self.chromedriver_binary = None
        self.is_running = False
        self._load_config()
        
    def _load_config(self) -> bool:
        """Chrome for Testing 設定読み込み"""
        if not self.config_path.exists():
            raise RuntimeError(
                "Chrome for Testing がインストールされていません。\n"
                "先に scripts/install_chrome_for_testing.py を実行してください。"
            )
        
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
            
            self.chrome_binary = config["chrome_binary"]
            self.chromedriver_binary = config["chromedriver_binary"]
            
            # バイナリ存在確認
            if not Path(self.chrome_binary).exists():
                raise RuntimeError(f"Chrome バイナリが見つかりません: {self.chrome_binary}")
            
            if not Path(self.chromedriver_binary).exists():
                raise RuntimeError(f"ChromeDriver バイナリが見つかりません: {self.chromedriver_binary}")
            
            print(f"✅ Chrome for Testing 設定読み込み完了")
            print(f"📍 Chrome: {self.chrome_binary}")
            print(f"📍 ChromeDriver: {self.chromedriver_binary}")
            
            return True
            
        except Exception as e:
            raise RuntimeError(f"設定読み込みエラー: {e}")
    
    def _create_chrome_options(self, headless: bool = True, extra_args: list = None) -> Options:
        """Chrome オプション作成 - WSL2最適化"""
        options = Options()
        
        # Chrome for Testing バイナリ指定
        options.binary_location = self.chrome_binary
        
        # WSL2最適化オプション
        base_args = [
            '--no-sandbox',                    # WSL2必須
            '--disable-dev-shm-usage',         # WSL2必須 
            '--disable-gpu',                   # WSL2最適化
            '--disable-software-rasterizer',   # GPU無効化
            '--disable-extensions',            # 軽量化
            '--disable-plugins',               # 軽量化
            '--disable-default-apps',          # 軽量化
            '--no-first-run',                  # 初回起動スキップ
            '--disable-background-timer-throttling',  # パフォーマンス
            '--disable-backgrounding-occluded-windows',  # パフォーマンス
            '--disable-renderer-backgrounding', # パフォーマンス
            '--disable-features=TranslateUI',   # UI簡素化
            '--disable-ipc-flooding-protection', # WSL2互換性
            '--window-size=1920,1080',         # デフォルトサイズ
            '--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        ]
        
        # ヘッドレスモード
        if headless:
            base_args.append('--headless')
        
        # 追加引数
        if extra_args:
            base_args.extend(extra_args)
        
        # オプション追加
        for arg in base_args:
            options.add_argument(arg)
        
        # 詳細設定
        options.add_experimental_option('excludeSwitches', ['enable-automation'])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Chrome DevTools Protocol設定
        options.add_experimental_option('detach', True)
        
        return options
    
    def _create_service(self) -> Service:
        """ChromeDriver サービス作成"""
        service = Service(
            executable_path=self.chromedriver_binary,
            log_level='INFO',  # デバッグ用にINFOレベル
        )
        return service
    
    def create_driver(self, headless: bool = True, extra_args: list = None, timeout: int = 30) -> webdriver.Chrome:
        """Chrome for Testing WebDriver 作成"""
        print("🚀 Chrome for Testing WebDriver 作成開始")
        print("=" * 50)
        
        try:
            # オプション作成
            options = self._create_chrome_options(headless, extra_args)
            print("✅ Chrome オプション設定完了")
            
            # サービス作成
            self.service = self._create_service()
            print("✅ ChromeDriver サービス作成完了")
            
            # WebDriver作成（タイムアウト付き）
            print("🔗 WebDriver接続開始...")
            start_time = time.time()
            
            self.driver = webdriver.Chrome(service=self.service, options=options)
            
            # WebDriver プロパティ隠蔽（Bot検知回避）
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            # タイムアウト設定
            self.driver.set_page_load_timeout(timeout)
            self.driver.implicitly_wait(10)
            
            connection_time = time.time() - start_time
            print(f"✅ WebDriver接続成功 ({connection_time:.2f}秒)")
            
            # 接続テスト
            print("🧪 接続テスト実行...")
            test_start = time.time()
            self.driver.get("data:text/html,<html><body>Chrome for Testing Ready</body></html>")
            test_time = time.time() - test_start
            print(f"✅ 基本動作確認完了 ({test_time:.2f}秒)")
            
            self.is_running = True
            
            print("🎉 Chrome for Testing WebDriver 準備完了！")
            return self.driver
            
        except Exception as e:
            print(f"❌ Chrome for Testing WebDriver 作成失敗: {e}")
            self.cleanup()
            raise
    
    def restart_driver(self, headless: bool = True, extra_args: list = None) -> webdriver.Chrome:
        """WebDriver 再起動"""
        print("🔄 Chrome for Testing WebDriver 再起動...")
        
        self.cleanup()
        time.sleep(2)  # クリーンアップ待機
        
        return self.create_driver(headless, extra_args)
    
    def is_driver_alive(self) -> bool:
        """WebDriver 生存確認"""
        if not self.driver or not self.is_running:
            return False
        
        try:
            # 簡単な操作でセッション確認
            self.driver.current_url
            return True
        except Exception:
            return False
    
    def get_driver_info(self) -> dict:
        """WebDriver 情報取得"""
        if not self.is_driver_alive():
            return {"status": "not_running"}
        
        try:
            capabilities = self.driver.capabilities
            return {
                "status": "running",
                "browser_name": capabilities.get("browserName", "unknown"),
                "browser_version": capabilities.get("browserVersion", "unknown"),
                "chrome_driver_version": capabilities.get("chrome", {}).get("chromedriverVersion", "unknown"),
                "current_url": self.driver.current_url,
                "window_handles": len(self.driver.window_handles),
                "chrome_binary": self.chrome_binary,
                "chromedriver_binary": self.chromedriver_binary
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def cleanup(self):
        """リソースクリーンアップ"""
        print("🧹 Chrome for Testing リソースクリーンアップ...")
        
        # WebDriver終了
        if self.driver:
            try:
                self.driver.quit()
                print("✅ WebDriver終了")
            except Exception as e:
                print(f"⚠️ WebDriver終了エラー: {e}")
            self.driver = None
        
        # Service終了
        if self.service:
            try:
                self.service.stop()
                print("✅ ChromeDriver Service終了")
            except Exception as e:
                print(f"⚠️ Service終了エラー: {e}")
            self.service = None
        
        self.is_running = False
        print("✅ クリーンアップ完了")
    
    def __enter__(self):
        """Context Manager 開始"""
        return self.create_driver()
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context Manager 終了"""
        self.cleanup()

# 使用例とテスト関数
def test_chrome_for_testing_manager():
    """Chrome for Testing マネージャーのテスト"""
    print("🧪 Chrome for Testing マネージャーテスト開始")
    print("=" * 50)
    
    try:
        manager = ChromeForTestingManager()
        
        # Context Manager テスト
        with manager as driver:
            print("🌐 Google アクセステスト...")
            driver.get("https://www.google.com")
            
            title = driver.title
            print(f"✅ ページタイトル: {title}")
            
            current_url = driver.current_url
            print(f"📍 現在のURL: {current_url}")
            
            # WebDriver情報表示
            info = manager.get_driver_info()
            print(f"📊 ブラウザ: {info.get('browser_name')} {info.get('browser_version')}")
            print(f"📊 ChromeDriver: {info.get('chrome_driver_version')}")
            
            # 簡単な要素操作テスト
            try:
                search_box = driver.find_element("name", "q")
                search_box.send_keys("Chrome for Testing WSL2")
                print("✅ 要素操作成功")
            except Exception as e:
                print(f"⚠️ 要素操作エラー: {e}")
        
        print("\n🎉 Chrome for Testing マネージャーテスト成功！")
        print("🚀 Amazon Kindle スクレイパー実装準備完了")
        return True
        
    except Exception as e:
        print(f"❌ テストエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_chrome_for_testing_manager()
    sys.exit(0 if success else 1)
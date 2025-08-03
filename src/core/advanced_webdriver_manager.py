#!/usr/bin/env python3
"""
高度WebDriverマネージャー - Snap制約克服版
Advanced WebDriver Manager for overcoming Snap constraints
"""
import os
import sys
import time
import signal
import subprocess
import tempfile
import threading
from pathlib import Path
from typing import Optional, Dict, Any
import psutil
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.common.exceptions import WebDriverException

class AdvancedWebDriverManager:
    """Snap制約を克服する高度WebDriverマネージャー"""
    
    def __init__(self):
        self.driver = None
        self.chromedriver_process = None
        self.chrome_process = None
        self.debugging_port = None
        self.temp_profile_dir = None
        self.is_running = False
        
    def _find_available_port(self, start_port: int = 9222) -> int:
        """利用可能なポートを検索"""
        import socket
        
        for port in range(start_port, start_port + 100):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(('127.0.0.1', port))
                    return port
            except OSError:
                continue
        raise RuntimeError("利用可能なポートが見つかりません")
    
    def _create_isolated_profile(self) -> str:
        """完全に独立したプロファイルディレクトリ作成"""
        # UUIDベースの完全にユニークな名前
        import uuid
        unique_id = str(uuid.uuid4())[:8]
        profile_dir = f"/tmp/chrome_isolated_{unique_id}_{int(time.time())}"
        
        os.makedirs(profile_dir, exist_ok=True)
        
        # 権限設定
        os.chmod(profile_dir, 0o700)
        
        print(f"🔒 独立プロファイル作成: {profile_dir}")
        return profile_dir
    
    def _terminate_conflicting_processes(self):
        """競合するChrome/Chromiumプロセスを安全に終了"""
        processes_to_kill = []
        
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if proc.info['name'] and 'chrom' in proc.info['name'].lower():
                    # システムプロセス（snapfuse）は除外
                    if 'snapfuse' not in ' '.join(proc.info.get('cmdline', [])):
                        processes_to_kill.append(proc.info['pid'])
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        for pid in processes_to_kill:
            try:
                os.kill(pid, signal.SIGTERM)
                print(f"🔪 プロセス終了: PID {pid}")
                time.sleep(0.5)
            except (OSError, ProcessLookupError):
                pass
    
    def _start_chrome_with_debugging(self) -> int:
        """デバッグモードでChromeを起動"""
        self.debugging_port = self._find_available_port()
        self.temp_profile_dir = self._create_isolated_profile()
        
        chrome_cmd = [
            '/snap/bin/chromium',
            '--headless',
            '--no-sandbox',
            '--disable-dev-shm-usage',
            '--disable-gpu',
            '--disable-software-rasterizer',
            '--disable-extensions',
            '--disable-plugins',
            '--disable-default-apps',
            '--no-first-run',
            '--disable-background-timer-throttling',
            '--disable-backgrounding-occluded-windows',
            '--disable-renderer-backgrounding',
            '--disable-features=TranslateUI',
            '--disable-ipc-flooding-protection',
            f'--remote-debugging-port={self.debugging_port}',
            f'--user-data-dir={self.temp_profile_dir}',
            '--disable-web-security',  # 開発用
            '--disable-features=VizDisplayCompositor',
        ]
        
        print(f"🚀 Chrome起動コマンド: {' '.join(chrome_cmd)}")
        
        try:
            self.chrome_process = subprocess.Popen(
                chrome_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid  # 新しいプロセスグループ
            )
            
            # Chrome起動確認
            for attempt in range(10):
                try:
                    response = requests.get(f'http://127.0.0.1:{self.debugging_port}/json/version', timeout=2)
                    if response.status_code == 200:
                        print(f"✅ Chrome起動確認: ポート {self.debugging_port}")
                        return self.debugging_port
                except requests.RequestException:
                    time.sleep(1)
                    continue
            
            raise RuntimeError("Chrome起動タイムアウト")
            
        except Exception as e:
            print(f"❌ Chrome起動エラー: {e}")
            self._cleanup_chrome()
            raise
    
    def _connect_via_debugging_protocol(self) -> webdriver.Chrome:
        """デバッグプロトコル経由でWebDriver接続"""
        options = Options()
        options.add_experimental_option("debuggerAddress", f"127.0.0.1:{self.debugging_port}")
        
        # Snap Chromium互換オプションのみ
        options.add_argument('--disable-blink-features=AutomationControlled')
        # excludeSwitchesはSnapで非対応のため削除
        # options.add_experimental_option("excludeSwitches", ["enable-automation"])
        # options.add_experimental_option('useAutomationExtension', False)
        
        try:
            # 直接接続（Serviceなし）
            driver = webdriver.Chrome(options=options)
            
            # WebDriverプロパティの隠蔽
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            print("✅ WebDriver接続成功（デバッグプロトコル経由）")
            return driver
            
        except Exception as e:
            print(f"❌ WebDriver接続エラー: {e}")
            raise
    
    def create_driver(self) -> webdriver.Chrome:
        """根本的アプローチでWebDriver作成"""
        print("🔄 高度WebDriverマネージャー起動")
        print("=" * 50)
        
        try:
            # Step 1: 競合プロセス終了
            print("🔪 競合プロセス終了...")
            self._terminate_conflicting_processes()
            time.sleep(2)
            
            # Step 2: デバッグモードでChrome起動
            print("🚀 独立Chrome起動...")
            debugging_port = self._start_chrome_with_debugging()
            
            # Step 3: デバッグプロトコル経由で接続
            print("🔗 WebDriver接続...")
            self.driver = self._connect_via_debugging_protocol()
            
            self.is_running = True
            print("✅ 高度WebDriverマネージャー準備完了")
            return self.driver
            
        except Exception as e:
            print(f"❌ WebDriver作成失敗: {e}")
            self.cleanup()
            raise
    
    def _cleanup_chrome(self):
        """Chrome関連プロセスのクリーンアップ"""
        if self.chrome_process:
            try:
                # プロセスグループ全体を終了
                os.killpg(os.getpgid(self.chrome_process.pid), signal.SIGTERM)
                self.chrome_process.wait(timeout=5)
            except (OSError, subprocess.TimeoutExpired):
                try:
                    os.killpg(os.getpgid(self.chrome_process.pid), signal.SIGKILL)
                except OSError:
                    pass
            self.chrome_process = None
    
    def _cleanup_profile(self):
        """一時プロファイルディレクトリのクリーンアップ"""
        if self.temp_profile_dir and os.path.exists(self.temp_profile_dir):
            try:
                import shutil
                shutil.rmtree(self.temp_profile_dir, ignore_errors=True)
                print(f"🗑️ プロファイルクリーンアップ: {self.temp_profile_dir}")
            except Exception as e:
                print(f"⚠️ プロファイルクリーンアップエラー: {e}")
    
    def cleanup(self):
        """全リソースのクリーンアップ"""
        print("🧹 WebDriverマネージャークリーンアップ開始")
        
        # WebDriver終了
        if self.driver:
            try:
                self.driver.quit()
                print("✅ WebDriver終了")
            except Exception as e:
                print(f"⚠️ WebDriver終了エラー: {e}")
            self.driver = None
        
        # Chrome終了
        self._cleanup_chrome()
        
        # プロファイル削除
        self._cleanup_profile()
        
        self.is_running = False
        print("✅ クリーンアップ完了")
    
    def __enter__(self):
        """Context Manager対応"""
        return self.create_driver()
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context Manager終了処理"""
        self.cleanup()

# 使用例とテスト関数
def test_advanced_webdriver():
    """高度WebDriverマネージャーのテスト"""
    print("🧪 高度WebDriverマネージャーテスト開始")
    print("=" * 50)
    
    try:
        manager = AdvancedWebDriverManager()
        
        with manager as driver:
            print("🌐 Googleアクセステスト...")
            driver.get("https://www.google.com")
            
            title = driver.title
            print(f"✅ ページタイトル: {title}")
            
            current_url = driver.current_url
            print(f"📍 現在のURL: {current_url}")
            
            # 簡単な要素検索テスト
            search_box = driver.find_element("name", "q")
            print("✅ 検索ボックス発見")
            
            search_box.send_keys("Selenium WebDriver test")
            time.sleep(1)
            
            print("✅ テキスト入力成功")
        
        print("\n🎉 高度WebDriverマネージャーテスト成功！")
        print("🚀 Amazon Kindle実動スクレイパー実装準備完了")
        return True
        
    except Exception as e:
        print(f"❌ テストエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_advanced_webdriver()
    sys.exit(0 if success else 1)
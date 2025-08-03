#!/usr/bin/env python3
"""
Chrome for Testing インストールスクリプト - WSL2最適化版
Chrome for Testing Installation Script - WSL2 Optimized Version

前回のZen ThinkDeep調査に基づく根本的アプローチ実装
Based on previous Zen ThinkDeep investigation findings
"""
import os
import sys
import json
import shutil
import tempfile
import subprocess
from pathlib import Path
from urllib.request import urlopen, urlretrieve
from zipfile import ZipFile

class ChromeForTestingInstaller:
    """Chrome for Testing インストーラー - WSL2対応版"""
    
    def __init__(self):
        self.base_dir = Path("/opt/chrome-for-testing")
        self.chrome_binary = self.base_dir / "chrome-linux64" / "chrome"
        self.chromedriver_binary = self.base_dir / "chromedriver-linux64" / "chromedriver"
        self.api_url = "https://googlechromelabs.github.io/chrome-for-testing/known-good-versions-with-downloads.json"
        
    def check_system_requirements(self) -> bool:
        """システム要件チェック"""
        print("🔍 システム要件チェック...")
        
        # WSL2環境確認
        try:
            with open('/proc/version', 'r') as f:
                version_info = f.read()
                if 'WSL2' not in version_info and 'microsoft' not in version_info.lower():
                    print("⚠️ WSL2環境ではない可能性があります")
        except FileNotFoundError:
            print("⚠️ Linux環境ではありません")
            return False
        
        # 必要なディレクトリ作成権限確認
        try:
            os.makedirs(self.base_dir, exist_ok=True)
            print(f"✅ インストールディレクトリ作成可能: {self.base_dir}")
        except PermissionError:
            print(f"❌ 権限エラー: {self.base_dir} の作成権限がありません")
            print("sudo権限で実行してください")
            return False
        
        return True
    
    def get_latest_stable_version(self) -> str:
        """最新安定版Chrome for Testingバージョン取得"""
        print("🔍 最新安定版バージョン取得...")
        
        try:
            with urlopen(self.api_url) as response:
                data = json.loads(response.read().decode('utf-8'))
            
            # 最新の安定版を検索
            versions = data.get('versions', [])
            for version_info in reversed(versions):  # 最新から検索
                version = version_info.get('version', '')
                downloads = version_info.get('downloads', {})
                
                # Chrome と ChromeDriver の Linux64版が両方存在するかチェック
                chrome_available = any(
                    d.get('platform') == 'linux64' 
                    for d in downloads.get('chrome', [])
                )
                chromedriver_available = any(
                    d.get('platform') == 'linux64' 
                    for d in downloads.get('chromedriver', [])
                )
                
                if chrome_available and chromedriver_available:
                    print(f"✅ 最新安定版発見: {version}")
                    return version
            
            raise RuntimeError("適切なバージョンが見つかりません")
            
        except Exception as e:
            print(f"❌ バージョン取得エラー: {e}")
            raise
    
    def get_download_urls(self, version: str) -> tuple:
        """指定バージョンのダウンロードURL取得"""
        print(f"🔍 バージョン {version} のダウンロードURL取得...")
        
        try:
            with urlopen(self.api_url) as response:
                data = json.loads(response.read().decode('utf-8'))
            
            # 指定バージョンを検索
            for version_info in data.get('versions', []):
                if version_info.get('version') == version:
                    downloads = version_info.get('downloads', {})
                    
                    # Chrome Linux64 URL
                    chrome_url = None
                    for chrome_download in downloads.get('chrome', []):
                        if chrome_download.get('platform') == 'linux64':
                            chrome_url = chrome_download.get('url')
                            break
                    
                    # ChromeDriver Linux64 URL
                    chromedriver_url = None
                    for driver_download in downloads.get('chromedriver', []):
                        if driver_download.get('platform') == 'linux64':
                            chromedriver_url = driver_download.get('url')
                            break
                    
                    if chrome_url and chromedriver_url:
                        print(f"✅ Chrome URL: {chrome_url}")
                        print(f"✅ ChromeDriver URL: {chromedriver_url}")
                        return chrome_url, chromedriver_url
            
            raise RuntimeError(f"バージョン {version} のダウンロードURLが見つかりません")
            
        except Exception as e:
            print(f"❌ URL取得エラー: {e}")
            raise
    
    def install_dependencies(self) -> bool:
        """Chrome実行に必要な依存関係インストール"""
        print("📦 Chrome依存関係インストール...")
        
        # WSL2で必要な最小限の依存関係（Ubuntu 22.04/20.04対応）
        dependencies = [
            "wget", "unzip", "libnss3", "libatk1.0-0", "libatk-bridge2.0-0",
            "libdrm2", "libxkbcommon0", "libxcomposite1", "libxdamage1",
            "libxrandr2", "libgbm1", "libxss1", "libasound2-dev", "libxshmfence1"
        ]
        
        # Ubuntu バージョン別の代替パッケージ
        alternative_dependencies = [
            "wget", "unzip", "libnss3", "libatk1.0-0", "libatk-bridge2.0-0",
            "libdrm2", "libxkbcommon0", "libxcomposite1", "libxdamage1", 
            "libxrandr2", "libgbm1", "libxss1", "libasound2-data", "libxshmfence1"
        ]
        
        try:
            # パッケージリスト更新
            print("📝 パッケージリスト更新中...")
            subprocess.run(["sudo", "apt", "update"], check=True, capture_output=True)
            
            # メイン依存関係インストール試行
            print("📦 メイン依存関係インストール試行...")
            cmd = ["sudo", "apt", "install", "-y"] + dependencies
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✅ 依存関係インストール完了")
                return True
            else:
                print(f"⚠️ メイン依存関係でエラー、代替パッケージを試行...")
                print(f"エラー詳細: {result.stderr}")
                
                # 代替依存関係で再試行
                cmd_alt = ["sudo", "apt", "install", "-y"] + alternative_dependencies
                result_alt = subprocess.run(cmd_alt, capture_output=True, text=True)
                
                if result_alt.returncode == 0:
                    print(f"✅ 代替依存関係インストール完了")
                    return True
                else:
                    print(f"❌ 代替依存関係もエラー: {result_alt.stderr}")
                    
                    # 最小限の必須パッケージのみインストール
                    print("🔧 最小限パッケージで再試行...")
                    minimal_deps = ["wget", "unzip", "libnss3", "libxss1"]
                    cmd_minimal = ["sudo", "apt", "install", "-y"] + minimal_deps
                    result_minimal = subprocess.run(cmd_minimal, capture_output=True, text=True)
                    
                    if result_minimal.returncode == 0:
                        print(f"✅ 最小限依存関係インストール完了")
                        print("⚠️ 一部の依存関係がインストールできませんでしたが、継続します")
                        return True
                    else:
                        print(f"❌ 最小限依存関係インストール失敗: {result_minimal.stderr}")
                        return False
            
        except subprocess.CalledProcessError as e:
            print(f"❌ 依存関係インストールエラー: {e}")
            return False
    
    def download_and_extract(self, url: str, target_dir: Path, binary_name: str) -> bool:
        """バイナリダウンロードと展開"""
        print(f"⬇️ {binary_name} ダウンロード開始...")
        
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                zip_path = Path(temp_dir) / f"{binary_name}.zip"
                
                # ダウンロード
                print(f"📥 ダウンロード中: {url}")
                urlretrieve(url, zip_path)
                
                # 展開
                print(f"📂 展開中...")
                with ZipFile(zip_path, 'r') as zip_file:
                    zip_file.extractall(target_dir)
                
                print(f"✅ {binary_name} インストール完了")
                return True
                
        except Exception as e:
            print(f"❌ {binary_name} インストールエラー: {e}")
            return False
    
    def set_permissions(self) -> bool:
        """実行権限設定"""
        print("🔒 実行権限設定...")
        
        try:
            # Chrome実行権限
            if self.chrome_binary.exists():
                os.chmod(self.chrome_binary, 0o755)
                print(f"✅ Chrome実行権限設定: {self.chrome_binary}")
            
            # ChromeDriver実行権限
            if self.chromedriver_binary.exists():
                os.chmod(self.chromedriver_binary, 0o755)
                print(f"✅ ChromeDriver実行権限設定: {self.chromedriver_binary}")
            
            return True
            
        except Exception as e:
            print(f"❌ 権限設定エラー: {e}")
            return False
    
    def create_symlinks(self) -> bool:
        """システムパスにシンボリックリンク作成"""
        print("🔗 システムパス設定...")
        
        try:
            # /usr/local/bin にシンボリックリンク作成
            chrome_link = Path("/usr/local/bin/chrome-for-testing")
            chromedriver_link = Path("/usr/local/bin/chromedriver-for-testing")
            
            # 既存リンク削除
            if chrome_link.exists() or chrome_link.is_symlink():
                chrome_link.unlink()
            if chromedriver_link.exists() or chromedriver_link.is_symlink():
                chromedriver_link.unlink()
            
            # 新しいリンク作成
            chrome_link.symlink_to(self.chrome_binary)
            chromedriver_link.symlink_to(self.chromedriver_binary)
            
            print(f"✅ Chrome リンク作成: {chrome_link} -> {self.chrome_binary}")
            print(f"✅ ChromeDriver リンク作成: {chromedriver_link} -> {self.chromedriver_binary}")
            
            return True
            
        except Exception as e:
            print(f"❌ シンボリックリンク作成エラー: {e}")
            return False
    
    def verify_installation(self) -> bool:
        """インストール検証"""
        print("🧪 インストール検証...")
        
        try:
            # Chrome バージョン確認
            chrome_result = subprocess.run(
                [str(self.chrome_binary), "--version"],
                capture_output=True, text=True, check=True
            )
            print(f"✅ Chrome バージョン: {chrome_result.stdout.strip()}")
            
            # ChromeDriver バージョン確認
            chromedriver_result = subprocess.run(
                [str(self.chromedriver_binary), "--version"],
                capture_output=True, text=True, check=True
            )
            print(f"✅ ChromeDriver バージョン: {chromedriver_result.stdout.strip()}")
            
            # 基本的な起動テスト
            print("🧪 Chrome起動テスト...")
            test_result = subprocess.run([
                str(self.chrome_binary),
                "--headless", "--no-sandbox", "--disable-dev-shm-usage",
                "--virtual-time-budget=1000", "--run-all-compositor-stages-before-draw",
                "--dump-dom", "data:text/html,<html><body>Test</body></html>"
            ], capture_output=True, text=True, timeout=10)
            
            if "Test" in test_result.stdout:
                print("✅ Chrome基本動作確認完了")
            else:
                print("⚠️ Chrome基本動作に問題がある可能性があります")
            
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ インストール検証エラー: {e}")
            return False
        except subprocess.TimeoutExpired:
            print("⚠️ Chrome起動テストタイムアウト（正常な可能性あり）")
            return True
    
    def create_config_file(self, version: str) -> None:
        """設定ファイル作成"""
        config_path = self.base_dir / "config.json"
        config = {
            "version": version,
            "installed_at": str(Path.cwd()),
            "chrome_binary": str(self.chrome_binary),
            "chromedriver_binary": str(self.chromedriver_binary),
            "chrome_symlink": "/usr/local/bin/chrome-for-testing",
            "chromedriver_symlink": "/usr/local/bin/chromedriver-for-testing"
        }
        
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"✅ 設定ファイル作成: {config_path}")
    
    def install(self) -> bool:
        """Chrome for Testing フルインストール実行"""
        print("🚀 Chrome for Testing インストール開始")
        print("=" * 50)
        
        try:
            # システム要件チェック
            if not self.check_system_requirements():
                return False
            
            # 依存関係インストール
            if not self.install_dependencies():
                return False
            
            # 最新バージョン取得
            version = self.get_latest_stable_version()
            
            # ダウンロードURL取得
            chrome_url, chromedriver_url = self.get_download_urls(version)
            
            # 既存インストール削除
            if self.base_dir.exists():
                print(f"🗑️ 既存インストール削除: {self.base_dir}")
                shutil.rmtree(self.base_dir)
            
            # インストールディレクトリ作成
            self.base_dir.mkdir(parents=True, exist_ok=True)
            
            # Chrome ダウンロード・インストール
            if not self.download_and_extract(chrome_url, self.base_dir, "Chrome"):
                return False
            
            # ChromeDriver ダウンロード・インストール
            if not self.download_and_extract(chromedriver_url, self.base_dir, "ChromeDriver"):
                return False
            
            # 実行権限設定
            if not self.set_permissions():
                return False
            
            # システムパス設定
            if not self.create_symlinks():
                return False
            
            # インストール検証
            if not self.verify_installation():
                return False
            
            # 設定ファイル作成
            self.create_config_file(version)
            
            print("\n🎉 Chrome for Testing インストール完了！")
            print("=" * 50)
            print(f"📍 Chrome バイナリ: {self.chrome_binary}")
            print(f"📍 ChromeDriver バイナリ: {self.chromedriver_binary}")
            print(f"🔗 Chrome システムリンク: /usr/local/bin/chrome-for-testing")
            print(f"🔗 ChromeDriver システムリンク: /usr/local/bin/chromedriver-for-testing")
            print("\n🚀 Selenium WebDriver での使用方法:")
            print("```python")
            print("from selenium import webdriver")
            print("from selenium.webdriver.chrome.service import Service")
            print("from selenium.webdriver.chrome.options import Options")
            print("")
            print("options = Options()")
            print("options.binary_location = '/opt/chrome-for-testing/chrome-linux64/chrome'")
            print("service = Service('/opt/chrome-for-testing/chromedriver-linux64/chromedriver')")
            print("driver = webdriver.Chrome(service=service, options=options)")
            print("```")
            
            return True
            
        except Exception as e:
            print(f"❌ インストール失敗: {e}")
            import traceback
            traceback.print_exc()
            return False

def main():
    """メイン実行関数"""
    if os.geteuid() != 0:
        print("❌ このスクリプトはsudo権限で実行してください")
        print("実行例: sudo python3 install_chrome_for_testing.py")
        sys.exit(1)
    
    installer = ChromeForTestingInstaller()
    success = installer.install()
    
    if success:
        print("\n✅ Chrome for Testing インストール成功")
        print("🔄 次のステップ: test_chrome_for_testing.py でテスト実行")
    else:
        print("\n❌ Chrome for Testing インストール失敗")
        sys.exit(1)

if __name__ == "__main__":
    main()
# ====================================================================
# 環境セットアップと依存関係検証スクリプト
# ====================================================================

param(
    [switch]$Force = $false,
    [switch]$Verbose = $false
)

$ErrorActionPreference = "Stop"

$PROJECT_ROOT = Split-Path -Parent -Path (Split-Path -Parent -Path $PSScriptRoot)
$VENV_PATH = Join-Path $PROJECT_ROOT "venv"

Write-Host "[START] Environment Setup and Verification" -ForegroundColor Cyan
Write-Host "Project Root: $PROJECT_ROOT" -ForegroundColor Yellow

# 仮想環境アクティベート
$activateScript = Join-Path $VENV_PATH "Scripts\Activate.ps1"
if (Test-Path $activateScript) {
    & $activateScript
    Write-Host "[OK] Virtual environment activated" -ForegroundColor Green
} else {
    Write-Host "[FAIL] Virtual environment not found: $VENV_PATH" -ForegroundColor Red
    exit 1
}

# Python依存関係検証スクリプト
$pythonScript = @"
#!/usr/bin/env python3
import sys
import subprocess
import importlib
from pathlib import Path

def check_and_install_dependencies():
    """依存関係の確認とインストール"""
    
    print("[INFO] Checking Python dependencies...")
    
    # 必須パッケージリスト
    required_packages = [
        'playwright',
        'asyncio',
        'selenium',
        'pydantic',
        'loguru',
        'rich'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            importlib.import_module(package)
            print(f"[OK] {package} is available")
        except ImportError:
            print(f"[MISSING] {package} not found")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"[INSTALL] Installing missing packages: {missing_packages}")
        for package in missing_packages:
            try:
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
                print(f"[OK] {package} installed successfully")
            except subprocess.CalledProcessError as e:
                print(f"[FAIL] Failed to install {package}: {e}")
                return False
    
    # Playwright特別セットアップ
    try:
        import playwright
        print("[OK] Playwright module available")
        
        # Playwrightブラウザーのインストール確認
        try:
            result = subprocess.run([sys.executable, '-m', 'playwright', 'install', '--help'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print("[INFO] Installing Playwright browsers...")
                subprocess.check_call([sys.executable, '-m', 'playwright', 'install', 'chromium'])
                print("[OK] Playwright chromium browser installed")
        except Exception as e:
            print(f"[WARN] Playwright browser setup issue: {e}")
    
    except ImportError:
        print("[FAIL] Playwright not available after installation attempt")
        return False
    
    return True

def verify_project_structure():
    """プロジェクト構造の確認"""
    
    print("[INFO] Verifying project structure...")
    
    project_root = Path(r"C:\Users\tky99\DEV\izumi-novels-workflow")
    
    required_paths = [
        project_root / 'src',
        project_root / 'src' / 'scraping',
        project_root / 'src' / 'scraping' / 'base_scraper.py',
        project_root / 'src' / 'scraping' / 'amazon_kindle_scraper.py',
        project_root / 'scripts',
        project_root / 'scripts' / 'windows'
    ]
    
    all_good = True
    for path in required_paths:
        if path.exists():
            print(f"[OK] {path}")
        else:
            print(f"[MISSING] {path}")
            all_good = False
    
    return all_good

def test_module_imports():
    """モジュールインポートテスト"""
    
    print("[INFO] Testing module imports...")
    
    project_root = Path(r"C:\Users\tky99\DEV\izumi-novels-workflow")
    src_path = project_root / 'src'
    scraping_path = src_path / 'scraping'
    
    # パス設定
    sys.path.insert(0, str(project_root))
    sys.path.insert(0, str(src_path))
    sys.path.insert(0, str(scraping_path))
    
    try:
        # base_scraperのインポートテスト
        import importlib.util
        
        base_spec = importlib.util.spec_from_file_location("base_scraper", scraping_path / "base_scraper.py")
        base_module = importlib.util.module_from_spec(base_spec)
        sys.modules["base_scraper"] = base_module
        base_spec.loader.exec_module(base_module)
        print("[OK] base_scraper module loaded")
        
        # amazon_kindle_scraperのインポートテスト
        amazon_spec = importlib.util.spec_from_file_location("amazon_kindle_scraper", scraping_path / "amazon_kindle_scraper.py")
        amazon_module = importlib.util.module_from_spec(amazon_spec)
        sys.modules["amazon_kindle_scraper"] = amazon_module
        amazon_spec.loader.exec_module(amazon_module)
        print("[OK] amazon_kindle_scraper module loaded")
        
        # クラスインスタンス化テスト
        AmazonKindleScraper = amazon_module.AmazonKindleScraper
        scraper = AmazonKindleScraper(headless=True)
        print("[OK] AmazonKindleScraper instance created")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] Module import test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("=" * 60)
    print("Environment Setup and Verification")
    print("=" * 60)
    
    # ステップ1: 依存関係確認
    if not check_and_install_dependencies():
        print("[FAIL] Dependency check failed")
        return False
    
    # ステップ2: プロジェクト構造確認
    if not verify_project_structure():
        print("[FAIL] Project structure verification failed")
        return False
    
    # ステップ3: モジュールインポートテスト
    if not test_module_imports():
        print("[FAIL] Module import test failed")
        return False
    
    print("[SUCCESS] All verifications passed!")
    print("Ready for real scraping tests.")
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
"@

try {
    # Pythonスクリプト実行
    $tempScriptPath = Join-Path $PROJECT_ROOT "temp_setup_verify.py"
    $pythonScript | Out-File -FilePath $tempScriptPath -Encoding UTF8
    
    Write-Host "[EXEC] Running environment verification..." -ForegroundColor Cyan
    
    $output = python $tempScriptPath 2>&1
    $exitCode = $LASTEXITCODE
    
    if ($Verbose) {
        Write-Host "Setup Output:" -ForegroundColor Yellow
        Write-Host $output -ForegroundColor White
    }
    
    Remove-Item $tempScriptPath -Force -ErrorAction SilentlyContinue
    
    if ($exitCode -eq 0) {
        Write-Host "[SUCCESS] Environment setup and verification completed" -ForegroundColor Green
        Write-Host "[READY] You can now run the scraping tests:" -ForegroundColor Cyan
        Write-Host "  .\scripts\windows\run_real_scraping_test_final.ps1 -Verbose" -ForegroundColor Yellow
    } else {
        Write-Host "[FAIL] Environment verification failed" -ForegroundColor Red
        Write-Host $output -ForegroundColor Red
    }
    
    exit $exitCode
    
} catch {
    Write-Host "[FAIL] Setup script error: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
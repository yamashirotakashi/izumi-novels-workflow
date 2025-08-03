# ====================================================================
# モジュールインポート問題デバッグスクリプト
# ====================================================================

param(
    [switch]$Verbose = $false
)

$ErrorActionPreference = "Stop"

$PROJECT_ROOT = Split-Path -Parent -Path (Split-Path -Parent -Path $PSScriptRoot)
$VENV_PATH = Join-Path $PROJECT_ROOT "venv"

Write-Host "[DEBUG] Module Import Debugging Test" -ForegroundColor Cyan
Write-Host "Project Root: $PROJECT_ROOT" -ForegroundColor Yellow

# 簡単なインポートテストスクリプト
$pythonScript = @"
#!/usr/bin/env python3
import sys
import os
from pathlib import Path

# プロジェクトルートの設定
project_root = Path(__file__).parent.parent.parent
src_path = project_root / 'src'
scraping_path = src_path / 'scraping'

print(f"[INFO] Project root: {project_root}")
print(f"[INFO] Src path: {src_path}")
print(f"[INFO] Scraping path: {scraping_path}")
print(f"[INFO] Src exists: {src_path.exists()}")
print(f"[INFO] Scraping exists: {scraping_path.exists()}")

# sys.pathに追加
sys.path.insert(0, str(src_path))
sys.path.insert(0, str(scraping_path))

print(f"[INFO] Python sys.path (first 5):")
for i, path in enumerate(sys.path[:5]):
    print(f"  {i+1}. {path}")

# ディレクトリ内容確認
print(f"[INFO] Files in scraping directory:")
if scraping_path.exists():
    for file in scraping_path.glob('*.py'):
        print(f"  - {file.name}")

# 段階的インポートテスト
print("\n[TEST] Step 1: Try importing scraping module")
try:
    import scraping
    print("[OK] scraping module imported")
    print(f"[INFO] scraping module path: {scraping.__file__}")
except ImportError as e:
    print(f"[FAIL] scraping import failed: {e}")

print("\n[TEST] Step 2: Try importing base_scraper directly")
try:
    sys.path.insert(0, str(scraping_path))
    import base_scraper
    print("[OK] base_scraper imported directly")
except ImportError as e:
    print(f"[FAIL] base_scraper import failed: {e}")

print("\n[TEST] Step 3: Try importing amazon_kindle_scraper directly")
try:
    import amazon_kindle_scraper
    print("[OK] amazon_kindle_scraper imported directly")
    if hasattr(amazon_kindle_scraper, 'AmazonKindleScraper'):
        print("[OK] AmazonKindleScraper class found")
    else:
        print("[WARN] AmazonKindleScraper class not found")
except ImportError as e:
    print(f"[FAIL] amazon_kindle_scraper import failed: {e}")

print("\n[TEST] Step 4: Try scraping.amazon_kindle_scraper import")
try:
    from scraping import amazon_kindle_scraper
    print("[OK] scraping.amazon_kindle_scraper imported")
except ImportError as e:
    print(f"[FAIL] scraping.amazon_kindle_scraper import failed: {e}")

print("\n[TEST] Step 5: Try creating AmazonKindleScraper instance")
try:
    # 最も成功したインポート方法を使用
    if 'amazon_kindle_scraper' in locals():
        scraper_class = amazon_kindle_scraper.AmazonKindleScraper
    else:
        from scraping.amazon_kindle_scraper import AmazonKindleScraper as scraper_class
    
    # インスタンス作成テスト（実際のスクレイピングは行わない）
    print("[INFO] Attempting to create scraper instance...")
    # scraper = scraper_class()  # 依存関係の問題があるかもしれないので一旦コメントアウト
    print("[OK] Scraper class accessible")
except Exception as e:
    print(f"[FAIL] Scraper instantiation failed: {e}")
    import traceback
    traceback.print_exc()

print("\n[COMPLETE] Import debugging finished")
"@

$tempScriptPath = Join-Path $PROJECT_ROOT "temp_import_debug.py"

try {
    # Pythonスクリプト保存
    $pythonScript | Out-File -FilePath $tempScriptPath -Encoding UTF8
    
    # 仮想環境アクティベート
    $activateScript = Join-Path $VENV_PATH "Scripts\Activate.ps1"
    if (Test-Path $activateScript) {
        & $activateScript
        Write-Host "[INFO] Virtual environment activated" -ForegroundColor Green
    } else {
        Write-Host "[WARN] Virtual environment not found, using system Python" -ForegroundColor Yellow
    }
    
    Write-Host "[TEST] Running import debugging test..." -ForegroundColor Cyan
    
    # Pythonスクリプト実行
    python $tempScriptPath
    $exitCode = $LASTEXITCODE
    
    if ($exitCode -eq 0) {
        Write-Host "[OK] Import debugging completed successfully" -ForegroundColor Green
    } else {
        Write-Host "[FAIL] Import debugging failed with exit code: $exitCode" -ForegroundColor Red
    }
    
    # 一時ファイル削除
    Remove-Item $tempScriptPath -Force -ErrorAction SilentlyContinue
    
} catch {
    Write-Host "[FAIL] Script execution error: $($_.Exception.Message)" -ForegroundColor Red
    Remove-Item $tempScriptPath -Force -ErrorAction SilentlyContinue
    exit 1
}
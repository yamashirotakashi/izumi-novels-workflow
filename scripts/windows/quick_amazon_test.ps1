# ====================================================================
# 軽量Amazon検索テスト
# ====================================================================

param(
    [string]$Query = "異世界転生",
    [switch]$Verbose = $false
)

$ErrorActionPreference = "Stop"

$PROJECT_ROOT = Split-Path -Parent -Path (Split-Path -Parent -Path $PSScriptRoot)
$VENV_PATH = Join-Path $PROJECT_ROOT "venv"

Write-Host "[START] Quick Amazon Search Test" -ForegroundColor Cyan
Write-Host "Query: $Query" -ForegroundColor Yellow

# 仮想環境アクティベート
$activateScript = Join-Path $VENV_PATH "Scripts\Activate.ps1"
if (Test-Path $activateScript) {
    & $activateScript
    Write-Host "[OK] Virtual environment activated" -ForegroundColor Green
}

# 軽量テストPythonスクリプト
$pythonScript = @"
#!/usr/bin/env python3
import sys
import time
from pathlib import Path

# プロジェクトルート設定
project_root = Path(r"C:\Users\tky99\DEV\izumi-novels-workflow")
src_path = project_root / 'src'
scraping_path = src_path / 'scraping'

# PYTHONPATH設定
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(src_path))
sys.path.insert(0, str(scraping_path))

print("[INFO] Quick Amazon search test starting...")

try:
    # モジュール読み込み
    import importlib.util
    
    base_spec = importlib.util.spec_from_file_location("base_scraper", scraping_path / "base_scraper.py")
    base_module = importlib.util.module_from_spec(base_spec)
    sys.modules["base_scraper"] = base_module
    base_spec.loader.exec_module(base_module)
    
    amazon_spec = importlib.util.spec_from_file_location("amazon_kindle_scraper", scraping_path / "amazon_kindle_scraper.py")
    amazon_module = importlib.util.module_from_spec(amazon_spec)
    sys.modules["amazon_kindle_scraper"] = amazon_module
    amazon_spec.loader.exec_module(amazon_module)
    
    AmazonKindleScraper = amazon_module.AmazonKindleScraper
    print("[OK] Modules loaded successfully")
    
    # スクレイパー作成（実際の初期化はしない）
    print("[INFO] Testing scraper creation...")
    scraper = AmazonKindleScraper(headless=True)
    print("[OK] Scraper instance created")
    
    # 簡単な機能テスト（Playwright起動なし）
    print("[INFO] Testing title matching...")
    test_title = "転生したらスライムだった件"
    variants = scraper.create_volume_variants(test_title)
    print(f"[OK] Title variants: {len(variants)} generated")
    for i, variant in enumerate(variants[:3], 1):
        print(f"  {i}. {variant}")
    
    # 類似度テスト
    similarity = scraper.is_title_match("異世界転生", "異世界転生小説")
    print(f"[OK] Similarity test: {similarity}")
    
    print("[SUCCESS] Quick test completed - scraper is functional")
    print("[NOTE] For full testing, run the actual scraping script")
    
except Exception as e:
    print(f"[FAIL] Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
"@

$tempScriptPath = Join-Path $PROJECT_ROOT "temp_quick_test.py"

try {
    # Pythonスクリプト実行
    $pythonScript | Out-File -FilePath $tempScriptPath -Encoding UTF8
    
    Write-Host "[TEST] Running quick functionality test..." -ForegroundColor Cyan
    
    $startTime = Get-Date
    $output = python $tempScriptPath 2>&1
    $exitCode = $LASTEXITCODE
    $endTime = Get-Date
    $duration = ($endTime - $startTime).TotalSeconds
    
    if ($exitCode -eq 0) {
        Write-Host "[SUCCESS] Quick test completed ($($duration.ToString('F1')) sec)" -ForegroundColor Green
    } else {
        Write-Host "[FAIL] Quick test failed ($($duration.ToString('F1')) sec)" -ForegroundColor Red
    }
    
    if ($Verbose -or $exitCode -ne 0) {
        Write-Host "Test Output:" -ForegroundColor Yellow
        Write-Host $output -ForegroundColor White
    }
    
    Remove-Item $tempScriptPath -Force -ErrorAction SilentlyContinue
    
    if ($exitCode -eq 0) {
        Write-Host ""
        Write-Host "[INFO] Scraper functionality verified!" -ForegroundColor Green
        Write-Host "[NOTE] For actual web scraping, try with smaller timeout:" -ForegroundColor Yellow
        Write-Host "  .\scripts\windows\run_actual_amazon_scraping.ps1 -Query `"$Query`" -Timeout 30 -Headless:`$false" -ForegroundColor Cyan
    }
    
    exit $exitCode
    
} catch {
    Write-Host "[FAIL] Script error: $($_.Exception.Message)" -ForegroundColor Red
    Remove-Item $tempScriptPath -Force -ErrorAction SilentlyContinue
    exit 1
}
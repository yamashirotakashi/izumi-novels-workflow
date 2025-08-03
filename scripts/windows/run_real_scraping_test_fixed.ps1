# ====================================================================
# IzumiNovels-Workflow Windows実スクレイピングテスト実行スクリプト（修正版）
# ====================================================================

param(
    [string]$Site = "amazon",         
    [string]$Query = "異世界転生",    
    [switch]$Headless = $false,       
    [switch]$Verbose = $false,        
    [int]$Timeout = 300              
)

$ErrorActionPreference = "Stop"

$PROJECT_ROOT = Split-Path -Parent -Path (Split-Path -Parent -Path $PSScriptRoot)
$VENV_PATH = Join-Path $PROJECT_ROOT "venv"
$SRC_PATH = Join-Path $PROJECT_ROOT "src"
$LOGS_PATH = Join-Path $PROJECT_ROOT "logs" "real_scraping"
$RESULTS_PATH = Join-Path $PROJECT_ROOT "real_scraping_results"

Write-Host "[START] IzumiNovels-Workflow Real Scraping Test" -ForegroundColor Cyan
Write-Host "Target Site: $Site" -ForegroundColor Yellow
Write-Host "Search Query: $Query" -ForegroundColor Yellow

# ディレクトリ作成
@($LOGS_PATH, $RESULTS_PATH) | ForEach-Object {
    if (-not (Test-Path $_)) {
        New-Item -ItemType Directory -Path $_ -Force | Out-Null
    }
}

# 修正版Pythonスクリプト（モジュールパス問題解決）
$pythonScript = @"
#!/usr/bin/env python3
import sys
import json
import time
import os
from pathlib import Path

# プロジェクトルートの確実な特定
script_dir = Path(__file__).parent.absolute()
project_root = script_dir.parent.parent
src_path = project_root / 'src'

# デバッグ情報
print(f"[DEBUG] Script dir: {script_dir}")
print(f"[DEBUG] Project root: {project_root}")
print(f"[DEBUG] Src path: {src_path}")
print(f"[DEBUG] Src path exists: {src_path.exists()}")

# PYTHONPATHに追加（複数の方法で確実に）
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# さらにスクレイピングディレクトリも直接追加
scraping_path = src_path / 'scraping'
if str(scraping_path) not in sys.path:
    sys.path.insert(0, str(scraping_path))

print(f"[DEBUG] Current sys.path:")
for i, path in enumerate(sys.path[:5]):  # 最初の5つのパスを表示
    print(f"  {i+1}. {path}")

def main():
    print("[QUICK] Amazon Kindle Real Scraping Test Started")
    print("=" * 50)
    
    query = "$Query"
    print(f"[TARGET] Search Query: {query}")
    
    # スクレイピングディレクトリの内容確認
    print("[INFO] Available files in src/scraping/:")
    scraping_dir = project_root / 'src' / 'scraping'
    if scraping_dir.exists():
        for file in scraping_dir.glob('*.py'):
            print(f"  - {file.name}")
    
    # Try to import scraper
    try:
        # 絶対インポートを試行
        import sys
        sys.path.insert(0, str(project_root / 'src'))
        
        # 直接インポートを試行
        import scraping.amazon_kindle_scraper as amazon_module
        AmazonKindleScraper = amazon_module.AmazonKindleScraper
        print("[OK] AmazonKindleScraper imported successfully")
    except ImportError as e:
        print(f"[FAIL] Import error: {e}")
        
        # alternative import method
        try:
            sys.path.insert(0, str(scraping_dir))
            import amazon_kindle_scraper
            AmazonKindleScraper = amazon_kindle_scraper.AmazonKindleScraper
            print("[OK] AmazonKindleScraper imported via alternative method")
        except ImportError as e2:
            print(f"[FAIL] Alternative import also failed: {e2}")
            return False
    
    # Initialize and run scraper
    try:
        scraper = AmazonKindleScraper()
        print("[OK] Scraper initialized")
        
        start_time = time.time()
        result = scraper.scrape_with_retry(query)
        execution_time = time.time() - start_time
        
        print(f"[TIME] Execution Time: {execution_time:.2f} seconds")
        print(f"[STATS] Success: {'[OK]' if result.success else '[FAIL]'}")
        print(f"[STATS] Books Found: {len(result.books_found)} items")
        print(f"[STATS] Retry Count: {result.retry_count} times")
        
        if result.error_message:
            print(f"[FAIL] Error: {result.error_message}")
        
        if result.books_found:
            print(f"[RESULT] Top 3 Books Found:")
            for i, book in enumerate(result.books_found[:3], 1):
                title = book.get('title', 'Unknown')
                url = book.get('url', 'Unknown')
                similarity = book.get('similarity_score', 0)
                print(f"  {i}. {title}")
                print(f"     URL: {url}")
                print(f"     Similarity: {similarity:.3f}")
        
        # Save results
        result_data = {
            "site": "amazon",
            "query": query,
            "success": result.success,
            "books_found": len(result.books_found),
            "execution_time": round(execution_time, 2),
            "error_message": result.error_message,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "books": result.books_found[:5]
        }
        
        result_file = "$($RESULTS_PATH -replace '\\', '\\\\')\\amazon.json"
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(result_data, f, ensure_ascii=False, indent=2)
        
        print(f"[FINISH] Results saved to: {result_file}")
        return result.success
        
    except Exception as e:
        print(f"[FAIL] Scraping execution error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
"@

$tempScriptPath = Join-Path $PROJECT_ROOT "temp_scraping_test_fixed.py"
$logFile = Join-Path $LOGS_PATH "amazon.log"

try {
    # Pythonスクリプト保存
    $pythonScript | Out-File -FilePath $tempScriptPath -Encoding UTF8
    
    # 仮想環境アクティベート
    $activateScript = Join-Path $VENV_PATH "Scripts\Activate.ps1"
    & $activateScript
    
    # 環境変数設定
    if ($Headless) { $env:HEADLESS_MODE = "true" }
    $env:TEST_TIMEOUT = $Timeout
    
    Write-Host "[TEST] Executing Amazon scraping test..." -ForegroundColor Cyan
    
    # Pythonスクリプト実行
    $startTime = Get-Date
    $testOutput = python $tempScriptPath 2>&1
    $exitCode = $LASTEXITCODE
    $endTime = Get-Date
    $duration = ($endTime - $startTime).TotalSeconds
    
    # ログ保存
    $testOutput | Out-File -FilePath $logFile -Encoding UTF8
    
    # 結果表示
    if ($exitCode -eq 0) {
        Write-Host "[OK] Amazon Real Scraping Test SUCCESS ($($duration.ToString('F1')) sec)" -ForegroundColor Green
    } else {
        Write-Host "[FAIL] Amazon Real Scraping Test FAILED ($($duration.ToString('F1')) sec)" -ForegroundColor Red
    }
    
    if ($Verbose -or $exitCode -ne 0) {
        Write-Host "Test Output:" -ForegroundColor Yellow
        Write-Host $testOutput -ForegroundColor White
    }
    
    # 結果ファイル確認
    $resultFile = Join-Path $RESULTS_PATH "amazon.json"
    if (Test-Path $resultFile) {
        Write-Host "[INFO] Result file created: $resultFile" -ForegroundColor Green
        try {
            $resultData = Get-Content $resultFile -Raw | ConvertFrom-Json
            Write-Host "[INFO] Books found: $($resultData.books_found)" -ForegroundColor Yellow
        } catch {
            Write-Host "[WARN] Could not parse result file" -ForegroundColor Yellow
        }
    }
    
    # 一時ファイル削除
    Remove-Item $tempScriptPath -Force -ErrorAction SilentlyContinue
    
    exit $exitCode
    
} catch {
    Write-Host "[FAIL] Script execution error: $($_.Exception.Message)" -ForegroundColor Red
    Remove-Item $tempScriptPath -Force -ErrorAction SilentlyContinue
    exit 1
}
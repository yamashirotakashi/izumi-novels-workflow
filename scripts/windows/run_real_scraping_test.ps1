# ====================================================================
# IzumiNovels-Workflow Windows実スクレイピングテスト実行スクリプト
# ====================================================================
# 用途: Windows PowerShell環境での実際のスクレイピング機能テスト
# 前提: setup_windows_environment.ps1 実行済み
# 実行方法: PowerShellで .\run_real_scraping_test.ps1
# ====================================================================

param(
    [string]$Site = "amazon",         # テスト対象サイト
    [string]$Query = "異世界転生",    # 検索クエリ
    [switch]$Headless = $false,       # ヘッドレスモード
    [switch]$Verbose = $false,        # 詳細出力
    [int]$Timeout = 300              # タイムアウト（秒）
)

# エラー時停止設定
$ErrorActionPreference = "Stop"

# ====================================================================
# 基本設定
# ====================================================================

$PROJECT_ROOT = Split-Path -Parent -Path (Split-Path -Parent -Path $PSScriptRoot)
$VENV_PATH = Join-Path $PROJECT_ROOT "venv"
$SRC_PATH = Join-Path $PROJECT_ROOT "src"
$LOGS_PATH = Join-Path $PROJECT_ROOT "logs" "real_scraping"
$RESULTS_PATH = Join-Path $PROJECT_ROOT "real_scraping_results"

# サイト設定マッピング
$SITE_MAPPING = @{
    "amazon" = @{
        "name" = "Amazon Kindle"
        "scraper_class" = "AmazonKindleScraper"
        "module" = "amazon_kindle_scraper"
    }
    "bookwalker" = @{
        "name" = "BOOK☆WALKER"
        "scraper_class" = "BookWalkerAdvancedScraper"
        "module" = "bookwalker_advanced_scraper"
    }
    "google" = @{
        "name" = "Google Play Books"
        "scraper_class" = "GooglePlayBooksScraper"
        "module" = "google_play_books_scraper"
    }
    "rakuten" = @{
        "name" = "Rakuten Kobo"
        "scraper_class" = "RakutenKoboScraper"
        "module" = "rakuten_kobo_scraper"
    }
}

Write-Host "[START] IzumiNovels-Workflow Real Scraping Test" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "Target Site: $Site" -ForegroundColor Yellow
Write-Host "Search Query: $Query" -ForegroundColor Yellow
Write-Host "Headless Mode: $Headless" -ForegroundColor Yellow
Write-Host "Timeout: $Timeout sec" -ForegroundColor Yellow

# ====================================================================
# ディレクトリ作成
# ====================================================================

@($LOGS_PATH, $RESULTS_PATH) | ForEach-Object {
    if (-not (Test-Path $_)) {
        New-Item -ItemType Directory -Path $_ -Force | Out-Null
        Write-Host "[OK] Directory created: $_" -ForegroundColor Green
    }
}

# ====================================================================
# 関数定義
# ====================================================================

function Write-TestLog {
    param(
        [string]$Message,
        [string]$Level = "INFO"
    )
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] [$Level] $Message"
    $logFile = Join-Path $LOGS_PATH "real_scraping_$(Get-Date -Format 'yyyyMMdd').log"
    Add-Content -Path $logFile -Value $logMessage
    if ($Verbose) { Write-Host $logMessage -ForegroundColor Gray }
}

function Test-Prerequisites {
    Write-Host "[CHECK] Prerequisites verification..." -ForegroundColor Cyan
    
    # Python仮想環境チェック
    $activateScript = Join-Path $VENV_PATH "Scripts\Activate.ps1"
    if (-not (Test-Path $activateScript)) {
        Write-Host "[FAIL] Python virtual environment not found: $VENV_PATH" -ForegroundColor Red
        return $false
    }
    
    # scraping モジュールチェック
    if (-not (Test-Path (Join-Path $SRC_PATH "scraping"))) {
        Write-Host "[FAIL] Scraping module directory not found: $SRC_PATH" -ForegroundColor Red
        return $false
    }
    
    Write-Host "[OK] Prerequisites check completed" -ForegroundColor Green
    Write-TestLog "Prerequisites check completed successfully"
    return $true
}

function Get-SiteConfig {
    param([string]$SiteName)
    
    if ($SITE_MAPPING.ContainsKey($SiteName.ToLower())) {
        return $SITE_MAPPING[$SiteName.ToLower()]
    } else {
        Write-Host "[FAIL] Unsupported site: $SiteName" -ForegroundColor Red
        Write-Host "Available sites: $($SITE_MAPPING.Keys -join ', ')" -ForegroundColor Yellow
        return $null
    }
}

function Invoke-RealScrapingTest {
    param(
        [string]$SiteName,
        [hashtable]$SiteConfig,
        [string]$SearchQuery
    )
    
    Write-Host ""
    Write-Host "[TEST] $($SiteConfig.name) Real Scraping Test Started..." -ForegroundColor Cyan
    Write-Host "-" * 50 -ForegroundColor Gray
    
    $resultFile = Join-Path $RESULTS_PATH "$SiteName.json"
    $logFile = Join-Path $LOGS_PATH "$SiteName.log"
    
    $startTime = Get-Date
    Write-TestLog "Starting real scraping test for $($SiteConfig.name) with query: $SearchQuery"
    
    # Python実スクレイピングスクリプト作成
    $pythonScript = @"
#!/usr/bin/env python3
import sys
import json
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root / 'src'))

try:
    from scraping.$($SiteConfig.module) import $($SiteConfig.scraper_class)
    
    def main():
        print(f"[QUICK] $($SiteConfig.name) Real Scraping Test Started")
        print("=" * 50)
        
        # Initialize scraper
        scraper = $($SiteConfig.scraper_class)()
        
        # Test query
        query = "$SearchQuery"
        print(f"[TARGET] Search Query: {query}")
        
        # Execute scraping
        start_time = time.time()
        try:
            result = scraper.scrape_with_retry(query)
            execution_time = time.time() - start_time
            
            # Display results
            print(f"[TIME] Execution Time: {execution_time:.2f} seconds")
            print(f"[TARGET] Site: {result.site_name}")
            print(f"[STATS] Success: {'[OK]' if result.success else '[FAIL]'}")
            print(f"[STATS] Books Found: {len(result.books_found)} items")
            print(f"[STATS] Retry Count: {result.retry_count} times")
            
            if result.error_message:
                print(f"[FAIL] Error: {result.error_message}")
            
            # Show found books
            if result.books_found:
                print(f"\n[RESULT] Found Books:")
                for i, book in enumerate(result.books_found[:3], 1):  # Show top 3
                    print(f"  {i}. Title: {book.get('title', 'Unknown')}")
                    print(f"     URL: {book.get('url', 'Unknown')}")
                    print(f"     Similarity: {book.get('similarity_score', 0):.3f}")
            
            # Save results to JSON
            result_data = {
                "site": "$SiteName",
                "site_name": result.site_name,
                "query": query,
                "success": result.success,
                "books_found": len(result.books_found),
                "retry_count": result.retry_count,
                "execution_time": round(execution_time, 2),
                "error_message": result.error_message,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "books": result.books_found[:5]  # Top 5 books
            }
            
            import json
            with open("$($resultFile -replace '\\', '\\\\')", 'w', encoding='utf-8') as f:
                json.dump(result_data, f, ensure_ascii=False, indent=2)
            
            print(f"\n[FINISH] $($SiteConfig.name) Real Scraping Test Completed")
            print(f"[FINISH] Results saved to: $($resultFile -replace '\\', '\\\\')")
            
            # Exit code based on success
            sys.exit(0 if result.success else 1)
            
        except Exception as e:
            execution_time = time.time() - start_time
            print(f"[FAIL] Scraping failed: {e}")
            print(f"[TIME] Execution Time: {execution_time:.2f} seconds")
            
            # Save error result
            error_data = {
                "site": "$SiteName",
                "site_name": "$($SiteConfig.name)",
                "query": query,
                "success": False,
                "books_found": 0,
                "retry_count": 0,
                "execution_time": round(execution_time, 2),
                "error_message": str(e),
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "books": []
            }
            
            import json
            with open("$($resultFile -replace '\\', '\\\\')", 'w', encoding='utf-8') as f:
                json.dump(error_data, f, ensure_ascii=False, indent=2)
            
            sys.exit(1)

if __name__ == '__main__':
    main()
    
except ImportError as e:
    print(f"[FAIL] Module import error: {e}")
    print(f"[INFO] Available scraper modules in src/scraping/:")
    import os
    scraping_dir = Path(__file__).parent.parent.parent / 'src' / 'scraping'
    if scraping_dir.exists():
        for file in scraping_dir.glob('*_scraper.py'):
            print(f"  - {file.name}")
    sys.exit(1)
"@
    
    $tempScriptPath = Join-Path $PROJECT_ROOT "temp_scraping_test.py"
    
    try {
        # Save Python script
        $pythonScript | Out-File -FilePath $tempScriptPath -Encoding UTF8
        
        # Activate virtual environment
        $activateScript = Join-Path $VENV_PATH "Scripts\Activate.ps1"
        & $activateScript
        
        # Set environment variables
        if ($Headless) {
            $env:HEADLESS_MODE = "true"
        }
        $env:TEST_TIMEOUT = $Timeout
        
        # Execute Python script
        $testOutput = python $tempScriptPath 2>&1
        $exitCode = $LASTEXITCODE
        
        $endTime = Get-Date
        $duration = ($endTime - $startTime).TotalSeconds
        
        # Save output to log
        $testOutput | Out-File -FilePath $logFile -Encoding UTF8
        
        # Display results
        if ($exitCode -eq 0) {
            Write-Host "[OK] $($SiteConfig.name) Real Scraping Test SUCCESS ($($duration.ToString('F1')) sec)" -ForegroundColor Green
            Write-TestLog "$($SiteConfig.name) real scraping test completed successfully in $duration seconds"
        } else {
            Write-Host "[FAIL] $($SiteConfig.name) Real Scraping Test FAILED ($($duration.ToString('F1')) sec)" -ForegroundColor Red
            Write-TestLog "$($SiteConfig.name) real scraping test failed in $duration seconds" "ERROR"
        }
        
        if ($Verbose) {
            Write-Host "Test Output:" -ForegroundColor Yellow
            Write-Host $testOutput -ForegroundColor White
        }
        
        # Clean up temp script
        Remove-Item $tempScriptPath -Force -ErrorAction SilentlyContinue
        
        return @{
            "success" = ($exitCode -eq 0)
            "duration" = [math]::Round($duration, 2)
            "output" = $testOutput -join "`n"
        }
        
    } catch {
        $endTime = Get-Date
        $duration = ($endTime - $startTime).TotalSeconds
        
        Write-Host "[FAIL] $($SiteConfig.name) Test execution error: $($_.Exception.Message)" -ForegroundColor Red
        Write-TestLog "$($SiteConfig.name) test execution error: $($_.Exception.Message)" "ERROR"
        
        # Clean up temp script
        Remove-Item $tempScriptPath -Force -ErrorAction SilentlyContinue
        
        return @{
            "success" = $false
            "duration" = [math]::Round($duration, 2)
            "output" = $_.Exception.Message
        }
    }
}

function Show-TestSummary {
    param([hashtable]$Result, [string]$SiteName, [string]$Query)
    
    Write-Host ""
    Write-Host "[SUMMARY] Real Scraping Test Summary" -ForegroundColor Cyan
    Write-Host "=" * 60 -ForegroundColor Cyan
    
    Write-Host "Site: $SiteName" -ForegroundColor Yellow
    Write-Host "Query: $Query" -ForegroundColor Yellow
    Write-Host "Success: $(if ($Result.success) { '[OK]' } else { '[FAIL]' })" -ForegroundColor $(if ($Result.success) { "Green" } else { "Red" })
    Write-Host "Duration: $($Result.duration) seconds" -ForegroundColor White
    
    # Show result file if exists
    $resultFile = Join-Path $RESULTS_PATH "$SiteName.json"
    if (Test-Path $resultFile) {
        try {
            $resultData = Get-Content $resultFile -Raw | ConvertFrom-Json
            Write-Host ""
            Write-Host "Books Found: $($resultData.books_found)" -ForegroundColor Yellow
            if ($resultData.books_found -gt 0) {
                Write-Host "Top Results:" -ForegroundColor Yellow
                foreach ($book in $resultData.books[0..2]) {
                    if ($book) {
                        Write-Host "  - $($book.title)" -ForegroundColor White
                        Write-Host "    Similarity: $($book.similarity_score)" -ForegroundColor Gray
                    }
                }
            }
        } catch {
            Write-Host "Result file parsing error: $($_.Exception.Message)" -ForegroundColor Red
        }
    }
    
    Write-Host ""
    Write-Host "Files:" -ForegroundColor Yellow
    Write-Host "  Result: $resultFile" -ForegroundColor White
    Write-Host "  Log: $(Join-Path $LOGS_PATH "$SiteName.log")" -ForegroundColor White
    
    Write-TestLog "Real scraping test summary - Site: $SiteName, Success: $($Result.success), Duration: $($Result.duration)s"
}

# ====================================================================
# メイン実行
# ====================================================================

try {
    Write-TestLog "=== Real Scraping Test Started ==="
    
    # 1. 前提条件チェック
    if (-not (Test-Prerequisites)) {
        exit 1
    }
    
    # 2. サイト設定取得
    $siteConfig = Get-SiteConfig -SiteName $Site
    if (-not $siteConfig) {
        exit 1
    }
    
    # 3. 実スクレイピングテスト実行
    $result = Invoke-RealScrapingTest -SiteName $Site -SiteConfig $siteConfig -SearchQuery $Query
    
    # 4. 結果サマリー表示
    Show-TestSummary -Result $result -SiteName $Site -Query $Query
    
    Write-TestLog "=== Real Scraping Test Completed ==="
    
    # 終了コード設定
    if ($result.success) {
        Write-Host ""
        Write-Host "[SUCCESS] Real scraping test completed successfully!" -ForegroundColor Green
        exit 0
    } else {
        Write-Host ""
        Write-Host "[FAIL] Real scraping test failed!" -ForegroundColor Red
        exit 1
    }
    
} catch {
    Write-Host "[FAIL] Unexpected error during real scraping test: $($_.Exception.Message)" -ForegroundColor Red
    Write-TestLog "Unexpected error during real scraping test: $($_.Exception.Message)" "ERROR"
    exit 1
}
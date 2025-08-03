# ====================================================================
# IzumiNovels-Workflow Windows実機テスト実行スクリプト
# ====================================================================
# 用途: Windows PowerShell環境での実機テスト実行
# 前提: setup_windows_environment.ps1 実行済み
# 実行方法: PowerShellで .\run_windows_tests.ps1
# ====================================================================

param(
    [string]$TestType = "quick",  # quick, full, single
    [string]$Site = "",           # 特定サイトのみテスト
    [switch]$Headless = $false,   # ヘッドレスモード
    [switch]$Verbose = $false,    # 詳細出力
    [int]$Timeout = 300          # タイムアウト（秒）
)

# エラー時停止設定
$ErrorActionPreference = "Stop"

# ====================================================================
# 基本設定
# ====================================================================

$PROJECT_ROOT = Split-Path -Parent -Path (Split-Path -Parent -Path $PSScriptRoot)
$VENV_PATH = Join-Path $PROJECT_ROOT "venv"
$TESTS_PATH = Join-Path $PROJECT_ROOT "tests"
$LOGS_PATH = Join-Path $PROJECT_ROOT "logs" "windows_tests"
$RESULTS_PATH = Join-Path $PROJECT_ROOT "test_results"

# テスト対象サイト定義
$TEST_SITES = @{
    "amazon" = @{
        "name" = "Amazon Kindle"
        "script" = "test_amazon_quick.py"
        "priority" = 1
    }
    "bookwalker" = @{
        "name" = "BOOK☆WALKER"
        "script" = "test_bookwalker_quick.py"
        "priority" = 2
    }
    "rakuten" = @{
        "name" = "楽天Kobo"
        "script" = "test_rakuten_kobo_quick.py"
        "priority" = 2
    }
    "google" = @{
        "name" = "Google Play Books"
        "script" = "test_google_play_books_quick.py"
        "priority" = 2
    }
    "honto" = @{
        "name" = "honto"
        "script" = "test_honto_quick.py"
        "priority" = 3
    }
    "kinoppy" = @{
        "name" = "紀伊國屋書店（Kinoppy）"
        "script" = "test_kinoppy_quick.py"
        "priority" = 3
    }
    "reader_store" = @{
        "name" = "Reader Store"
        "script" = "test_reader_store_quick.py"
        "priority" = 3
    }
    "apple" = @{
        "name" = "Apple Books"
        "script" = "test_apple_books_quick.py"
        "priority" = 4
    }
    "booklive" = @{
        "name" = "BookLive"
        "script" = "test_booklive_quick.py"
        "priority" = 4
    }
    "ebookjapan" = @{
        "name" = "ebookjapan"
        "script" = "test_ebookjapan_quick.py"
        "priority" = 4
    }
    "amazon_pod" = @{
        "name" = "Amazon POD（印刷版）"
        "script" = "test_amazon_pod_quick.py"
        "priority" = 5
    }
}

Write-Host "🚀 IzumiNovels-Workflow Windows実機テスト開始" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "テストタイプ: $TestType" -ForegroundColor Yellow
Write-Host "対象サイト: $(if ($Site) { $Site } else { '全サイト' })" -ForegroundColor Yellow
Write-Host "ヘッドレスモード: $Headless" -ForegroundColor Yellow
Write-Host "タイムアウト: $Timeout 秒" -ForegroundColor Yellow

# ====================================================================
# ディレクトリ作成
# ====================================================================

@($LOGS_PATH, $RESULTS_PATH) | ForEach-Object {
    if (-not (Test-Path $_)) {
        New-Item -ItemType Directory -Path $_ -Force | Out-Null
        Write-Host "✅ ディレクトリ作成: $_" -ForegroundColor Green
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
    $logFile = Join-Path $LOGS_PATH "test_execution_$(Get-Date -Format 'yyyyMMdd').log"
    Add-Content -Path $logFile -Value $logMessage
    if ($Verbose) { Write-Host $logMessage -ForegroundColor Gray }
}

function Test-Prerequisites {
    Write-Host "🔍 前提条件チェック..." -ForegroundColor Cyan
    
    # Python仮想環境チェック
    $activateScript = Join-Path $VENV_PATH "Scripts\Activate.ps1"
    if (-not (Test-Path $activateScript)) {
        Write-Host "❌ Python仮想環境が見つかりません: $VENV_PATH" -ForegroundColor Red
        Write-Host "   setup_windows_environment.ps1 を先に実行してください" -ForegroundColor Yellow
        return $false
    }
    
    # テストディレクトリチェック
    if (-not (Test-Path $TESTS_PATH)) {
        Write-Host "❌ テストディレクトリが見つかりません: $TESTS_PATH" -ForegroundColor Red
        return $false
    }
    
    Write-Host "✅ 前提条件チェック完了" -ForegroundColor Green
    Write-TestLog "Prerequisites check completed successfully"
    return $true
}

function Get-TestSites {
    param([string]$TestType, [string]$SpecificSite)
    
    if ($SpecificSite) {
        if ($TEST_SITES.ContainsKey($SpecificSite)) {
            return @($SpecificSite)
        } else {
            Write-Host "❌ 指定されたサイト '$SpecificSite' は無効です" -ForegroundColor Red
            Write-Host "利用可能なサイト: $($TEST_SITES.Keys -join ', ')" -ForegroundColor Yellow
            return @()
        }
    }
    
    switch ($TestType) {
        "quick" {
            # 優先度1-2のサイトのみ
            return $TEST_SITES.Keys | Where-Object { $TEST_SITES[$_].priority -le 2 }
        }
        "full" {
            # 全サイト
            return $TEST_SITES.Keys | Sort-Object { $TEST_SITES[$_].priority }
        }
        default {
            return $TEST_SITES.Keys | Where-Object { $TEST_SITES[$_].priority -le 2 }
        }
    }
}

function Invoke-SiteTest {
    param(
        [string]$SiteKey,
        [hashtable]$SiteInfo,
        [int]$TestNumber,
        [int]$TotalTests
    )
    
    Write-Host ""
    Write-Host "[$TestNumber/$TotalTests] 🌐 $($SiteInfo.name) テスト開始..." -ForegroundColor Cyan
    Write-Host "-" * 50 -ForegroundColor Gray
    
    $testScript = Join-Path $TESTS_PATH "individual" $SiteInfo.script
    $resultFile = Join-Path $RESULTS_PATH "$SiteKey.json"
    $logFile = Join-Path $LOGS_PATH "$SiteKey.log"
    
    if (-not (Test-Path $testScript)) {
        Write-Host "❌ テストスクリプトが見つかりません: $testScript" -ForegroundColor Red
        Write-TestLog "Test script not found: $testScript" "ERROR"
        return @{
            "site" = $SiteKey
            "name" = $SiteInfo.name
            "status" = "ERROR"
            "message" = "テストスクリプトが見つかりません"
            "duration" = 0
        }
    }
    
    $startTime = Get-Date
    Write-TestLog "Starting test for $($SiteInfo.name)"
    
    try {
        # 仮想環境をアクティベート
        $activateScript = Join-Path $VENV_PATH "Scripts\Activate.ps1"
        & $activateScript
        
        # 環境変数設定
        if ($Headless) {
            $env:HEADLESS_MODE = "true"
        }
        $env:TEST_TIMEOUT = $Timeout
        
        # テスト実行
        $testOutput = python $testScript 2>&1
        $exitCode = $LASTEXITCODE
        
        $endTime = Get-Date
        $duration = ($endTime - $startTime).TotalSeconds
        
        # 結果保存
        $result = @{
            "site" = $SiteKey
            "name" = $SiteInfo.name
            "status" = if ($exitCode -eq 0) { "SUCCESS" } else { "FAILED" }
            "message" = $testOutput -join "`n"
            "duration" = [math]::Round($duration, 2)
            "timestamp" = $startTime.ToString("yyyy-MM-dd HH:mm:ss")
        }
        
        $result | ConvertTo-Json -Depth 3 | Out-File -FilePath $resultFile -Encoding UTF8
        $testOutput | Out-File -FilePath $logFile -Encoding UTF8
        
        if ($exitCode -eq 0) {
            Write-Host "✅ $($SiteInfo.name) テスト成功 ($($duration.ToString('F1'))秒)" -ForegroundColor Green
            Write-TestLog "$($SiteInfo.name) test completed successfully in $duration seconds"
        } else {
            Write-Host "❌ $($SiteInfo.name) テスト失敗 ($($duration.ToString('F1'))秒)" -ForegroundColor Red
            Write-TestLog "$($SiteInfo.name) test failed in $duration seconds" "ERROR"
            if ($Verbose) {
                Write-Host "エラー詳細:" -ForegroundColor Yellow
                Write-Host $testOutput -ForegroundColor Red
            }
        }
        
        return $result
        
    } catch {
        $endTime = Get-Date
        $duration = ($endTime - $startTime).TotalSeconds
        
        Write-Host "❌ $($SiteInfo.name) テスト中にエラー: $($_.Exception.Message)" -ForegroundColor Red
        Write-TestLog "$($SiteInfo.name) test error: $($_.Exception.Message)" "ERROR"
        
        return @{
            "site" = $SiteKey
            "name" = $SiteInfo.name
            "status" = "ERROR"
            "message" = $_.Exception.Message
            "duration" = [math]::Round($duration, 2)
            "timestamp" = $startTime.ToString("yyyy-MM-dd HH:mm:ss")
        }
    }
}

function Show-TestSummary {
    param([array]$Results)
    
    Write-Host ""
    Write-Host "📊 テスト結果サマリー" -ForegroundColor Cyan
    Write-Host "=" * 60 -ForegroundColor Cyan
    
    $totalTests = $Results.Count
    $successCount = ($Results | Where-Object { $_.status -eq "SUCCESS" }).Count
    $failedCount = ($Results | Where-Object { $_.status -eq "FAILED" }).Count
    $errorCount = ($Results | Where-Object { $_.status -eq "ERROR" }).Count
    $totalDuration = ($Results | Measure-Object -Property duration -Sum).Sum
    
    Write-Host "📈 統計情報:" -ForegroundColor Yellow
    Write-Host "  総テスト数: $totalTests" -ForegroundColor White
    Write-Host "  成功: $successCount" -ForegroundColor Green
    Write-Host "  失敗: $failedCount" -ForegroundColor Red
    Write-Host "  エラー: $errorCount" -ForegroundColor Magenta
    Write-Host "  成功率: $([math]::Round($successCount / $totalTests * 100, 1))%" -ForegroundColor Yellow
    Write-Host "  総実行時間: $([math]::Round($totalDuration, 1))秒" -ForegroundColor White
    
    Write-Host ""
    Write-Host "📋 詳細結果:" -ForegroundColor Yellow
    
    foreach ($result in $Results) {
        $status = switch ($result.status) {
            "SUCCESS" { "✅" }
            "FAILED" { "❌" }
            "ERROR" { "🔥" }
        }
        $color = switch ($result.status) {
            "SUCCESS" { "Green" }
            "FAILED" { "Red" }
            "ERROR" { "Magenta" }
        }
        
        Write-Host "  $status $($result.name): $($result.status) ($($result.duration)秒)" -ForegroundColor $color
    }
    
    # 結果をJSONファイルに保存
    $summaryFile = Join-Path $RESULTS_PATH "test_summary_$(Get-Date -Format 'yyyyMMdd_HHmmss').json"
    $summary = @{
        "timestamp" = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
        "test_type" = $TestType
        "total_tests" = $totalTests
        "success_count" = $successCount
        "failed_count" = $failedCount
        "error_count" = $errorCount
        "success_rate" = [math]::Round($successCount / $totalTests * 100, 1)
        "total_duration" = [math]::Round($totalDuration, 1)
        "results" = $Results
    }
    
    $summary | ConvertTo-Json -Depth 4 | Out-File -FilePath $summaryFile -Encoding UTF8
    
    Write-Host ""
    Write-Host "📄 詳細結果保存先:" -ForegroundColor Yellow
    Write-Host "  サマリー: $summaryFile" -ForegroundColor White
    Write-Host "  個別結果: $RESULTS_PATH" -ForegroundColor White
    Write-Host "  ログ: $LOGS_PATH" -ForegroundColor White
    
    Write-TestLog "Test summary - Total: $totalTests, Success: $successCount, Failed: $failedCount, Error: $errorCount"
}

# ====================================================================
# メイン実行
# ====================================================================

try {
    Write-TestLog "=== Windows実機テスト開始 ==="
    
    # 1. 前提条件チェック
    if (-not (Test-Prerequisites)) {
        exit 1
    }
    
    # 2. テスト対象サイト取得
    $sitesToTest = Get-TestSites -TestType $TestType -SpecificSite $Site
    if ($sitesToTest.Count -eq 0) {
        Write-Host "❌ テスト対象サイトが見つかりません" -ForegroundColor Red
        exit 1
    }
    
    Write-Host ""
    Write-Host "🎯 テスト対象サイト ($($sitesToTest.Count)サイト):" -ForegroundColor Yellow
    foreach ($siteKey in $sitesToTest) {
        Write-Host "  - $($TEST_SITES[$siteKey].name)" -ForegroundColor White
    }
    
    # 3. テスト実行
    $results = @()
    $testNumber = 1
    
    foreach ($siteKey in $sitesToTest) {
        $siteInfo = $TEST_SITES[$siteKey]
        $result = Invoke-SiteTest -SiteKey $siteKey -SiteInfo $siteInfo -TestNumber $testNumber -TotalTests $sitesToTest.Count
        $results += $result
        $testNumber++
        
        # 少し休憩（サイトへの負荷軽減）
        if ($testNumber -le $sitesToTest.Count) {
            Start-Sleep -Seconds 2
        }
    }
    
    # 4. 結果サマリー表示
    Show-TestSummary -Results $results
    
    Write-TestLog "=== Windows実機テスト完了 ==="
    
    # 終了コード設定
    $failedOrErrorCount = ($results | Where-Object { $_.status -in @("FAILED", "ERROR") }).Count
    if ($failedOrErrorCount -gt 0) {
        Write-Host ""
        Write-Host "⚠️  $failedOrErrorCount 件のテストで問題が発生しました" -ForegroundColor Yellow
        exit 1
    } else {
        Write-Host ""
        Write-Host "🎉 全テストが正常に完了しました！" -ForegroundColor Green
        exit 0
    }
    
} catch {
    Write-Host "❌ テスト実行中に予期しないエラーが発生しました: $($_.Exception.Message)" -ForegroundColor Red
    Write-TestLog "Unexpected error during test execution: $($_.Exception.Message)" "ERROR"
    exit 1
}
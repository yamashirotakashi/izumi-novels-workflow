# ====================================================================
# IzumiNovels-Workflow テスト結果レポート生成スクリプト
# ====================================================================
# 用途: Windows実機テスト結果の包括的レポート生成
# 実行方法: PowerShellで .\generate_test_report.ps1
# ====================================================================

param(
    [string]$InputPath = "",      # 特定の結果ファイルパス
    [string]$OutputFormat = "html", # html, json, csv
    [switch]$OpenReport = $true,  # レポート自動オープン
    [switch]$Verbose = $false     # 詳細出力
)

# エラー時停止設定
$ErrorActionPreference = "Stop"

# ====================================================================
# 基本設定
# ====================================================================

$PROJECT_ROOT = Split-Path -Parent -Path (Split-Path -Parent -Path $PSScriptRoot)
$RESULTS_PATH = Join-Path $PROJECT_ROOT "test_results"
$REPORTS_PATH = Join-Path $PROJECT_ROOT "reports"
$TEMPLATE_PATH = Join-Path $PSScriptRoot "report_template.html"

Write-Host "📊 IzumiNovels-Workflow テスト結果レポート生成" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan

# ====================================================================
# ディレクトリ作成
# ====================================================================

if (-not (Test-Path $REPORTS_PATH)) {
    New-Item -ItemType Directory -Path $REPORTS_PATH -Force | Out-Null
    Write-Host "✅ レポートディレクトリ作成: $REPORTS_PATH" -ForegroundColor Green
}

# ====================================================================
# 関数定義
# ====================================================================

function Get-LatestTestResults {
    if ($InputPath -and (Test-Path $InputPath)) {
        return $InputPath
    }
    
    $summaryFiles = Get-ChildItem -Path $RESULTS_PATH -Filter "test_summary_*.json" | Sort-Object LastWriteTime -Descending
    
    if ($summaryFiles.Count -eq 0) {
        Write-Host "❌ テスト結果ファイルが見つかりません: $RESULTS_PATH" -ForegroundColor Red
        return $null
    }
    
    $latestFile = $summaryFiles[0].FullName
    Write-Host "📄 最新テスト結果: $($summaryFiles[0].Name)" -ForegroundColor Yellow
    return $latestFile
}

function Read-TestSummary {
    param([string]$FilePath)
    
    try {
        $content = Get-Content -Path $FilePath -Raw -Encoding UTF8
        $summary = $content | ConvertFrom-Json
        Write-Host "✅ テスト結果読み込み完了" -ForegroundColor Green
        return $summary
    } catch {
        Write-Host "❌ テスト結果読み込み失敗: $($_.Exception.Message)" -ForegroundColor Red
        return $null
    }
}

function Generate-HTMLReport {
    param([object]$Summary, [string]$OutputPath)
    
    Write-Host "🌐 HTMLレポート生成中..." -ForegroundColor Cyan
    
    # HTMLテンプレート
    $htmlTemplate = @"
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>IzumiNovels-Workflow テスト結果レポート</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
            color: #333;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        .header h1 {
            margin: 0;
            font-size: 2.5em;
            font-weight: 300;
        }
        .header p {
            margin: 10px 0 0;
            opacity: 0.9;
            font-size: 1.1em;
        }
        .summary {
            padding: 30px;
            background: #f8f9fa;
            border-bottom: 1px solid #dee2e6;
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .stat-card {
            background: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            border-left: 4px solid #667eea;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .stat-number {
            font-size: 2.5em;
            font-weight: bold;
            margin-bottom: 5px;
        }
        .stat-label {
            color: #666;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .success { color: #28a745; border-left-color: #28a745; }
        .danger { color: #dc3545; border-left-color: #dc3545; }
        .warning { color: #ffc107; border-left-color: #ffc107; }
        .info { color: #17a2b8; border-left-color: #17a2b8; }
        .results {
            padding: 30px;
        }
        .results h2 {
            margin-bottom: 20px;
            color: #495057;
            border-bottom: 2px solid #dee2e6;
            padding-bottom: 10px;
        }
        .result-table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 30px;
        }
        .result-table th,
        .result-table td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #dee2e6;
        }
        .result-table th {
            background-color: #f8f9fa;
            font-weight: 600;
            color: #495057;
        }
        .result-table tr:hover {
            background-color: #f8f9fa;
        }
        .status-badge {
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: 600;
            text-transform: uppercase;
        }
        .status-success {
            background-color: #d4edda;
            color: #155724;
        }
        .status-failed {
            background-color: #f8d7da;
            color: #721c24;
        }
        .status-error {
            background-color: #fff3cd;
            color: #856404;
        }
        .footer {
            padding: 20px 30px;
            background-color: #f8f9fa;
            border-top: 1px solid #dee2e6;
            text-align: center;
            color: #6c757d;
            font-size: 0.9em;
        }
        .progress-bar {
            background-color: #e9ecef;
            border-radius: 10px;
            overflow: hidden;
            height: 20px;
            margin: 10px 0;
        }
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #28a745, #20c997);
            transition: width 0.3s ease;
        }
        .chart-container {
            text-align: center;
            margin: 20px 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- ヘッダー -->
        <div class="header">
            <h1>🚀 IzumiNovels-Workflow</h1>
            <p>Phase 1 Windows実機テスト結果レポート</p>
        </div>

        <!-- サマリーセクション -->
        <div class="summary">
            <div class="stats">
                <div class="stat-card info">
                    <div class="stat-number">{{TOTAL_TESTS}}</div>
                    <div class="stat-label">総テスト数</div>
                </div>
                <div class="stat-card success">
                    <div class="stat-number">{{SUCCESS_COUNT}}</div>
                    <div class="stat-label">成功</div>
                </div>
                <div class="stat-card danger">
                    <div class="stat-number">{{FAILED_COUNT}}</div>
                    <div class="stat-label">失敗</div>
                </div>
                <div class="stat-card warning">
                    <div class="stat-number">{{ERROR_COUNT}}</div>
                    <div class="stat-label">エラー</div>
                </div>
            </div>
            
            <div class="stat-card">
                <div class="stat-label">成功率</div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: {{SUCCESS_RATE}}%"></div>
                </div>
                <div class="stat-number success">{{SUCCESS_RATE}}%</div>
            </div>
        </div>

        <!-- 詳細結果 -->
        <div class="results">
            <h2>📋 詳細テスト結果</h2>
            <table class="result-table">
                <thead>
                    <tr>
                        <th>サイト名</th>
                        <th>ステータス</th>
                        <th>実行時間</th>
                        <th>実行日時</th>
                        <th>メッセージ</th>
                    </tr>
                </thead>
                <tbody>
                    {{RESULT_ROWS}}
                </tbody>
            </table>
        </div>

        <!-- フッター -->
        <div class="footer">
            <p>生成日時: {{GENERATION_TIME}} | IzumiNovels-Workflow Project</p>
        </div>
    </div>
</body>
</html>
"@

    # データ置換
    $resultRows = ""
    foreach ($result in $Summary.results) {
        $statusClass = switch ($result.status) {
            "SUCCESS" { "status-success" }
            "FAILED" { "status-failed" }
            "ERROR" { "status-error" }
        }
        
        $message = if ($result.message.Length -gt 100) { 
            $result.message.Substring(0, 97) + "..." 
        } else { 
            $result.message 
        }
        
        $resultRows += @"
                    <tr>
                        <td>$($result.name)</td>
                        <td><span class="status-badge $statusClass">$($result.status)</span></td>
                        <td>$($result.duration)秒</td>
                        <td>$($result.timestamp)</td>
                        <td>$($message -replace '"', '&quot;' -replace '<', '&lt;' -replace '>', '&gt;')</td>
                    </tr>
"@
    }
    
    $html = $htmlTemplate `
        -replace "{{TOTAL_TESTS}}", $Summary.total_tests `
        -replace "{{SUCCESS_COUNT}}", $Summary.success_count `
        -replace "{{FAILED_COUNT}}", $Summary.failed_count `
        -replace "{{ERROR_COUNT}}", $Summary.error_count `
        -replace "{{SUCCESS_RATE}}", $Summary.success_rate `
        -replace "{{RESULT_ROWS}}", $resultRows `
        -replace "{{GENERATION_TIME}}", (Get-Date -Format "yyyy-MM-dd HH:mm:ss")
    
    try {
        $html | Out-File -FilePath $OutputPath -Encoding UTF8
        Write-Host "✅ HTMLレポート生成完了: $OutputPath" -ForegroundColor Green
        return $true
    } catch {
        Write-Host "❌ HTMLレポート生成失敗: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

function Generate-CSVReport {
    param([object]$Summary, [string]$OutputPath)
    
    Write-Host "📄 CSVレポート生成中..." -ForegroundColor Cyan
    
    try {
        $csv = "サイト名,ステータス,実行時間(秒),実行日時,メッセージ`n"
        
        foreach ($result in $Summary.results) {
            $message = $result.message -replace '"', '""' -replace "`n", " " -replace "`r", ""
            $csv += "`"$($result.name)`",`"$($result.status)`",$($result.duration),`"$($result.timestamp)`",`"$message`"`n"
        }
        
        $csv | Out-File -FilePath $OutputPath -Encoding UTF8
        Write-Host "✅ CSVレポート生成完了: $OutputPath" -ForegroundColor Green
        return $true
    } catch {
        Write-Host "❌ CSVレポート生成失敗: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

function Generate-JSONReport {
    param([object]$Summary, [string]$OutputPath)
    
    Write-Host "📊 JSONレポート生成中..." -ForegroundColor Cyan
    
    try {
        $reportData = @{
            "metadata" = @{
                "generation_time" = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
                "project_name" = "IzumiNovels-Workflow"
                "phase" = "Phase 1"
                "test_environment" = "Windows PowerShell"
            }
            "summary" = $Summary
            "analysis" = @{
                "success_sites" = @($Summary.results | Where-Object { $_.status -eq "SUCCESS" } | ForEach-Object { $_.name })
                "failed_sites" = @($Summary.results | Where-Object { $_.status -eq "FAILED" } | ForEach-Object { $_.name })
                "error_sites" = @($Summary.results | Where-Object { $_.status -eq "ERROR" } | ForEach-Object { $_.name })
                "average_duration" = [math]::Round(($Summary.results | Measure-Object -Property duration -Average).Average, 2)
                "total_duration" = $Summary.total_duration
            }
        }
        
        $reportData | ConvertTo-Json -Depth 5 | Out-File -FilePath $OutputPath -Encoding UTF8
        Write-Host "✅ JSONレポート生成完了: $OutputPath" -ForegroundColor Green
        return $true
    } catch {
        Write-Host "❌ JSONレポート生成失敗: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

function Show-ReportSummary {
    param([object]$Summary, [string]$ReportPath)
    
    Write-Host ""
    Write-Host "📊 レポート生成完了サマリー" -ForegroundColor Cyan
    Write-Host "=" * 60 -ForegroundColor Cyan
    
    Write-Host "📅 テスト実行日時: $($Summary.timestamp)" -ForegroundColor Yellow
    Write-Host "🎯 テストタイプ: $($Summary.test_type)" -ForegroundColor Yellow
    Write-Host "📈 成功率: $($Summary.success_rate)%" -ForegroundColor $(if ($Summary.success_rate -ge 75) { "Green" } else { "Red" })
    Write-Host "⏱️  総実行時間: $($Summary.total_duration)秒" -ForegroundColor White
    
    Write-Host ""
    Write-Host "📄 生成されたレポート:" -ForegroundColor Yellow
    Write-Host "  パス: $ReportPath" -ForegroundColor White
    Write-Host "  形式: $($OutputFormat.ToUpper())" -ForegroundColor White
    
    # Phase 1 品質評価
    $qualityRating = switch ($Summary.success_rate) {
        { $_ -ge 90 } { "🎉 優秀 (Excellent)" }
        { $_ -ge 75 } { "✅ 良好 (Good)" }
        { $_ -ge 50 } { "⚠️ 改善必要 (Needs Improvement)" }
        default { "❌ 要対応 (Critical)" }
    }
    
    Write-Host ""
    Write-Host "🏆 Phase 1 品質評価: $qualityRating" -ForegroundColor Cyan
    
    if ($Summary.success_rate -ge 75) {
        Write-Host "   Phase 2 (WordPress統合) への移行準備完了" -ForegroundColor Green
    } else {
        Write-Host "   追加調整・修正が必要です" -ForegroundColor Yellow
    }
}

# ====================================================================
# メイン実行
# ====================================================================

try {
    # 1. 最新テスト結果取得
    $summaryFile = Get-LatestTestResults
    if (-not $summaryFile) {
        exit 1
    }
    
    # 2. テスト結果読み込み
    $summary = Read-TestSummary -FilePath $summaryFile
    if (-not $summary) {
        exit 1
    }
    
    # 3. 出力ファイル名生成
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $outputFileName = "test_report_$timestamp.$OutputFormat"
    $outputPath = Join-Path $REPORTS_PATH $outputFileName
    
    # 4. 形式別レポート生成
    $success = switch ($OutputFormat.ToLower()) {
        "html" { Generate-HTMLReport -Summary $summary -OutputPath $outputPath }
        "csv" { Generate-CSVReport -Summary $summary -OutputPath $outputPath }
        "json" { Generate-JSONReport -Summary $summary -OutputPath $outputPath }
        default {
            Write-Host "❌ 未対応の出力形式: $OutputFormat" -ForegroundColor Red
            $false
        }
    }
    
    if (-not $success) {
        exit 1
    }
    
    # 5. サマリー表示
    Show-ReportSummary -Summary $summary -ReportPath $outputPath
    
    # 6. レポート自動オープン
    if ($OpenReport -and $OutputFormat.ToLower() -eq "html") {
        Write-Host ""
        Write-Host "🌐 レポートをブラウザで開いています..." -ForegroundColor Cyan
        Start-Process $outputPath
    }
    
    Write-Host ""
    Write-Host "🎉 レポート生成完了！" -ForegroundColor Green
    
} catch {
    Write-Host "❌ レポート生成中に予期しないエラーが発生しました: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
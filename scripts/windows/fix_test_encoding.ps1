# Quick script to fix all remaining Japanese text in test files
$testFiles = Get-ChildItem -Path "C:\Users\tky99\DEV\izumi-novels-workflow\tests\individual\*.py" -File

foreach ($file in $testFiles) {
    $content = Get-Content -Path $file.FullName -Encoding UTF8 -Raw
    
    # Replace remaining Japanese text with English
    $content = $content -replace "サイト名:", "Site Name:"
    $content = $content -replace "ベースURL:", "Base URL:"
    $content = $content -replace "検索URL:", "Search URL:"
    $content = $content -replace "不明", "Unknown"
    $content = $content -replace "個のセレクタ", " selectors"
    $content = $content -replace "主要:", "Primary:"
    $content = $content -replace "フォールバック:", "Fallback:"
    $content = $content -replace "個", " items"
    $content = $content -replace "秒", "sec"
    $content = $content -replace "直接検索URL:", "Direct Search URL:"
    $content = $content -replace "テスト", "test"
    $content = $content -replace "品質:", "Quality:"
    $content = $content -replace "EXCELLENT - 全必須項目完備", "EXCELLENT - All required items complete"
    $content = $content -replace "GOOD - セレクタ完全、軽微な不足", "GOOD - Selectors complete, minor issues"
    $content = $content -replace "PARTIAL - 不足項目:", "PARTIAL - Missing items:"
    $content = $content -replace "設定完全性:", "Config Completeness:"
    $content = $content -replace "総セレクタ数:", "Total Selectors:"
    $content = $content -replace "フォールバック対応:", "Fallback Support:"
    $content = $content -replace "あり", "Available"
    $content = $content -replace "なし", "None"
    $content = $content -replace "直接検索対応:", "Direct Search Support:"
    $content = $content -replace "判定:", "Result:"
    $content = $content -replace "実用準備完了", "Ready for Production"
    $content = $content -replace "改善推奨", "Improvement Recommended"
    $content = $content -replace "修正必要", "Fix Required"
    $content = $content -replace "メイン実行", "Main Execution"
    $content = $content -replace "終了コード設定", "Set exit code"
    
    # Write back to file
    $content | Out-File -FilePath $file.FullName -Encoding UTF8 -NoNewline
}

Write-Host "[OK] All test files converted to English" -ForegroundColor Green
# Windows環境用Phase 1実機テストスクリプト
# IzumiNovels-Workflow Project
# 実行日: 2025-08-01

Write-Host "🚀 IzumiNovels-Workflow Phase 1 Windows実機テスト開始" -ForegroundColor Cyan
Write-Host ("=" * 70) -ForegroundColor DarkGray

# プロジェクトルートディレクトリを設定
$projectRoot = "C:\Users\tky99\DEV\izumi-novels-workflow"
Set-Location $projectRoot

# Python仮想環境の確認（Windows環境用）
# 注意: WSLで作成した仮想環境はWindowsでは使用不可
$venvPath = Join-Path $projectRoot "venv_windows"
$activateScript = Join-Path $venvPath "Scripts\Activate.ps1"

if (-not (Test-Path $activateScript)) {
    Write-Host "❌ Windows用仮想環境が見つかりません: $venvPath" -ForegroundColor Red
    Write-Host "📝 Windows用仮想環境を新規作成します..." -ForegroundColor Yellow
    Write-Host "⚠️ WSLの仮想環境とは別に作成が必要です" -ForegroundColor Yellow
    
    # Windows環境でpython実行
    python -m venv venv_windows
    & $activateScript
    
    Write-Host "📦 依存関係をインストール中..." -ForegroundColor Yellow
    python -m pip install --upgrade pip
    pip install -r requirements.txt
    
    # Windows固有の依存関係
    Write-Host "🔧 Windows固有の設定を適用中..." -ForegroundColor Yellow
    pip install pywin32
}
else {
    Write-Host "✅ Windows用仮想環境を有効化しています..." -ForegroundColor Green
    & $activateScript
}

# Chrome実行可能ファイルの確認
Write-Host "`n🔍 Google Chrome環境チェック" -ForegroundColor Yellow
$chromePaths = @(
    "C:\Program Files\Google\Chrome\Application\chrome.exe",
    "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    "$env:LOCALAPPDATA\Google\Chrome\Application\chrome.exe"
)

$chromeFound = $false
foreach ($path in $chromePaths) {
    if (Test-Path $path) {
        Write-Host "✅ Chrome検出: $path" -ForegroundColor Green
        $chromeFound = $true
        break
    }
}

if (-not $chromeFound) {
    Write-Host "⚠️ Google Chromeが見つかりません。インストールしてください。" -ForegroundColor Red
    exit 1
}

# 基本的な動作確認テスト
Write-Host "`n📋 Phase 1基本動作確認テスト" -ForegroundColor Yellow

# 1. インポートテスト
Write-Host "`n[1/5] モジュールインポートテスト..." -ForegroundColor Cyan
python -c "from src.scrapers.advanced.selenium_base_scraper import SeleniumBaseScraper; print('✅ SeleniumBaseScraper: OK')"
python -c "from src.scrapers.advanced.kinoppy_advanced import KinoppyAdvancedScraper; print('✅ KinoppyAdvanced: OK')"
python -c "from src.scrapers.advanced.reader_store_advanced import ReaderStoreAdvancedScraper; print('✅ ReaderStoreAdvanced: OK')"
python -c "import undetected_chromedriver as uc; print('✅ undetected-chromedriver: OK')"

# 2. 簡易実行テスト
Write-Host "`n[2/5] スクレイパー初期化テスト..." -ForegroundColor Cyan
$testScript = @"
import sys
sys.path.append('src')
from scrapers.advanced.kinoppy_advanced import KinoppyAdvancedScraper
from scrapers.advanced.reader_store_advanced import ReaderStoreAdvancedScraper

try:
    # Kinoppy初期化テスト
    kinoppy = KinoppyAdvancedScraper()
    print('✅ Kinoppyスクレイパー初期化: OK')
    
    # Reader Store初期化テスト
    reader = ReaderStoreAdvancedScraper()
    print('✅ Reader Storeスクレイパー初期化: OK')
    
except Exception as e:
    print(f'❌ エラー: {e}')
"@

$testScript | python

# 3. 実際の検索テスト（GUI表示）
Write-Host "`n[3/5] 実際の検索テスト準備..." -ForegroundColor Cyan
Write-Host "⚠️ 次のテストではブラウザウィンドウが表示されます" -ForegroundColor Yellow

$confirm = Read-Host "検索テストを実行しますか？ (y/n)"
if ($confirm -eq 'y') {
    Write-Host "`n🔍 Kinoppy検索テスト実行中..." -ForegroundColor Green
    python test_advanced_scrapers_simple.py --site kinoppy --title "課長が目覚めたら異世界SF艦隊の提督になってた件です①"
    
    Write-Host "`n🔍 Reader Store検索テスト実行中..." -ForegroundColor Green
    python test_advanced_scrapers_simple.py --site reader_store --title "課長が目覚めたら異世界SF艦隊の提督になってた件です①"
}

# 4. Phase 1完全検証テスト
Write-Host "`n[4/5] Phase 1完全検証テスト..." -ForegroundColor Cyan
python phase1_verification_final.py

# 5. レポート確認
Write-Host "`n[5/5] テストレポート確認..." -ForegroundColor Cyan
$reportPath = Join-Path $projectRoot "reports\phase1_verification_final.json"
if (Test-Path $reportPath) {
    Write-Host "✅ レポートが生成されました: $reportPath" -ForegroundColor Green
    $report = Get-Content $reportPath | ConvertFrom-Json
    Write-Host "`n📊 テスト結果サマリー:" -ForegroundColor Yellow
    Write-Host "  総合ステータス: $($report.overall_status)" -ForegroundColor White
    Write-Host "  合格率: $($report.test_summary.pass_rate * 100)%" -ForegroundColor White
}

Write-Host "`n🏁 Windows実機テスト完了" -ForegroundColor Green
Write-Host ("=" * 70) -ForegroundColor DarkGray

# 次のアクション提案
Write-Host "`n💡 次のステップ:" -ForegroundColor Yellow
Write-Host "1. 実際のサイトでの手動確認" -ForegroundColor White
Write-Host "2. 成功率の計測（複数書籍でのテスト）" -ForegroundColor White
Write-Host "3. Phase 2への移行準備" -ForegroundColor White
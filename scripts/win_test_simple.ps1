# Windows環境用 Phase 1 テストスクリプト（簡易版）
Write-Host "Starting IzumiNovels-Workflow Phase 1 Windows Test" -ForegroundColor Cyan

# プロジェクトディレクトリ
cd C:\Users\tky99\DEV\izumi-novels-workflow

# 仮想環境の確認と作成
$venvPath = "venv_windows"
if (!(Test-Path $venvPath)) {
    Write-Host "Creating Windows virtual environment..." -ForegroundColor Yellow
    python -m venv $venvPath
}

# 仮想環境の有効化
Write-Host "Activating virtual environment..." -ForegroundColor Green
& .\venv_windows\Scripts\Activate.ps1

# 依存関係のインストール
Write-Host "Installing dependencies..." -ForegroundColor Yellow
python -m pip install --upgrade pip
pip install -r requirements.txt

# Chromeの確認
Write-Host "Checking Chrome installation..." -ForegroundColor Yellow
$chromePath = "C:\Program Files\Google\Chrome\Application\chrome.exe"
if (Test-Path $chromePath) {
    Write-Host "Chrome found at: $chromePath" -ForegroundColor Green
}

# Phase 1 検証テスト実行
Write-Host "Running Phase 1 verification test..." -ForegroundColor Cyan
python phase1_verification_final.py

Write-Host "Test completed!" -ForegroundColor Green
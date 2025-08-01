# Windows環境完全セットアップスクリプト
Write-Host "IzumiNovels-Workflow Windows完全セットアップ" -ForegroundColor Cyan

# プロジェクトディレクトリ
cd C:\Users\tky99\DEV\izumi-novels-workflow

# 必要なディレクトリを作成
Write-Host "Creating required directories..." -ForegroundColor Yellow
if (!(Test-Path "reports")) { New-Item -ItemType Directory -Name "reports" }
if (!(Test-Path "logs")) { New-Item -ItemType Directory -Name "logs" }

# 既存の仮想環境を削除（クリーンインストール）
if (Test-Path "venv_windows") {
    Write-Host "Removing existing Windows virtual environment..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force "venv_windows"
}

# 新しい仮想環境を作成
Write-Host "Creating fresh Windows virtual environment..." -ForegroundColor Green
python -m venv venv_windows

# 仮想環境を有効化
Write-Host "Activating virtual environment..." -ForegroundColor Green
& .\venv_windows\Scripts\Activate.ps1

# pipをアップグレード
Write-Host "Upgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip

# Windows専用依存関係をインストール
Write-Host "Installing Windows-specific dependencies..." -ForegroundColor Yellow
pip install -r requirements_windows.txt

# Chrome確認
Write-Host "Checking Chrome installation..." -ForegroundColor Yellow
$chromePath = "C:\Program Files\Google\Chrome\Application\chrome.exe"
if (Test-Path $chromePath) {
    Write-Host "Chrome found: $chromePath" -ForegroundColor Green
} else {
    Write-Host "Chrome not found at standard location" -ForegroundColor Red
}

# 基本的な動作確認
Write-Host "Testing basic imports..." -ForegroundColor Cyan
python -c "import selenium; print('✅ Selenium: OK')"
python -c "import undetected_chromedriver; print('✅ Undetected Chrome: OK')"
python -c "import bs4; print('✅ BeautifulSoup: OK')"
python -c "import requests; print('✅ Requests: OK')"

Write-Host "Windows setup completed successfully!" -ForegroundColor Green
Write-Host "Next: Run 'python phase1_verification_final.py' to test" -ForegroundColor Yellow
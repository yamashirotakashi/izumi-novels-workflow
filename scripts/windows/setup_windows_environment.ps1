# ====================================================================
# IzumiNovels-Workflow Windows環境セットアップスクリプト
# ====================================================================
# 用途: Windows PowerShell環境でのプロジェクト実行環境構築
# 実行方法: PowerShellで .\setup_windows_environment.ps1
# ====================================================================

param(
    [switch]$Force,
    [switch]$Verbose
)

# エラー時停止設定
$ErrorActionPreference = "Stop"

# ====================================================================
# 基本設定
# ====================================================================

$PROJECT_ROOT = Split-Path -Parent -Path (Split-Path -Parent -Path $PSScriptRoot)
$VENV_PATH = Join-Path $PROJECT_ROOT "venv"
$REQUIREMENTS_PATH = Join-Path $PROJECT_ROOT "requirements.txt"
$LOG_PATH = Join-Path $PROJECT_ROOT "logs" "windows_setup.log"

Write-Host "🚀 IzumiNovels-Workflow Windows環境セットアップ開始" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "プロジェクトルート: $PROJECT_ROOT" -ForegroundColor Yellow

# ====================================================================
# ログディレクトリ作成
# ====================================================================

$LOG_DIR = Split-Path -Parent $LOG_PATH
if (-not (Test-Path $LOG_DIR)) {
    New-Item -ItemType Directory -Path $LOG_DIR -Force | Out-Null
    Write-Host "✅ ログディレクトリ作成: $LOG_DIR" -ForegroundColor Green
}

# ====================================================================
# 関数定義
# ====================================================================

function Write-Log {
    param([string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] $Message"
    Add-Content -Path $LOG_PATH -Value $logMessage
    if ($Verbose) { Write-Host $logMessage -ForegroundColor Gray }
}

function Test-PythonInstallation {
    try {
        $pythonVersion = python --version 2>$null
        if ($pythonVersion -match "Python (\d+\.\d+)") {
            $version = [version]$matches[1]
            if ($version -ge [version]"3.8") {
                Write-Host "✅ Python $pythonVersion 検出" -ForegroundColor Green
                Write-Log "Python installation verified: $pythonVersion"
                return $true
            } else {
                Write-Host "❌ Python 3.8以上が必要です (現在: $pythonVersion)" -ForegroundColor Red
                return $false
            }
        }
    } catch {
        Write-Host "❌ Pythonが見つかりません" -ForegroundColor Red
        Write-Host "   Python 3.8以上をインストールしてPATHに追加してください" -ForegroundColor Yellow
        return $false
    }
}

function Setup-VirtualEnvironment {
    Write-Host "📦 Python仮想環境セットアップ..." -ForegroundColor Cyan
    
    if (Test-Path $VENV_PATH) {
        if ($Force) {
            Write-Host "🔄 既存の仮想環境を削除して再作成..." -ForegroundColor Yellow
            Remove-Item -Recurse -Force $VENV_PATH
        } else {
            Write-Host "✅ 仮想環境は既に存在します: $VENV_PATH" -ForegroundColor Green
            Write-Log "Virtual environment already exists"
            return $true
        }
    }
    
    try {
        python -m venv $VENV_PATH
        Write-Host "✅ 仮想環境作成完了: $VENV_PATH" -ForegroundColor Green
        Write-Log "Virtual environment created successfully"
        return $true
    } catch {
        Write-Host "❌ 仮想環境作成失敗: $($_.Exception.Message)" -ForegroundColor Red
        Write-Log "Failed to create virtual environment: $($_.Exception.Message)"
        return $false
    }
}

function Install-Dependencies {
    Write-Host "📚 依存関係インストール..." -ForegroundColor Cyan
    
    $activateScript = Join-Path $VENV_PATH "Scripts\Activate.ps1"
    if (-not (Test-Path $activateScript)) {
        Write-Host "❌ 仮想環境アクティベーションスクリプトが見つかりません" -ForegroundColor Red
        return $false
    }
    
    try {
        & $activateScript
        Write-Log "Virtual environment activated"
        
        if (Test-Path $REQUIREMENTS_PATH) {
            pip install -r $REQUIREMENTS_PATH
            Write-Host "✅ 依存関係インストール完了" -ForegroundColor Green
            Write-Log "Dependencies installed from requirements.txt"
        } else {
            Write-Host "⚠️  requirements.txt が見つかりません。基本パッケージのみインストール..." -ForegroundColor Yellow
            pip install selenium undetected-chromedriver beautifulsoup4 requests google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
            Write-Host "✅ 基本パッケージインストール完了" -ForegroundColor Green
            Write-Log "Basic packages installed"
        }
        
        return $true
    } catch {
        Write-Host "❌ 依存関係インストール失敗: $($_.Exception.Message)" -ForegroundColor Red
        Write-Log "Failed to install dependencies: $($_.Exception.Message)"
        return $false
    }
}

function Test-ChromeDriver {
    Write-Host "🌐 ChromeDriver 動作確認..." -ForegroundColor Cyan
    
    $testScript = @"
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root / 'src'))

try:
    import undetected_chromedriver as uc
    from selenium.webdriver.chrome.options import Options
    
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    driver = uc.Chrome(options=options)
    driver.get('https://www.google.com')
    title = driver.title
    driver.quit()
    
    print(f'ChromeDriver テスト成功: {title}')
    sys.exit(0)
except Exception as e:
    print(f'ChromeDriver テスト失敗: {e}')
    sys.exit(1)
"@
    
    $testFile = Join-Path $PROJECT_ROOT "temp_chrome_test.py"
    
    try {
        $testScript | Out-File -FilePath $testFile -Encoding UTF8
        $result = python $testFile 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ ChromeDriver 動作確認成功" -ForegroundColor Green
            Write-Log "ChromeDriver test successful"
            $success = $true
        } else {
            Write-Host "❌ ChromeDriver 動作確認失敗: $result" -ForegroundColor Red
            Write-Log "ChromeDriver test failed: $result"
            $success = $false
        }
        
        Remove-Item $testFile -Force -ErrorAction SilentlyContinue
        return $success
    } catch {
        Write-Host "❌ ChromeDriver テスト中にエラー: $($_.Exception.Message)" -ForegroundColor Red
        Write-Log "ChromeDriver test error: $($_.Exception.Message)"
        Remove-Item $testFile -Force -ErrorAction SilentlyContinue
        return $false
    }
}

function Show-NextSteps {
    Write-Host ""
    Write-Host "🎉 Windows環境セットアップ完了!" -ForegroundColor Green
    Write-Host "=" * 60 -ForegroundColor Green
    Write-Host ""
    Write-Host "📋 次のステップ:" -ForegroundColor Yellow
    Write-Host "  1. 新しいPowerShellセッションを開く" -ForegroundColor White
    Write-Host "  2. プロジェクトディレクトリに移動:" -ForegroundColor White
    Write-Host "     cd `"$PROJECT_ROOT`"" -ForegroundColor Cyan
    Write-Host "  3. Windows実機テストを実行:" -ForegroundColor White
    Write-Host "     .\scripts\windows\run_windows_tests.ps1" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "📄 追加情報:" -ForegroundColor Yellow
    Write-Host "  - セットアップログ: $LOG_PATH" -ForegroundColor White
    Write-Host "  - 仮想環境パス: $VENV_PATH" -ForegroundColor White
    Write-Host ""
}

# ====================================================================
# メイン実行
# ====================================================================

try {
    Write-Log "=== Windows環境セットアップ開始 ==="
    
    # 1. Python インストール確認
    Write-Host "🐍 Python インストール確認..." -ForegroundColor Cyan
    if (-not (Test-PythonInstallation)) {
        Write-Log "Python installation check failed"
        exit 1
    }
    
    # 2. 仮想環境セットアップ
    if (-not (Setup-VirtualEnvironment)) {
        Write-Log "Virtual environment setup failed"
        exit 1
    }
    
    # 3. 依存関係インストール
    if (-not (Install-Dependencies)) {
        Write-Log "Dependencies installation failed"
        exit 1
    }
    
    # 4. ChromeDriver 動作確認
    if (-not (Test-ChromeDriver)) {
        Write-Host "⚠️  ChromeDriver テストに失敗しましたが、セットアップは続行します" -ForegroundColor Yellow
        Write-Log "ChromeDriver test failed but setup continues"
    }
    
    # 5. 完了メッセージ
    Write-Log "=== Windows環境セットアップ完了 ==="
    Show-NextSteps
    
} catch {
    Write-Host "❌ セットアップ中に予期しないエラーが発生しました: $($_.Exception.Message)" -ForegroundColor Red
    Write-Log "Unexpected error during setup: $($_.Exception.Message)"
    exit 1
}
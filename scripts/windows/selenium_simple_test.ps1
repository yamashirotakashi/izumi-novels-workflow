# ====================================================================
# シンプルなSelenium Amazon検索テスト（webdriver-manager使用）
# ====================================================================

param(
    [string]$Query = "異世界転生",
    [int]$MaxResults = 3
)

$ErrorActionPreference = "Stop"

Write-Host "[START] Simple Selenium Test" -ForegroundColor Cyan

# 既存のChromeプロセスを終了
Write-Host "[INFO] Cleaning up Chrome processes..." -ForegroundColor Yellow
Get-Process -Name "chrome*","chromedriver*" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 1

$PROJECT_ROOT = Split-Path -Parent -Path (Split-Path -Parent -Path $PSScriptRoot)
$VENV_PATH = Join-Path $PROJECT_ROOT "venv"

# 仮想環境アクティベート
$activateScript = Join-Path $VENV_PATH "Scripts\Activate.ps1"
if (Test-Path $activateScript) {
    & $activateScript
    Write-Host "[OK] Virtual environment activated" -ForegroundColor Green
}

# webdriver-managerインストール確認
Write-Host "[INFO] Installing webdriver-manager if needed..." -ForegroundColor Yellow
pip install -q webdriver-manager 2>$null

# シンプルなSeleniumスクリプト
$pythonScript = @"
#!/usr/bin/env python3
import sys
import time
import json
from pathlib import Path

print("[INFO] Starting simple Selenium test...")

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from webdriver_manager.chrome import ChromeDriverManager
    
    print("[OK] Modules loaded")
    
    # Chrome設定（最小限）
    chrome_options = Options()
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--window-size=1280,800')
    
    # webdriver-managerで自動的にChromeDriverをダウンロード
    print("[INFO] Setting up ChromeDriver...")
    service = Service(ChromeDriverManager().install())
    
    print("[INFO] Starting Chrome...")
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    try:
        # Amazon検索
        print("[INFO] Navigating to Amazon...")
        driver.get("https://www.amazon.co.jp")
        time.sleep(2)
        
        # 検索実行
        print("[INFO] Searching for: $Query")
        search_box = driver.find_element(By.ID, "twotabsearchtextbox")
        search_box.clear()
        search_box.send_keys("$Query")
        search_box.send_keys(Keys.RETURN)
        
        # 結果待機
        print("[INFO] Waiting for results...")
        time.sleep(3)
        
        # 結果取得
        results = []
        try:
            products = driver.find_elements(By.CSS_SELECTOR, '[data-component-type="s-search-result"]')[:$MaxResults]
            print(f"[INFO] Found {len(products)} products")
            
            for i, product in enumerate(products, 1):
                try:
                    title = product.find_element(By.CSS_SELECTOR, 'h2 span').text
                    results.append(title)
                    print(f"  {i}. {title[:60]}...")
                except:
                    pass
                    
        except Exception as e:
            print(f"[WARN] Could not extract products: {e}")
        
        if results:
            print(f"[SUCCESS] Found {len(results)} books")
            
            # 結果保存
            result_file = Path(r"C:\Users\tky99\DEV\izumi-novels-workflow\real_scraping_results\simple_test.json")
            result_file.parent.mkdir(exist_ok=True)
            
            with open(result_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "query": "$Query",
                    "results": results,
                    "count": len(results)
                }, f, ensure_ascii=False, indent=2)
            
            print(f"[SAVED] Results to: {result_file}")
        else:
            print("[WARN] No results found")
            
    finally:
        print("[INFO] Closing browser...")
        driver.quit()
        
except ImportError as e:
    print(f"[FAIL] Import error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"[FAIL] Error: {e}")
    sys.exit(1)

print("[COMPLETE] Test finished")
"@

$tempScriptPath = Join-Path $PROJECT_ROOT "temp_simple_test.py"

try {
    # Pythonスクリプト実行
    $pythonScript | Out-File -FilePath $tempScriptPath -Encoding UTF8
    
    Write-Host "[TEST] Running simple search test..." -ForegroundColor Cyan
    
    $output = python $tempScriptPath 2>&1
    $exitCode = $LASTEXITCODE
    
    Write-Host $output -ForegroundColor White
    
    if ($exitCode -eq 0) {
        Write-Host "[SUCCESS] Test completed successfully!" -ForegroundColor Green
        
        # 結果確認
        $resultFile = Join-Path $PROJECT_ROOT "real_scraping_results\simple_test.json"
        if (Test-Path $resultFile) {
            $data = Get-Content $resultFile -Raw | ConvertFrom-Json
            Write-Host "[RESULT] Found $($data.count) items for query: $($data.query)" -ForegroundColor Yellow
        }
    } else {
        Write-Host "[FAIL] Test failed with exit code: $exitCode" -ForegroundColor Red
    }
    
    Remove-Item $tempScriptPath -Force -ErrorAction SilentlyContinue
    exit $exitCode
    
} catch {
    Write-Host "[FAIL] Script error: $($_.Exception.Message)" -ForegroundColor Red
    Remove-Item $tempScriptPath -Force -ErrorAction SilentlyContinue
    exit 1
}
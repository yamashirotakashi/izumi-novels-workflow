# ====================================================================
# Selenium版Amazon検索テスト（Playwrightフリーズ回避）
# ====================================================================

param(
    [string]$Query = "異世界転生",
    [switch]$Headless = $false,
    [int]$MaxResults = 3
)

$ErrorActionPreference = "Stop"

$PROJECT_ROOT = Split-Path -Parent -Path (Split-Path -Parent -Path $PSScriptRoot)
$VENV_PATH = Join-Path $PROJECT_ROOT "venv"

Write-Host "[START] Selenium Amazon Search Test" -ForegroundColor Cyan
Write-Host "Query: $Query" -ForegroundColor Yellow
Write-Host "Headless: $Headless" -ForegroundColor Yellow

# 仮想環境アクティベート
$activateScript = Join-Path $VENV_PATH "Scripts\Activate.ps1"
if (Test-Path $activateScript) {
    & $activateScript
    Write-Host "[OK] Virtual environment activated" -ForegroundColor Green
}

# Selenium版テストスクリプト
$pythonScript = @"
#!/usr/bin/env python3
import sys
import time
import json
from pathlib import Path

# プロジェクトルート設定
project_root = Path(r"C:\Users\tky99\DEV\izumi-novels-workflow")
results_path = project_root / 'real_scraping_results'
results_path.mkdir(exist_ok=True)

print("[INFO] Starting Selenium-based Amazon search test...")

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    from selenium.common.exceptions import TimeoutException, NoSuchElementException
    
    print("[OK] Selenium modules loaded")
    
    # Chrome設定
    chrome_options = Options()
    headless_mode = "$($Headless.ToString().ToLower())" == "true"
    if headless_mode:
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-gpu')
    
    # ユニークなユーザーデータディレクトリを使用
    import tempfile
    import os
    temp_dir = tempfile.mkdtemp(prefix='chrome_selenium_')
    chrome_options.add_argument(f'--user-data-dir={temp_dir}')
    
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    
    print("[INFO] Starting Chrome driver...")
    driver = webdriver.Chrome(options=chrome_options)
    driver.set_window_size(1280, 800)
    
    try:
        # Amazon Kindleストアにアクセス
        print("[INFO] Navigating to Amazon Kindle store...")
        driver.get("https://www.amazon.co.jp/kindle-store")
        time.sleep(2)
        
        # 検索ボックスを探す
        print("[INFO] Finding search box...")
        search_box = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "twotabsearchtextbox"))
        )
        
        # 検索クエリ入力
        print(f"[INFO] Entering search query: $Query")
        search_box.clear()
        search_box.send_keys("$Query いずみノベルズ")
        search_box.send_keys(Keys.RETURN)
        
        # 検索結果待機
        print("[INFO] Waiting for search results...")
        time.sleep(3)
        
        # 検索結果取得
        results = []
        try:
            # 商品要素を探す
            product_elements = driver.find_elements(By.CSS_SELECTOR, '[data-component-type="s-search-result"]')[:$MaxResults]
            
            print(f"[INFO] Found {len(product_elements)} products")
            
            for i, elem in enumerate(product_elements, 1):
                try:
                    # タイトル取得
                    title_elem = elem.find_element(By.CSS_SELECTOR, 'h2 a span')
                    title = title_elem.text
                    
                    # URL取得
                    link_elem = elem.find_element(By.CSS_SELECTOR, 'h2 a')
                    url = link_elem.get_attribute('href')
                    
                    # 価格取得（可能なら）
                    price = "N/A"
                    try:
                        price_elem = elem.find_element(By.CSS_SELECTOR, '.a-price .a-offscreen')
                        price = price_elem.get_attribute('textContent')
                    except:
                        pass
                    
                    result = {
                        "title": title,
                        "url": url,
                        "price": price
                    }
                    results.append(result)
                    
                    print(f"[FOUND] {i}. {title[:50]}...")
                    print(f"        Price: {price}")
                    
                except Exception as e:
                    print(f"[WARN] Failed to extract product {i}: {e}")
                    continue
            
        except Exception as e:
            print(f"[ERROR] Failed to find products: {e}")
        
        # 結果保存
        result_data = {
            "query": "$Query",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_found": len(results),
            "books": results,
            "test_type": "selenium_test"
        }
        
        result_file = results_path / "selenium_amazon_test.json"
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(result_data, f, ensure_ascii=False, indent=2)
        
        print(f"[SAVED] Results saved to: {result_file}")
        
        if results:
            print(f"[SUCCESS] Found {len(results)} books")
        else:
            print("[WARN] No books found")
        
    finally:
        print("[INFO] Closing browser...")
        driver.quit()
        
        # 一時ディレクトリのクリーンアップ
        try:
            import shutil
            if 'temp_dir' in locals() and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)
                print("[INFO] Cleaned up temp directory")
        except:
            pass
        
except ImportError as e:
    print(f"[FAIL] Module import error: {e}")
    print("[HINT] Try: pip install selenium webdriver-manager")
    sys.exit(1)
    
except Exception as e:
    print(f"[FAIL] Test error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("[COMPLETE] Selenium test finished")
"@

$tempScriptPath = Join-Path $PROJECT_ROOT "temp_selenium_test.py"

try {
    # Pythonスクリプト実行
    $pythonScript | Out-File -FilePath $tempScriptPath -Encoding UTF8
    
    Write-Host "[TEST] Running Selenium-based search..." -ForegroundColor Cyan
    
    $startTime = Get-Date
    $output = python $tempScriptPath 2>&1
    $exitCode = $LASTEXITCODE
    $endTime = Get-Date
    $duration = ($endTime - $startTime).TotalSeconds
    
    if ($exitCode -eq 0) {
        Write-Host "[SUCCESS] Selenium test completed ($($duration.ToString('F1')) sec)" -ForegroundColor Green
    } else {
        Write-Host "[FAIL] Selenium test failed ($($duration.ToString('F1')) sec)" -ForegroundColor Red
    }
    
    Write-Host "Test Output:" -ForegroundColor Yellow
    Write-Host $output -ForegroundColor White
    
    # 結果ファイル確認
    $resultFile = Join-Path $PROJECT_ROOT "real_scraping_results\selenium_amazon_test.json"
    if (Test-Path $resultFile) {
        Write-Host "[INFO] Checking results..." -ForegroundColor Cyan
        $resultData = Get-Content $resultFile -Raw | ConvertFrom-Json
        Write-Host "[RESULT] Found $($resultData.total_found) books" -ForegroundColor Green
        if ($resultData.books.Count -gt 0) {
            Write-Host "[TOP BOOK] $($resultData.books[0].title)" -ForegroundColor Yellow
        }
    }
    
    Remove-Item $tempScriptPath -Force -ErrorAction SilentlyContinue
    
    exit $exitCode
    
} catch {
    Write-Host "[FAIL] Script error: $($_.Exception.Message)" -ForegroundColor Red
    Remove-Item $tempScriptPath -Force -ErrorAction SilentlyContinue
    exit 1
}
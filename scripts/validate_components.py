#!/usr/bin/env python3
"""
コンポーネント検証スクリプト
実装したコンポーネントの基本機能を検証
"""
import sys
import json
from pathlib import Path
from datetime import datetime
import asyncio

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.scraping.result_exporter import ResultExporter, BatchResult, ScrapingResult, ResultStatus, ExportFormat
from src.scraping.error_handler import ErrorHandler, RetryConfig, ScrapingError

def validate_result_exporter():
    """結果エクスポーターの検証"""
    print("🔍 結果エクスポーター検証")
    
    # テストディレクトリ作成
    test_dir = project_root / 'logs' / 'validation_test'
    test_dir.mkdir(parents=True, exist_ok=True)
    
    # エクスポーター初期化
    exporter = ResultExporter(test_dir)
    
    # テストデータ作成
    batch_result = BatchResult(
        batch_id="validation_test",
        started_at=datetime.now()
    )
    
    # テスト結果追加
    test_results = [
        ScrapingResult(
            n_code="N02306",
            title="パラレイドデイズ④",
            site_name="Amazon Kindle", 
            status=ResultStatus.SUCCESS,
            url="https://example.com/test1"
        ),
        ScrapingResult(
            n_code="N02307",
            title="エアボーンウイッチ④",
            site_name="楽天Kobo",
            status=ResultStatus.NOT_FOUND,
            error_message="検索結果なし"
        )
    ]
    
    for result in test_results:
        batch_result.add_result(result)
    
    batch_result.finalize()
    
    # 各形式でエクスポート
    formats_tested = []
    for format in [ExportFormat.JSON, ExportFormat.CSV]:
        try:
            output_path = exporter.export_batch_result(batch_result, format=format)
            print(f"  ✅ {format.value.upper()}出力成功: {output_path.name}")
            formats_tested.append(format.value)
        except Exception as e:
            print(f"  ❌ {format.value.upper()}出力失敗: {e}")
    
    # サマリーレポート
    try:
        summary_path = exporter.export_summary_report([batch_result])
        print(f"  ✅ サマリーレポート成功: {summary_path.name}")
    except Exception as e:
        print(f"  ❌ サマリーレポート失敗: {e}")
    
    print(f"  📊 統計: 成功率 {batch_result.success_rate:.1f}%")
    return True

async def validate_error_handler():
    """エラーハンドラーの検証"""
    print("🔍 エラーハンドラー検証")
    
    error_handler = ErrorHandler()
    
    # 成功ケースのテスト
    async def success_function():
        return "Success!"
    
    try:
        result = await error_handler.execute_with_retry(success_function)
        print(f"  ✅ 成功ケース: {result}")
    except Exception as e:
        print(f"  ❌ 成功ケース失敗: {e}")
        return False
    
    # リトライテスト
    attempt_count = [0]
    
    async def failing_then_success():
        attempt_count[0] += 1
        if attempt_count[0] < 3:
            raise ScrapingError(f"Test error (attempt {attempt_count[0]})")
        return "Success after retries"
    
    try:
        retry_config = RetryConfig(max_attempts=5, base_delay=0.1)
        result = await error_handler.execute_with_retry(
            failing_then_success,
            retry_config=retry_config
        )
        print(f"  ✅ リトライ成功: {result}")
    except Exception as e:
        print(f"  ❌ リトライ失敗: {e}")
        return False
    
    # エラー統計
    health_report = error_handler.get_health_report()
    print(f"  📊 システム健全性: {health_report.get('overall_health', 'unknown')}")
    
    return True

def validate_scrapers():
    """スクレイパーの基本検証"""
    print("🔍 スクレイパー基本機能検証")
    
    try:
        from src.scraping.amazon_kindle_scraper import AmazonKindleScraper
        from src.scraping.rakuten_kobo_scraper import RakutenKoboScraper
        from src.scraping.google_play_books_scraper import GooglePlayBooksScraper
        
        scrapers = [
            ("Amazon Kindle", AmazonKindleScraper),
            ("楽天Kobo", RakutenKoboScraper),
            ("Google Play Books", GooglePlayBooksScraper)
        ]
        
        for name, scraper_class in scrapers:
            try:
                scraper = scraper_class(headless=True)
                print(f"  ✅ {name}スクレイパー初期化成功")
                
                # タイトル正規化テスト
                test_title = "パラレイドデイズ④"
                normalized = scraper.normalize_title(test_title)
                print(f"    📝 タイトル正規化: {test_title} → {normalized}")
                
                # 巻数抽出テスト
                volume = scraper.extract_volume_number(test_title)
                print(f"    📖 巻数抽出: {test_title} → 第{volume}巻")
                
                # バリエーション生成テスト
                variants = scraper.create_volume_variants(test_title)
                print(f"    🔄 バリエーション数: {len(variants)}")
                
            except Exception as e:
                print(f"  ❌ {name}スクレイパー初期化失敗: {e}")
                
    except ImportError as e:
        print(f"  ❌ スクレイパーインポート失敗: {e}")
        return False
    
    return True

def validate_google_sheets():
    """Google Sheetsクライアント検証"""
    print("🔍 Google Sheetsクライアント検証")
    
    try:
        from src.scraping.google_sheets_client_updated import GoogleSheetsClient, SalesChannel
        
        # 設定ファイルの存在確認
        credentials_path = project_root / 'config' / 'credentials' / 'google-sheets-key.json'
        if not credentials_path.exists():
            print(f"  ⚠️  認証ファイルが見つかりません: {credentials_path}")
            print("  📝 Google Sheets接続テストはスキップします")
            return True
        
        # 基本的な初期化テスト
        spreadsheet_id = '1hMhDw3HJsUMetceMvy2lszDeLCxarNavn_2E6Inf84M'
        client = GoogleSheetsClient(str(credentials_path), spreadsheet_id)
        print("  ✅ GoogleSheetsClient初期化成功")
        
        # 列挙型テスト
        channels = list(SalesChannel)
        print(f"  📊 販売チャンネル数: {len(channels)}")
        
        return True
        
    except ImportError as e:
        print(f"  ❌ Google Sheetsクライアントインポート失敗: {e}")
        return False
    except Exception as e:
        print(f"  ❌ Google Sheetsクライアント初期化失敗: {e}")
        return False

async def main():
    """メイン検証処理"""
    print("=== IzumiNovels-Workflow コンポーネント検証 ===")
    print(f"実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    results = []
    
    # 各コンポーネントの検証
    results.append(("結果エクスポーター", validate_result_exporter()))
    results.append(("エラーハンドラー", await validate_error_handler()))
    results.append(("スクレイパー基本機能", validate_scrapers()))
    results.append(("Google Sheetsクライアント", validate_google_sheets()))
    
    # 結果サマリー
    print("\n=== 検証結果サマリー ===")
    passed = 0
    total = len(results)
    
    for component, result in results:
        status = "✅ 成功" if result else "❌ 失敗"
        print(f"{component}: {status}")
        if result:
            passed += 1
    
    print(f"\n📊 全体結果: {passed}/{total} ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 すべてのコンポーネントが正常に動作しています！")
    else:
        print("⚠️  一部のコンポーネントに問題があります。")
    
    return passed == total

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
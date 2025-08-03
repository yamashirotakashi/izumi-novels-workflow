#!/usr/bin/env python3
"""
統合テストスクリプト
全スクレイパーの統合テストとGoogle Sheets連携テスト
"""
import asyncio
import sys
import json
import uuid
from pathlib import Path
from datetime import datetime
import logging

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.scraping.amazon_kindle_scraper import AmazonKindleScraper
from src.scraping.rakuten_kobo_scraper import RakutenKoboScraper
from src.scraping.google_play_books_scraper import GooglePlayBooksScraper
from src.scraping.bookwalker_scraper import BookWalkerScraper
from src.scraping.google_sheets_client_consolidated import GoogleSheetsClient, SalesLinkUpdate, SalesChannel
from src.scraping.result_exporter import ResultExporter, BatchResult, ScrapingResult, ResultStatus, ExportFormat
from src.scraping.error_handler import ErrorHandler, RetryConfig

# ロガー設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class IntegratedTestRunner:
    """統合テスト実行クラス"""
    
    def __init__(self):
        self.batch_id = f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.results_dir = project_root / 'logs' / 'test_results'
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        # コンポーネントの初期化
        self.error_handler = ErrorHandler()
        self.result_exporter = ResultExporter(self.results_dir)
        self.batch_result = BatchResult(
            batch_id=self.batch_id,
            started_at=datetime.now()
        )
        
        # スクレイパーの設定
        screenshot_dir = self.results_dir / 'screenshots'
        screenshot_dir.mkdir(exist_ok=True)
        
        self.scrapers = {
            'Amazon Kindle': AmazonKindleScraper(
                headless=True,
                timeout=20000,
                screenshot_dir=screenshot_dir
            ),
            '楽天Kobo': RakutenKoboScraper(
                headless=True,
                timeout=20000,  
                screenshot_dir=screenshot_dir
            ),
            'Google Play Books': GooglePlayBooksScraper(
                headless=True,
                timeout=20000,
                screenshot_dir=screenshot_dir
            ),
            'BOOK☆WALKER': BookWalkerScraper(
                headless=True,
                timeout=30000,  # BOOK☆WALKERは少し長めのタイムアウト
                screenshot_dir=screenshot_dir
            )
        }
    
    async def run_full_test(self):
        """フルテストの実行"""
        print(f"=== 統合テスト開始 (ID: {self.batch_id}) ===")
        print(f"結果保存先: {self.results_dir}")
        print()
        
        # テストデータの読み込み
        test_books = await self._load_test_data()
        print(f"テスト対象書籍: {len(test_books)}冊")
        
        # 1. スクレイパー個別テスト
        print("\n📖 Phase 1: 個別スクレイパーテスト")
        await self._test_individual_scrapers(test_books)
        
        # 2. Google Sheets連携テスト
        print("\n📊 Phase 2: Google Sheets連携テスト")
        await self._test_google_sheets_integration()
        
        # 3. エラーハンドリングテスト
        print("\n⚡ Phase 3: エラーハンドリングテスト")
        await self._test_error_handling()
        
        # 4. 結果出力テスト
        print("\n📤 Phase 4: 結果出力テスト")
        await self._test_result_export()
        
        # 最終レポート
        self.batch_result.finalize()
        await self._generate_final_report()
        
        print(f"\n✅ 統合テスト完了!")
        print(f"成功率: {self.batch_result.success_rate:.1f}%")
        print(f"処理時間: {self.batch_result.processing_time:.1f}秒")
    
    async def _load_test_data(self):
        """テストデータの読み込み"""
        test_data_path = project_root / 'config' / 'test_data.json'
        with open(test_data_path, 'r', encoding='utf-8') as f:
            test_data = json.load(f)
        return test_data['test_books']
    
    async def _test_individual_scrapers(self, test_books):
        """個別スクレイパーのテスト"""
        for scraper_name, scraper in self.scrapers.items():
            print(f"\n🔍 {scraper_name} テスト開始")
            
            async with scraper:
                for book in test_books:
                    n_code = book['n_code']
                    title = book['title']
                    
                    print(f"  📚 {title} ({n_code})")
                    start_time = datetime.now()
                    
                    try:
                        url = await scraper.search_book(title, n_code)
                        end_time = datetime.now()
                        processing_time = (end_time - start_time).total_seconds()
                        
                        if url:
                            result = ScrapingResult(
                                n_code=n_code,
                                title=title,
                                site_name=scraper_name,
                                status=ResultStatus.SUCCESS,
                                url=url,
                                processing_time=processing_time
                            )
                            print(f"    ✅ 成功: {url}")
                        else:
                            result = ScrapingResult(
                                n_code=n_code,
                                title=title,
                                site_name=scraper_name,
                                status=ResultStatus.NOT_FOUND,
                                processing_time=processing_time,
                                error_message="URL not found"
                            )
                            print(f"    ❌ 見つからず")
                        
                        self.batch_result.add_result(result)
                        
                    except Exception as e:
                        end_time = datetime.now()
                        processing_time = (end_time - start_time).total_seconds()
                        
                        result = ScrapingResult(
                            n_code=n_code,
                            title=title,
                            site_name=scraper_name,
                            status=ResultStatus.ERROR,
                            processing_time=processing_time,
                            error_message=str(e)
                        )
                        self.batch_result.add_result(result)
                        print(f"    💥 エラー: {str(e)[:50]}...")
                    
                    # 書籍間の待機
                    await asyncio.sleep(2)
                
                # スクレイパー統計の表示
                stats = scraper.get_stats()
                print(f"  📊 統計: 成功率 {stats.get('success_rate', 'N/A')}")
    
    async def _test_google_sheets_integration(self):
        """Google Sheets連携テスト"""
        try:
            credentials_path = 'config/credentials/google-sheets-key.json'
            spreadsheet_id = '1hMhDw3HJsUMetceMvy2lszDeLCxarNavn_2E6Inf84M'
            
            client = GoogleSheetsClient(credentials_path, spreadsheet_id)
            
            # 1. 書籍データ読み取りテスト
            print("  📖 書籍データ読み取りテスト")
            books = client.read_all_books()
            print(f"    ✅ {len(books)}冊の書籍データを読み取り")
            
            # 2. 統計情報テスト
            print("  📊 統計情報テスト")
            stats = client.get_summary_stats()
            print(f"    ✅ 収集率: {stats.get('collection_rate', 0):.1f}%")
            
            # 3. テスト用リンク更新（実際のシートは更新しない）
            print("  🔗 リンク更新テスト（模擬）")
            test_updates = []
            for result in self.batch_result.results:
                if result.status == ResultStatus.SUCCESS and result.url:
                    # チャンネルマッピング（サイト名→チャンネル）
                    channel_map = {
                        'Amazon Kindle': SalesChannel.KINDLE,
                        '楽天Kobo': SalesChannel.KOBO,
                        'Google Play Books': SalesChannel.GOOGLE,
                        'BOOK☆WALKER': SalesChannel.BOOKWALKER
                    }
                    
                    if result.site_name in channel_map:
                        update = SalesLinkUpdate(
                            n_code=result.n_code,
                            channel=channel_map[result.site_name],
                            url=result.url,
                            scraped_at=result.scraped_at.isoformat()
                        )
                        test_updates.append(update)
            
            print(f"    📝 {len(test_updates)}件の更新データを準備")
            print("    ⚠️  実際のシート更新はスキップ（テストモード）")
            
        except Exception as e:
            print(f"    💥 Google Sheets連携エラー: {e}")
    
    async def _test_error_handling(self):
        """エラーハンドリングテスト"""
        print("  ⚡ リトライ機構テスト")
        
        # 模擬エラー関数
        async def failing_function(attempt_count=[0]):
            attempt_count[0] += 1
            if attempt_count[0] < 3:
                raise Exception(f"Test error (attempt {attempt_count[0]})")
            return "Success after retries"
        
        try:
            retry_config = RetryConfig(max_attempts=5, base_delay=0.1)
            result = await self.error_handler.execute_with_retry(
                failing_function,
                retry_config=retry_config
            )
            print(f"    ✅ リトライ成功: {result}")
        except Exception as e:
            print(f"    ❌ リトライ失敗: {e}")
        
        # エラー統計の表示
        health_report = self.error_handler.get_health_report()
        print(f"    📊 システム健全性: {health_report.get('overall_health', 'unknown')}")
    
    async def _test_result_export(self):
        """結果出力テスト"""
        formats = [ExportFormat.JSON, ExportFormat.CSV]
        
        for format in formats:
            try:
                output_path = self.result_exporter.export_batch_result(
                    self.batch_result,
                    format=format
                )
                print(f"    ✅ {format.value.upper()}出力: {output_path.name}")
            except Exception as e:
                print(f"    ❌ {format.value.upper()}出力エラー: {e}")
    
    async def _generate_final_report(self):
        """最終レポートの生成"""
        # 詳細結果の出力
        json_path = self.result_exporter.export_batch_result(
            self.batch_result,
            format=ExportFormat.JSON,
            filename=f"integrated_test_results_{self.batch_id}.json"
        )
        
        csv_path = self.result_exporter.export_batch_result(
            self.batch_result,
            format=ExportFormat.CSV,
            filename=f"integrated_test_results_{self.batch_id}.csv"
        )
        
        # サマリーレポート
        summary_path = self.result_exporter.export_summary_report(
            [self.batch_result],
            filename=f"integrated_test_summary_{self.batch_id}.json"
        )
        
        print(f"\n📋 最終レポート:")
        print(f"  詳細結果 (JSON): {json_path}")
        print(f"  詳細結果 (CSV): {csv_path}")
        print(f"  サマリー: {summary_path}")
        
        # 統計サマリー
        print(f"\n📊 テスト統計:")
        print(f"  総実行数: {self.batch_result.total_books}")
        print(f"  成功: {self.batch_result.successful_results}")
        print(f"  失敗: {self.batch_result.failed_results}")
        print(f"  見つからず: {self.batch_result.skipped_results}")
        print(f"  成功率: {self.batch_result.success_rate:.1f}%")
        print(f"  総処理時間: {self.batch_result.processing_time:.1f}秒")
        
        # サイト別統計
        site_stats = {}
        for result in self.batch_result.results:
            site = result.site_name
            if site not in site_stats:
                site_stats[site] = {'total': 0, 'success': 0}
            site_stats[site]['total'] += 1
            if result.status == ResultStatus.SUCCESS:
                site_stats[site]['success'] += 1
        
        print(f"\n🌐 サイト別統計:")
        for site, stats in site_stats.items():
            success_rate = (stats['success'] / stats['total'] * 100) if stats['total'] > 0 else 0
            print(f"  {site}: {stats['success']}/{stats['total']} ({success_rate:.1f}%)")


async def main():
    """メイン処理"""
    test_runner = IntegratedTestRunner()
    await test_runner.run_full_test()


if __name__ == "__main__":
    asyncio.run(main())
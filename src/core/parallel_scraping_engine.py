#!/usr/bin/env python3
"""
並列スクレイピングエンジン - 11サイト同時実行基盤
Parallel Scraping Engine - 11-site Concurrent Execution Foundation

Chrome for Testing統合により、Snap制約問題を完全克服した並列実行システム
Parallel execution system with Snap constraint issues completely overcome through Chrome for Testing integration
"""
import asyncio
import time
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, asdict
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import threading

# プロジェクト内インポート
import sys
sys.path.append(str(Path(__file__).parent.parent))

from scrapers.playwright_base_scraper import PlaywrightBaseScraper, BookInfo, ScrapingResult

@dataclass
class SiteConfig:
    """サイト設定データクラス"""
    site_id: str
    site_name: str
    enabled: bool = True
    priority: int = 1  # 1=高, 2=中, 3=低
    timeout: int = 30  # タイムアウト秒数
    max_retries: int = 3
    scraper_class: Optional[str] = None

@dataclass
class ParallelScrapingRequest:
    """並列スクレイピングリクエスト"""
    query: str
    target_sites: List[str]  # サイトIDリスト
    max_concurrent: int = 5  # 最大同時実行数
    timeout_per_site: int = 30
    include_details: bool = False  # 詳細情報取得フラグ

@dataclass
class ParallelScrapingResult:
    """並列スクレイピング結果"""
    query: str
    total_sites: int
    successful_sites: int
    failed_sites: int
    total_books_found: int
    execution_time: float
    results_per_site: Dict[str, ScrapingResult]
    errors: Dict[str, str]
    started_at: str
    completed_at: str

class ParallelScrapingEngine:
    """並列スクレイピングエンジン - Chrome for Testing基盤"""
    
    def __init__(self):
        self.config_path = Path(__file__).parent.parent.parent / "config" / "site_selectors.json"
        self.sites_config = self._load_sites_config()
        self.scrapers = {}  # サイトID -> スクレイパーインスタンス
        self.semaphore = None  # 同時実行制限
        self.executor = ThreadPoolExecutor(max_workers=10)
        
        # ログ設定
        self._setup_logging()
        
        # 11サイト設定
        self.target_sites = {
            "amazon_kindle": SiteConfig("amazon_kindle", "Amazon Kindle", priority=1),
            "bookwalker": SiteConfig("bookwalker", "BOOK☆WALKER", priority=1),
            "ebookjapan": SiteConfig("ebookjapan", "ebookjapan", priority=1), 
            "rakuten_kobo": SiteConfig("rakuten_kobo", "楽天Kobo", priority=1),
            "booklive": SiteConfig("booklive", "BookLive", priority=2),
            "honto": SiteConfig("honto", "honto", priority=2),
            "kinoppy": SiteConfig("kinoppy", "紀伊國屋書店Kinoppy", priority=2),
            "apple_books": SiteConfig("apple_books", "Apple Books", priority=3),
            "google_play_books": SiteConfig("google_play_books", "Google Play Books", priority=1),
            "reader_store": SiteConfig("reader_store", "Reader Store", priority=3),
            "amazon_pod": SiteConfig("amazon_pod", "Amazon POD", priority=2)
        }
        
        print(f"✅ 並列スクレイピングエンジン初期化完了 ({len(self.target_sites)}サイト対応)")
    
    def _setup_logging(self):
        """ログ設定"""
        log_dir = Path(__file__).parent.parent.parent / "logs"
        log_dir.mkdir(exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / "parallel_scraping.log"),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def _load_sites_config(self) -> Dict[str, Any]:
        """サイト設定読み込み"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ 設定ファイル読み込みエラー: {e}")
            return {}
    
    async def scrape_all_sites(self, request: ParallelScrapingRequest) -> ParallelScrapingResult:
        """全サイト並列スクレイピング実行"""
        print(f"🚀 並列スクレイピング開始: '{request.query}'")
        print(f"🎯 対象サイト: {len(request.target_sites)}サイト")
        print(f"⚡ 最大同時実行: {request.max_concurrent}")
        print("=" * 60)
        
        start_time = time.time()
        started_at = datetime.now().isoformat()
        
        # 同時実行制限セマフォ
        self.semaphore = asyncio.Semaphore(request.max_concurrent)
        
        # 対象サイトフィルタリング
        target_configs = []
        for site_id in request.target_sites:
            if site_id in self.target_sites and self.target_sites[site_id].enabled:
                target_configs.append(self.target_sites[site_id])
            else:
                print(f"⚠️ 無効なサイトID: {site_id}")
        
        # 優先度でソート
        target_configs.sort(key=lambda x: x.priority)
        
        # 並列タスク作成
        tasks = []
        for config in target_configs:
            task = asyncio.create_task(
                self._scrape_single_site(config, request.query, request.timeout_per_site)
            )
            tasks.append(task)
        
        # 並列実行
        print(f"⚡ {len(tasks)}サイトの並列スクレイピング開始...")
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 結果集計
        execution_time = time.time() - start_time
        completed_at = datetime.now().isoformat()
        
        successful_results = {}
        failed_results = {}
        errors = {}
        total_books = 0
        
        for i, result in enumerate(results):
            config = target_configs[i]
            site_id = config.site_id
            
            if isinstance(result, Exception):
                # 例外が発生した場合
                errors[site_id] = str(result)
                failed_results[site_id] = ScrapingResult(
                    site_name=config.site_name,
                    site_id=site_id,
                    query=request.query,
                    success=False,
                    books_found=[],
                    error_message=str(result)
                )
                print(f"❌ {config.site_name}: {str(result)}")
            elif result and result.success:
                # 成功
                successful_results[site_id] = result
                total_books += len(result.books_found)
                print(f"✅ {config.site_name}: {len(result.books_found)}冊発見")
            else:
                # 失敗（例外ではない）
                failed_results[site_id] = result
                if result:
                    errors[site_id] = result.error_message or "不明なエラー"
                print(f"❌ {config.site_name}: スクレイピング失敗")
        
        # 全結果をマージ
        all_results = {**successful_results, **failed_results}
        
        # 結果サマリー作成
        final_result = ParallelScrapingResult(
            query=request.query,
            total_sites=len(target_configs),
            successful_sites=len(successful_results),
            failed_sites=len(failed_results),
            total_books_found=total_books,
            execution_time=execution_time,
            results_per_site=all_results,
            errors=errors,
            started_at=started_at,
            completed_at=completed_at
        )
        
        # 結果サマリー表示
        self._print_results_summary(final_result)
        
        return final_result
    
    async def _scrape_single_site(self, config: SiteConfig, query: str, timeout: int) -> Optional[ScrapingResult]:
        """単一サイトスクレイピング実行"""
        async with self.semaphore:  # 同時実行制限
            try:
                print(f"🔍 {config.site_name} スクレイピング開始...")
                
                # スクレイパー取得または作成
                scraper = await self._get_scraper(config)
                if not scraper:
                    raise Exception(f"スクレイパー作成失敗: {config.site_id}")
                
                # タイムアウト付きでスクレイピング実行
                result = await asyncio.wait_for(
                    scraper.scrape_with_retry(query),
                    timeout=timeout
                )
                
                return result
                
            except asyncio.TimeoutError:
                return ScrapingResult(
                    site_name=config.site_name,
                    site_id=config.site_id,
                    query=query,
                    success=False,
                    books_found=[],
                    error_message=f"タイムアウト ({timeout}秒)"
                )
            except Exception as e:
                return ScrapingResult(
                    site_name=config.site_name,
                    site_id=config.site_id,
                    query=query,
                    success=False,
                    books_found=[],
                    error_message=str(e)
                )
    
    async def _get_scraper(self, config: SiteConfig) -> Optional[PlaywrightBaseScraper]:
        """スクレイパー取得（ファクトリーパターン）"""
        try:
            # サイト別スクレイパー作成
            if config.site_id == "amazon_kindle":
                from scrapers.amazon_kindle_scraper import AmazonKindleScraper
                scraper = AmazonKindleScraper()
            elif config.site_id == "rakuten_kobo":
                # 楽天Koboスクレイパー（今後実装）
                scraper = self._create_generic_scraper(config)
            elif config.site_id == "google_play_books":
                # Google Play Booksスクレイパー（今後実装）
                scraper = self._create_generic_scraper(config)
            else:
                # 汎用スクレイパー
                scraper = self._create_generic_scraper(config)
            
            # ブラウザセットアップ
            await scraper.setup_browser(headless=True)
            return scraper
            
        except Exception as e:
            print(f"❌ {config.site_name} スクレイパー作成エラー: {e}")
            return None
    
    def _create_generic_scraper(self, config: SiteConfig) -> PlaywrightBaseScraper:
        """汎用スクレイパー作成"""
        from scrapers.generic_scraper import GenericScraper
        return GenericScraper(config.site_id, config.site_name)
    
    def _print_results_summary(self, result: ParallelScrapingResult):
        """結果サマリー表示"""
        print("\n📊 並列スクレイピング結果サマリー")
        print("=" * 60)
        print(f"🔍 検索クエリ: '{result.query}'")
        print(f"📈 成功率: {result.successful_sites}/{result.total_sites} ({result.successful_sites/result.total_sites*100:.1f}%)")
        print(f"📚 総発見書籍数: {result.total_books_found}冊")
        print(f"⏱️ 実行時間: {result.execution_time:.2f}秒")
        
        if result.successful_sites > 0:
            print(f"\n✅ 成功サイト ({result.successful_sites}個):")
            for site_id, site_result in result.results_per_site.items():
                if site_result.success:
                    print(f"  📖 {site_result.site_name}: {len(site_result.books_found)}冊")
        
        if result.failed_sites > 0:
            print(f"\n❌ 失敗サイト ({result.failed_sites}個):")
            for site_id, error in result.errors.items():
                site_name = result.results_per_site.get(site_id, {}).site_name or site_id
                print(f"  ⚠️ {site_name}: {error}")
    
    def save_results(self, result: ParallelScrapingResult, output_path: Optional[Path] = None) -> Path:
        """結果をJSONファイルに保存"""
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            results_dir = Path(__file__).parent.parent.parent / "results"
            results_dir.mkdir(exist_ok=True)
            output_path = results_dir / f"scraping_result_{timestamp}.json"
        
        # 結果をJSON形式で保存
        result_dict = asdict(result)
        
        # ScrapingResultオブジェクトをdict化
        for site_id, site_result in result_dict["results_per_site"].items():
            result_dict["results_per_site"][site_id] = asdict(site_result)
            # BookInfoオブジェクトもdict化
            books_data = []
            for book in site_result.books_found:
                books_data.append(asdict(book))
            result_dict["results_per_site"][site_id]["books_found"] = books_data
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result_dict, f, ensure_ascii=False, indent=2)
        
        print(f"💾 結果保存完了: {output_path}")
        return output_path
    
    async def cleanup(self):
        """リソースクリーンアップ"""
        print("🧹 並列スクレイピングエンジンクリーンアップ...")
        
        # 全スクレイパーのクリーンアップ
        cleanup_tasks = []
        for scraper in self.scrapers.values():
            if scraper:
                cleanup_tasks.append(scraper.cleanup())
        
        if cleanup_tasks:
            await asyncio.gather(*cleanup_tasks, return_exceptions=True)
        
        # ThreadPoolExecutor終了
        self.executor.shutdown(wait=True)
        
        print("✅ クリーンアップ完了")

# テスト・デモ関数
async def demo_parallel_scraping():
    """並列スクレイピングエンジンのデモ"""
    print("🧪 並列スクレイピングエンジン デモ開始")
    print("=" * 60)
    
    try:
        engine = ParallelScrapingEngine()
        
        # テストリクエスト作成
        request = ParallelScrapingRequest(
            query="プログラミング Python",
            target_sites=["amazon_kindle", "rakuten_kobo", "google_play_books"],
            max_concurrent=3,
            timeout_per_site=20
        )
        
        # 並列スクレイピング実行
        result = await engine.scrape_all_sites(request)
        
        # 結果保存
        output_path = engine.save_results(result)
        
        # クリーンアップ
        await engine.cleanup()
        
        print(f"\n🎉 並列スクレイピングデモ完了！")
        print(f"📁 結果ファイル: {output_path}")
        return True
        
    except Exception as e:
        print(f"❌ デモエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = asyncio.run(demo_parallel_scraping())
    print(f"\n📊 デモ結果: {'✅ 成功' if success else '❌ 失敗'}")
    sys.exit(0 if success else 1)
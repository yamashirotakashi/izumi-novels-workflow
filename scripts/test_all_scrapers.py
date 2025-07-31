#!/usr/bin/env python3
"""
全サイトスクレイパー統合テストスクリプト
Phase 2実装の包括的評価
"""
import asyncio
import sys
import json
from pathlib import Path
from datetime import datetime
import logging

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.scraping.bookwalker_scraper import BookWalkerScraper
from src.scraping.ebookjapan_scraper import EbookjapanScraper
from src.scraping.booklive_scraper import BookLiveScraper
from src.scraping.apple_books_scraper import AppleBooksLinkGenerator
from src.scraping.honto_scraper import HontoScraper
from src.scraping.kinoppy_scraper import KinoppyScraper
from src.scraping.reader_store_scraper import ReaderStoreScraper

# ログ設定
logging.basicConfig(
    level=logging.INFO,  # DEBUGからINFOに変更（出力量削減）
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/all_scrapers_test.log')
    ]
)
logger = logging.getLogger(__name__)


async def test_scraper(scraper_class, scraper_name: str, test_books: list, isbn_books: dict = None):
    """個別スクレイパーのテスト実行"""
    print(f"\n🔍 {scraper_name} テスト開始")
    
    # スクレイパー別初期化パラメータ
    if scraper_name == "Apple Books":
        scraper = scraper_class(timeout=20, max_retries=2)
    elif scraper_name == "BOOK☆WALKER":
        # Playwright ベース（BaseScraper継承）
        scraper = scraper_class(headless=True, timeout=15000)
    else:
        # Requests ベース（RequestsScraper継承）
        scraper = scraper_class(timeout=15, max_retries=2)
    
    results = []
    
    try:
        async with scraper:
            for i, book in enumerate(test_books, 1):
                print(f"  📚 {i}/{len(test_books)}: {book['title'][:30]}...")
                
                start_time = datetime.now()
                
                try:
                    # Apple Books特殊対応（ISBN付き）
                    if scraper_name == "Apple Books" and isbn_books and book['n_code'] in isbn_books:
                        isbn = isbn_books[book['n_code']]
                        url = await scraper.search_book(book['title'], book['n_code'], isbn)
                    else:
                        url = await scraper.search_book(book['title'], book['n_code'])
                    
                    end_time = datetime.now()
                    processing_time = (end_time - start_time).total_seconds()
                    
                    result = {
                        'n_code': book['n_code'],
                        'title': book['title'],
                        'url': url,
                        'success': url is not None,
                        'processing_time': processing_time,
                        'timestamp': end_time.isoformat()
                    }
                    
                    if url:
                        print(f"    ✅ 成功 ({processing_time:.1f}s)")
                    else:
                        print(f"    ❌ 失敗 ({processing_time:.1f}s)")
                    
                    results.append(result)
                    
                except Exception as e:
                    end_time = datetime.now()
                    processing_time = (end_time - start_time).total_seconds()
                    
                    result = {
                        'n_code': book['n_code'],
                        'title': book['title'],
                        'url': None,
                        'success': False,
                        'error': str(e),
                        'processing_time': processing_time,
                        'timestamp': end_time.isoformat()
                    }
                    
                    print(f"    💥 エラー ({processing_time:.1f}s): {str(e)[:50]}...")
                    results.append(result)
                
                # サイト間待機
                if i < len(test_books):
                    await asyncio.sleep(1)
    
    except Exception as e:
        logger.error(f"{scraper_name} 初期化エラー: {e}")
        print(f"  💥 {scraper_name} 初期化エラー: {e}")
        return []
    
    return results


async def main():
    """メイン統合テスト実行"""
    print("=== IzumiNovels-Workflow Phase 2 統合テスト ===")
    print(f"開始時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("対象: 全7サイトの包括的スクレイピングテスト")
    print()
    
    # 共通テストデータ
    test_books = [
        {
            'n_code': 'N0000TEST',
            'title': 'ソードアート・オンライン1',
            'description': '人気シリーズ・基本形'
        },
        {
            'n_code': 'N02402',
            'title': 'クソゲー悪役令嬢①新装版',
            'description': '実際のなろう作品（シート未設定）'
        },
        {
            'n_code': 'N0230FK',
            'title': 'パラレイドデイズ④',
            'description': 'KADOKAWA系ライトノベル（丸数字巻数）'
        }
    ]
    
    # Apple Books用ISBN情報
    isbn_books = {
        'N0000TEST': '9784048671811',  # SAO
        'N02402': '',                  # クソゲー悪役令嬢（ISBNなし）
        'N0230FK': '9784040738222',   # パラレイドデイズ
    }
    
    # スクレイパー設定
    scrapers = [
        (EbookjapanScraper, "ebookjapan", "🥇 100%成功の基準サイト"),
        (BookWalkerScraper, "BOOK☆WALKER", "📈 改善中（66.7%）"),
        (BookLiveScraper, "BookLive", "📈 改善中（66.7%）"),
        (AppleBooksLinkGenerator, "Apple Books", "🎯 iTunes API特殊実装"),
        (HontoScraper, "honto", "✨ 新実装（ebookjapan継承）"),
        (KinoppyScraper, "Kinoppy", "✨ 新実装（ebookjapan継承）"),
        (ReaderStoreScraper, "Reader Store", "✨ 新実装（ebookjapan継承）")
    ]
    
    # ログディレクトリ作成
    Path('logs').mkdir(exist_ok=True)
    
    all_results = {}
    summary_stats = {}
    
    # 各スクレイパーのテスト実行
    for scraper_class, scraper_name, description in scrapers:
        print(f"\n{'='*60}")
        print(f"📋 {scraper_name}: {description}")
        
        # Apple Books特殊対応
        if scraper_name == "Apple Books":
            results = await test_scraper(scraper_class, scraper_name, test_books, isbn_books)
        else:
            results = await test_scraper(scraper_class, scraper_name, test_books)
        
        all_results[scraper_name] = results
        
        # 統計計算
        if results:
            successful = [r for r in results if r['success']]
            success_rate = (len(successful) / len(results)) * 100
            avg_time = sum(r['processing_time'] for r in results) / len(results)
            
            summary_stats[scraper_name] = {
                'total_tests': len(results),
                'successes': len(successful),
                'success_rate': success_rate,
                'avg_processing_time': avg_time
            }
            
            print(f"  📊 結果: {len(successful)}/{len(results)} ({success_rate:.1f}%) | 平均時間: {avg_time:.1f}s")
        else:
            summary_stats[scraper_name] = {
                'total_tests': 0,
                'successes': 0,
                'success_rate': 0.0,
                'avg_processing_time': 0.0
            }
            print(f"  📊 結果: テスト失敗")
        
        # サイト間の待機
        await asyncio.sleep(3)
    
    # 統合結果サマリー
    print(f"\n{'='*60}")
    print("🎯 Phase 2 統合テスト結果サマリー")
    print(f"{'='*60}")
    
    total_tests = sum(stats['total_tests'] for stats in summary_stats.values())
    total_successes = sum(stats['successes'] for stats in summary_stats.values())
    overall_success_rate = (total_successes / total_tests * 100) if total_tests > 0 else 0
    
    print(f"総合成績: {total_successes}/{total_tests} ({overall_success_rate:.1f}%)")
    print()
    print("📊 サイト別成績:")
    
    # 成功率順でソート
    sorted_stats = sorted(summary_stats.items(), key=lambda x: x[1]['success_rate'], reverse=True)
    
    for scraper_name, stats in sorted_stats:
        rate = stats['success_rate']
        successes = stats['successes']
        total = stats['total_tests']
        avg_time = stats['avg_processing_time']
        
        if rate == 100.0:
            emoji = "🥇"
            status = "Perfect!"
        elif rate >= 80.0:
            emoji = "🥈"
            status = "Excellent"
        elif rate >= 60.0:
            emoji = "🥉"
            status = "Good"
        else:
            emoji = "🤔"
            status = "Need Fix"
        
        print(f"  {emoji} {scraper_name:15}: {successes:1}/{total} ({rate:5.1f}%) {avg_time:4.1f}s - {status}")
    
    # パフォーマンス分析
    print(f"\n⚡ パフォーマンス分析:")
    fastest_site = min(sorted_stats, key=lambda x: x[1]['avg_processing_time'])
    slowest_site = max(sorted_stats, key=lambda x: x[1]['avg_processing_time'])
    
    print(f"  最速: {fastest_site[0]} ({fastest_site[1]['avg_processing_time']:.1f}s)")
    print(f"  最遅: {slowest_site[0]} ({slowest_site[1]['avg_processing_time']:.1f}s)")
    
    # 技術パターン分析
    print(f"\\n🔬 技術パターン分析:")
    ebookjapan_rate = summary_stats.get('ebookjapan', {}).get('success_rate', 0)
    inheritance_sites = ['honto', 'Kinoppy', 'Reader Store']
    
    inheritance_rates = [summary_stats.get(site, {}).get('success_rate', 0) 
                        for site in inheritance_sites if site in summary_stats]
    
    if inheritance_rates:
        avg_inheritance_rate = sum(inheritance_rates) / len(inheritance_rates)
        print(f"  ebookjapan基準: {ebookjapan_rate:.1f}%")
        print(f"  継承サイト平均: {avg_inheritance_rate:.1f}%")
        print(f"  継承効果: {'+' if avg_inheritance_rate >= 80 else '-'}{abs(avg_inheritance_rate - ebookjapan_rate):.1f}%")
    
    # 改善提案
    print(f"\\n💡 Phase 3 への提案:")
    problem_sites = [name for name, stats in summary_stats.items() 
                    if stats['success_rate'] < 80.0 and stats['total_tests'] > 0]
    
    if problem_sites:
        print(f"  🔧 要改善: {', '.join(problem_sites)}")
        print(f"  📋 対策: サイト構造再調査、セレクタ最適化")
    else:
        print(f"  🎉 全サイト80%以上達成！最終調整へ")
    
    # 結果保存
    comprehensive_results = {
        'test_info': {
            'test_type': 'Phase2_Integration_Test',
            'test_date': datetime.now().isoformat(),
            'total_sites': len(scrapers),
            'total_tests': total_tests,
            'total_successes': total_successes,
            'overall_success_rate': overall_success_rate,
            'test_books': test_books,
            'target_achievement': '全サイト80%以上',
        },
        'site_results': all_results,
        'summary_stats': summary_stats,
        'recommendations': {
            'problem_sites': problem_sites,
            'next_phase': 'Phase3_Final_Optimization' if not problem_sites else 'Phase2_Improvement'
        }
    }
    
    output_file = f"logs/integration_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(comprehensive_results, f, ensure_ascii=False, indent=2)
    
    print(f"\\n📄 詳細結果保存: {output_file}")
    print(f"\\n{'='*60}")
    print("🎯 Phase 2 統合テスト完了")
    print(f"{'='*60}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\\n⚠️ テストが中断されました")
    except Exception as e:
        logger.error(f"統合テストエラー: {e}")
        print(f"💥 予期しないエラー: {e}")
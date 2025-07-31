#!/usr/bin/env python3
"""
Kinoppy & Reader Store スクレイパー
新実装テスト（ebookjapan継承パターン）
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

from src.scraping.kinoppy_scraper import KinoppyScraper
from src.scraping.reader_store_scraper import ReaderStoreScraper

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


async def test_new_sites():
    """新実装サイトのテスト"""
    
    # テスト書籍（新書籍含む）
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
    
    print("=== Kinoppy & Reader Store テスト ===")
    print(f"開始時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("対象: 新実装2サイト（ebookjapan継承パターン）")
    print(f"テスト書籍: {len(test_books)}冊")
    print()
    
    # 新実装スクレイパー設定
    scrapers = [
        (KinoppyScraper, "Kinoppy", "✨ 紀伊國屋書店（ebookjapan継承）"),
        (ReaderStoreScraper, "Reader Store", "✨ Sony（ebookjapan継承）")
    ]
    
    all_results = {}
    
    # 各スクレイパーのテスト実行
    for scraper_class, scraper_name, description in scrapers:
        print(f"\n{'='*60}")
        print(f"📋 {scraper_name}: {description}")
        
        results = []
        
        try:
            scraper = scraper_class(timeout=15, max_retries=2)
            
            async with scraper:
                for i, book in enumerate(test_books, 1):
                    print(f"\n📚 テスト {i}/{len(test_books)}: {book['title']}")
                    print(f"   説明: {book['description']}")
                    
                    start_time = datetime.now()
                    
                    try:
                        url = await scraper.search_book(book['title'], book['n_code'])
                        
                        end_time = datetime.now()
                        processing_time = (end_time - start_time).total_seconds()
                        
                        result = {
                            'n_code': book['n_code'],
                            'title': book['title'],
                            'description': book['description'],
                            'url': url,
                            'success': url is not None,
                            'processing_time': processing_time,
                            'timestamp': end_time.isoformat()
                        }
                        
                        if url:
                            print(f"   ✅ 成功: {url}")
                            print(f"   ⏱️  処理時間: {processing_time:.1f}秒")
                        else:
                            print(f"   ❌ 見つからず")
                            print(f"   ⏱️  処理時間: {processing_time:.1f}秒")
                        
                        results.append(result)
                        
                    except Exception as e:
                        end_time = datetime.now()
                        processing_time = (end_time - start_time).total_seconds()
                        
                        result = {
                            'n_code': book['n_code'],
                            'title': book['title'],
                            'description': book['description'],
                            'url': None,
                            'success': False,
                            'error': str(e),
                            'processing_time': processing_time,
                            'timestamp': end_time.isoformat()
                        }
                        
                        print(f"   💥 エラー: {str(e)}")
                        print(f"   ⏱️  処理時間: {processing_time:.1f}秒")
                        results.append(result)
                    
                    # 書籍間待機
                    if i < len(test_books):
                        await asyncio.sleep(2)
            
            all_results[scraper_name] = results
            
            # サイト別サマリー
            successful = [r for r in results if r['success']]
            success_rate = (len(successful) / len(results)) * 100 if results else 0
            avg_time = sum(r['processing_time'] for r in results) / len(results) if results else 0
            
            print(f"\n📊 {scraper_name} 結果:")
            print(f"  成功: {len(successful)}/{len(results)} ({success_rate:.1f}%)")
            print(f"  平均時間: {avg_time:.1f}秒")
            
            # スクレイパー統計
            stats = scraper.get_stats()
            print(f"  検索パターン: {stats.get('search_pattern', 'N/A')}")
            print(f"  継承元: {stats.get('success_pattern', 'N/A')}")
            
        except Exception as e:
            logger.error(f"{scraper_name} 初期化エラー: {e}")
            print(f"💥 {scraper_name} 初期化エラー: {e}")
            all_results[scraper_name] = []
        
        # サイト間待機
        await asyncio.sleep(3)
    
    # 総合結果
    print(f"\n{'='*60}")
    print("🎯 新実装サイト総合結果")
    print(f"{'='*60}")
    
    total_tests = sum(len(results) for results in all_results.values())
    total_successes = sum(len([r for r in results if r['success']]) 
                         for results in all_results.values())
    overall_success_rate = (total_successes / total_tests * 100) if total_tests > 0 else 0
    
    print(f"総合成績: {total_successes}/{total_tests} ({overall_success_rate:.1f}%)")
    print(f"テスト書籍: {len(test_books)}冊 × {len(scrapers)}サイト")
    print()
    print("📊 サイト別詳細:")
    
    for scraper_name, results in all_results.items():
        if results:
            successful = [r for r in results if r['success']]
            success_rate = (len(successful) / len(results)) * 100
            avg_time = sum(r['processing_time'] for r in results) / len(results)
            
            if success_rate == 100.0:
                emoji = "🥇"
                status = "Perfect!"
            elif success_rate >= 80.0:
                emoji = "🥈"
                status = "Excellent"
            elif success_rate >= 60.0:
                emoji = "🥉"
                status = "Good"
            else:
                emoji = "🤔"
                status = "Need Fix"
            
            print(f"  {emoji} {scraper_name:15}: {len(successful)}/{len(results)} ({success_rate:5.1f}%) {avg_time:4.1f}s - {status}")
        else:
            print(f"  💥 {scraper_name:15}: 初期化失敗")
    
    # ebookjapan継承効果分析
    print(f"\n🔬 ebookjapan継承効果分析:")
    print(f"  継承元: ebookjapan 100%")
    
    if all_results:
        inheritance_rates = []
        for scraper_name, results in all_results.items():
            if results:
                successful = [r for r in results if r['success']]
                rate = (len(successful) / len(results)) * 100
                inheritance_rates.append(rate)
                print(f"  {scraper_name}: {rate:.1f}%")
        
        if inheritance_rates:
            avg_inheritance = sum(inheritance_rates) / len(inheritance_rates)
            print(f"  継承サイト平均: {avg_inheritance:.1f}%")
            print(f"  継承効果: {'+' if avg_inheritance >= 80 else '-'}{abs(avg_inheritance - 100):.1f}%")
    
    # 成功・失敗詳細
    for scraper_name, results in all_results.items():
        if not results:
            continue
        
        successful = [r for r in results if r['success']]
        failed = [r for r in results if not r['success']]
        
        if successful:
            print(f"\n✅ {scraper_name} 成功ケース:")
            for result in successful:
                print(f"  - {result['title']}: {result['url']}")
        
        if failed:
            print(f"\n❌ {scraper_name} 失敗ケース:")
            for result in failed:
                error = result.get('error', '見つからず')
                print(f"  - {result['title']}: {error}")
    
    # 提案
    print(f"\n💡 Phase 3 への提案:")
    if overall_success_rate >= 80:
        print(f"  🎉 継承戦略成功！全サイト80%以上達成")
        print(f"  📋 次: Amazon POD実装 + 最終統合テスト")
    else:
        problem_sites = [name for name, results in all_results.items() 
                        if results and (len([r for r in results if r['success']]) / len(results) * 100) < 80]
        if problem_sites:
            print(f"  🔧 要改善: {', '.join(problem_sites)}")
            print(f"  📋 対策: セレクタ調整、URL検証強化")
    
    print(f"\n=== Kinoppy & Reader Store テスト完了 ===")
    return all_results


async def main():
    """メイン処理"""
    try:
        await test_new_sites()
        
    except KeyboardInterrupt:
        print("\n⚠️ テストが中断されました")
    except Exception as e:
        logger.error(f"テストエラー: {e}")
        print(f"💥 予期しないエラー: {e}")


if __name__ == "__main__":
    asyncio.run(main())
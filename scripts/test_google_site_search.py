#!/usr/bin/env python3
"""
Google Site Search スクレイパーテスト
Kinoppy & Reader Store攻略最終手段
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime
import logging

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.scraping.google_site_search_scraper import KinoppyGoogleScraper, ReaderStoreGoogleScraper

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


async def test_google_site_search():
    """Google Site Search スクレイパーテスト"""
    
    # テスト書籍
    test_books = [
        {
            'n_code': 'N0000TEST',
            'title': 'ソードアート・オンライン1',
            'description': '人気シリーズ・基本形（Google検索で確実にヒット）'
        },
        {
            'n_code': 'N02402',
            'title': 'クソゲー悪役令嬢①新装版',
            'description': '実際のなろう作品（シート未設定）'
        }
    ]
    
    print("=== Google Site Search スクレイパーテスト ===")
    print(f"開始時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("対象: Kinoppy & Reader Store（Google経由攻略）")
    print(f"テスト書籍: {len(test_books)}冊")
    print()
    
    # Google Site Searchスクレイパー設定
    scrapers = [
        (KinoppyGoogleScraper, "Kinoppy Google", "🔍 紀伊國屋（Google Site Search）"),
        (ReaderStoreGoogleScraper, "Reader Store Google", "🔍 Sony（Google Site Search）")
    ]
    
    all_results = {}
    
    # 各スクレイパーのテスト実行
    for scraper_class, scraper_name, description in scrapers:
        print(f"\n{'='*60}")
        print(f"📋 {scraper_name}: {description}")
        
        results = []
        
        try:
            scraper = scraper_class(timeout=20, max_retries=2)
            
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
                    
                    # 書籍間待機（Google負荷軽減）
                    if i < len(test_books):
                        await asyncio.sleep(3)
            
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
            print(f"  検索方式: {stats.get('search_method', 'N/A')}")
            print(f"  対象サイト: {stats.get('target_site', 'N/A')}")
            
        except Exception as e:
            logger.error(f"{scraper_name} 初期化エラー: {e}")
            print(f"💥 {scraper_name} 初期化エラー: {e}")
            all_results[scraper_name] = []
        
        # サイト間待機（Google負荷軽減）
        await asyncio.sleep(5)
    
    # 総合結果
    print(f"\n{'='*60}")
    print("🎯 Google Site Search 総合結果")
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
            
            if success_rate >= 50.0:
                emoji = "🥇"
                status = "Google突破成功！"
            elif success_rate > 0:
                emoji = "🥈"
                status = "部分成功"
            else:
                emoji = "🤔"
                status = "Google制限？"
            
            print(f"  {emoji} {scraper_name:20}: {len(successful)}/{len(results)} ({success_rate:5.1f}%) {avg_time:4.1f}s - {status}")
        else:
            print(f"  💥 {scraper_name:20}: 初期化失敗")
    
    # Google Site Search効果分析
    print(f"\n🔬 Google Site Search効果分析:")
    print(f"  従来手法: Requests + BeautifulSoup 0%")
    print(f"  Google経由: {overall_success_rate:.1f}%")
    
    if overall_success_rate > 0:
        print(f"  🎉 Google Site Search効果: +{overall_success_rate:.1f}%の改善！")
        print(f"  💡 間接アプローチによる困難サイト攻略成功")
    else:
        print(f"  🤔 Google制限またはサイト構造の問題")
        print(f"  📋 次段階: より高度な手法（API解析、ヘッドレスブラウザ）")
    
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
    
    print(f"\n=== Google Site Search テスト完了 ===")
    return all_results


async def main():
    """メイン処理"""
    try:
        await test_google_site_search()
        
    except KeyboardInterrupt:
        print("\n⚠️ テストが中断されました")
    except Exception as e:
        logger.error(f"テストエラー: {e}")
        print(f"💥 予期しないエラー: {e}")


if __name__ == "__main__":
    asyncio.run(main())
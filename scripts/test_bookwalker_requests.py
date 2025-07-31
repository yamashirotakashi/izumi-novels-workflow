#!/usr/bin/env python3
"""
BOOK☆WALKER Requestsスクレイパーテストスクリプト
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

from src.scraping.bookwalker_requests_scraper import BookWalkerRequestsScraper

# ログ設定
logging.basicConfig(
    level=logging.DEBUG,  # DEBUGレベルに変更
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/bookwalker_requests_test.log')
    ]
)
logger = logging.getLogger(__name__)


async def test_bookwalker_requests():
    """BOOK☆WALKER Requestsスクレイパーのテスト実行"""
    
    # テストデータ
    test_books = [
        {
            'n_code': 'N0230FK',
            'title': 'パラレイドデイズ④',
            'description': 'KADOKAWA系ライトノベル（丸数字巻数）'
        },
        {
            'n_code': 'N7975EJ',
            'title': 'エアボーンウイッチ④',
            'description': 'KADOKAWA系ライトノベル（丸数字巻数）'
        },
        {
            'n_code': 'N0000TEST',
            'title': 'ソードアート・オンライン1',
            'description': '人気シリーズ（数字巻数）'
        }
    ]
    
    print("=== BOOK☆WALKER Requestsスクレイパーテスト開始 ===")
    print(f"テスト開始時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"テスト対象: {len(test_books)}冊")
    print()
    
    # スクレイパー初期化
    scraper = BookWalkerRequestsScraper(
        timeout=10,
        max_retries=2
    )
    
    results = []
    
    try:
        async with scraper:
            for i, book in enumerate(test_books, 1):
                print(f"📚 テスト {i}/{len(test_books)}: {book['title']}")
                print(f"   説明: {book['description']}")
                
                start_time = datetime.now()
                
                try:
                    # 書籍検索実行
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
                
                print()
                
                # 書籍間の待機（レート制限対応）
                if i < len(test_books):
                    await asyncio.sleep(2)
    
    except Exception as e:
        logger.error(f"スクレイパー初期化エラー: {e}")
        print(f"💥 スクレイパー初期化エラー: {e}")
        return
    
    # 結果サマリー
    print("=== テスト結果サマリー ===")
    
    successful_results = [r for r in results if r['success']]
    failed_results = [r for r in results if not r['success']]
    
    success_rate = (len(successful_results) / len(results)) * 100 if results else 0
    avg_processing_time = sum(r['processing_time'] for r in results) / len(results) if results else 0
    
    print(f"総実行数: {len(results)}")
    print(f"成功: {len(successful_results)}件")
    print(f"失敗: {len(failed_results)}件")
    print(f"成功率: {success_rate:.1f}%")
    print(f"平均処理時間: {avg_processing_time:.1f}秒")
    
    # スクレイパー統計
    stats = scraper.get_stats()
    print(f"\nスクレイパー統計:")
    print(f"  検索回数: {stats.get('total_searches', 0)}")
    print(f"  成功回数: {stats.get('successful_searches', 0)}")
    print(f"  リクエスト数: {stats.get('requests_made', 0)}")
    print(f"  平均レスポンス時間: {stats.get('avg_response_time', 'N/A')}")
    print(f"  スクレイパータイプ: {stats.get('scraper_type', 'Unknown')}")
    
    # 詳細結果の保存
    results_data = {
        'test_info': {
            'scraper': 'BookWalkerRequestsScraper',
            'test_date': datetime.now().isoformat(),
            'total_tests': len(results),
            'success_count': len(successful_results),
            'failure_count': len(failed_results),
            'success_rate': success_rate,
            'average_processing_time': avg_processing_time
        },
        'results': results,
        'scraper_stats': stats
    }
    
    # 結果をJSONファイルに保存
    output_file = f"logs/bookwalker_requests_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n📄 詳細結果を保存: {output_file}")
    
    # 失敗ケースの詳細表示
    if failed_results:
        print(f"\n❌ 失敗ケース詳細:")
        for result in failed_results:
            print(f"  - {result['title']}")
            if 'error' in result:
                print(f"    エラー: {result['error']}")
    
    print(f"\n=== BOOK☆WALKER Requestsスクレイパーテスト完了 ===")
    return results


async def test_title_normalization():
    """タイトル正規化のテスト"""
    print("\n=== タイトル正規化テスト（Requests版） ===")
    
    scraper = BookWalkerRequestsScraper()
    
    test_titles = [
        "パラレイドデイズ④",
        "ソードアート・オンライン１",
        "この素晴らしい世界に祝福を！",
        "BOOK☆WALKER限定版",
        "魔法科高校の劣等生　第1巻",
        "Re:ゼロから始める異世界生活（１）",
        "【期間限定】特典付き版"
    ]
    
    for title in test_titles:
        normalized = scraper.normalize_title(title)
        variants = scraper._create_bookwalker_title_variants(title)
        volume = scraper.extract_volume_number(title)
        
        print(f"原題: {title}")
        print(f"正規化: {normalized}")
        print(f"巻数: {volume}")
        print(f"バリエーション: {variants[:3]}")  # 上位3つを表示
        print()


async def main():
    """メイン処理"""
    # ログディレクトリ作成
    Path('logs').mkdir(exist_ok=True)
    
    try:
        # タイトル正規化テスト
        await test_title_normalization()
        
        # Requestsスクレイパーテスト
        await test_bookwalker_requests()
        
    except KeyboardInterrupt:
        print("\n⚠️ テストが中断されました")
    except Exception as e:
        logger.error(f"テストエラー: {e}")
        print(f"💥 予期しないエラー: {e}")


if __name__ == "__main__":
    asyncio.run(main())
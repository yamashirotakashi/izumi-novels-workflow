#!/usr/bin/env python3
"""
honto スクレイパーテストスクリプト
ebookjapan成功パターン継承の検証
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

from src.scraping.honto_scraper import HontoScraper

# ログ設定
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/honto_test.log')
    ]
)
logger = logging.getLogger(__name__)


async def test_honto():
    """honto スクレイパーのテスト実行"""
    
    # テストデータ（ebookjapan成功パターンと同一）
    test_books = [
        {
            'n_code': 'N0000TEST',
            'title': 'ソードアート・オンライン1',
            'description': '人気シリーズ・基本形'
        },
        {
            'n_code': 'N0000TEST2',
            'title': '転生したらスライムだった件1',
            'description': '人気なろう系'
        },
        {
            'n_code': 'N0230FK',
            'title': 'パラレイドデイズ④',
            'description': 'KADOKAWA系ライトノベル（丸数字巻数）'
        }
    ]
    
    print("=== honto スクレイパーテスト開始 ===")
    print(f"テスト開始時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"テスト対象: {len(test_books)}冊")
    print("戦略: ebookjapan 100%成功パターンの継承")
    print("注目: コンテナベースのa[href*=\"/ebook/\"]セレクタ使用")
    print()
    
    # スクレイパー初期化
    scraper = HontoScraper(
        timeout=15,
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
                    # honto URL検索実行
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
                
                # 書籍間の待機（サイト負荷軽減）
                if i < len(test_books):
                    await asyncio.sleep(2)
    
    except Exception as e:
        logger.error(f"スクレイパー初期化エラー: {e}")
        print(f"💥 スクレイパー初期化エラー: {e}")
        return
    
    # 結果サマリー
    print("=== honto テスト結果サマリー ===")
    
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
    print(f"\nhonto スクレイパー統計:")
    print(f"  検索回数: {stats.get('total_searches', 0)}")
    print(f"  成功回数: {stats.get('successful_searches', 0)}")
    print(f"  リクエスト数: {stats.get('requests_made', 0)}")
    print(f"  検索パターン: {stats.get('search_pattern', 'N/A')}")
    print(f"  継承元: {stats.get('success_pattern', 'N/A')}")
    
    # 詳細結果の保存
    results_data = {
        'test_info': {
            'scraper': 'HontoScraper',
            'test_date': datetime.now().isoformat(),
            'total_tests': len(results),
            'success_count': len(successful_results),
            'failure_count': len(failed_results),
            'success_rate': success_rate,
            'average_processing_time': avg_processing_time,
            'pattern_inheritance': 'ebookjapan 100%成功パターン',
            'improvements': [
                'ebookjapanコンテナパターン継承',
                'a[href*="/ebook/"]セレクタ使用',
                '多段階検索戦略',
                'シリーズ名抽出機能'
            ]
        },
        'results': results,
        'scraper_stats': stats
    }
    
    # 結果をJSONファイルに保存
    output_file = f"logs/honto_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n📄 詳細結果を保存: {output_file}")
    
    # 成功ケースの詳細表示
    if successful_results:
        print(f"\n✅ 成功ケース詳細:")
        for result in successful_results:
            print(f"  - {result['title']}")
            print(f"    URL: {result['url']}")
    
    # 失敗ケースの詳細表示
    if failed_results:
        print(f"\n❌ 失敗ケース詳細:")
        for result in failed_results:
            print(f"  - {result['title']}")
            if 'error' in result:
                print(f"    エラー: {result['error']}")
    
    # 他サイトとの比較
    print(f"\n📊 他サイトとの比較:")
    print(f"  ebookjapan: 成功率 100.0% (3/3) ← 継承元")
    print(f"  BOOK☆WALKER: 成功率 66.7% (2/3)")
    print(f"  BookLive: 成功率 66.7% (2/3)")
    print(f"  Apple Books: 成功率 100.0% (4/4)")
    print(f"  honto（今回）: 成功率 {success_rate:.1f}% ({len(successful_results)}/{len(results)})")
    
    if success_rate >= 80.0:
        print(f"  🎉 excellent! ebookjapanパターン継承成功")
    elif success_rate >= 60.0:
        print(f"  📈 良好な結果、調整でさらなる向上期待")
    else:
        print(f"  🤔 セレクタ調整またはサイト構造再調査が必要")
    
    print(f"\n=== honto テスト完了 ===")
    return results


async def main():
    """メイン処理"""
    # ログディレクトリ作成
    Path('logs').mkdir(exist_ok=True)
    
    try:
        await test_honto()
        
    except KeyboardInterrupt:
        print("\n⚠️ テストが中断されました")
    except Exception as e:
        logger.error(f"テストエラー: {e}")
        print(f"💥 予期しないエラー: {e}")


if __name__ == "__main__":
    asyncio.run(main())
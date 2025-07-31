#!/usr/bin/env python3
"""
ebookjapan スクレイパーテストスクリプト
BOOK☆WALKERの成功技術を適用
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

from src.scraping.ebookjapan_scraper import EbookjapanScraper

# ログ設定
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/ebookjapan_test.log')
    ]
)
logger = logging.getLogger(__name__)


async def test_ebookjapan():
    """ebookjapan スクレイパーのテスト実行"""
    
    # テストデータ（同じケースで比較）
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
    
    print("=== ebookjapan スクレイパーテスト開始 ===")
    print(f"テスト開始時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"テスト対象: {len(test_books)}冊")
    print("技術: BOOK☆WALKER成功パターンを適用したコンテナベース抽出")
    print()
    
    # スクレイパー初期化
    scraper = EbookjapanScraper(
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
    print("=== ebookjapanテスト結果サマリー ===")
    
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
    print(f"\nebookjapanスクレイパー統計:")
    print(f"  検索回数: {stats.get('total_searches', 0)}")
    print(f"  成功回数: {stats.get('successful_searches', 0)}")
    print(f"  リクエスト数: {stats.get('requests_made', 0)}")
    print(f"  平均レスポンス時間: {stats.get('avg_response_time', 'N/A')}")
    print(f"  スクレイパータイプ: {stats.get('scraper_type', 'Unknown')}")
    
    # 詳細結果の保存
    results_data = {
        'test_info': {
            'scraper': 'EbookjapanScraper',
            'test_date': datetime.now().isoformat(),
            'total_tests': len(results),
            'success_count': len(successful_results),
            'failure_count': len(failed_results),
            'success_rate': success_rate,
            'average_processing_time': avg_processing_time,
            'improvements': [
                'BOOK☆WALKER成功技術の適用',
                'コンテナベース抽出実装',
                'Yahoo!系サイト最適化ヘッダー',
                'keyword検索パラメータ使用'
            ]
        },
        'results': results,
        'scraper_stats': stats
    }
    
    # 結果をJSONファイルに保存
    output_file = f"logs/ebookjapan_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
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
    
    # BOOK☆WALKERとの比較
    print(f"\n📊 BOOK☆WALKERとの比較:")
    print(f"  BOOK☆WALKER（高度版）: 成功率 66.7% (2/3)")
    print(f"  ebookjapan（今回）: 成功率 {success_rate:.1f}% ({len(successful_results)}/{len(results)})")
    
    if success_rate >= 66.7:
        print(f"  🎉 同等以上の性能！")
    elif success_rate >= 33.3:
        print(f"  📈 まずまずの結果、改善の余地あり")
    else:
        print(f"  🤔 更なる改善が必要")
    
    print(f"\n=== ebookjapanテスト完了 ===")
    return results


async def test_container_extraction():
    """コンテナ抽出機能の単体テスト"""
    print("\n=== ebookjapanコンテナ抽出機能テスト ===")
    
    scraper = EbookjapanScraper()
    
    # パラレイドデイズで実際のHTML構造をテスト
    test_query = "パラレイドデイズ"
    
    async with scraper:
        try:
            soup = await scraper.make_request(scraper.SEARCH_URL, params={'keyword': test_query})
            if soup:
                print(f"検索結果を取得: {test_query}")
                
                # コンテナ発見テスト
                containers = scraper._find_book_containers(soup)
                print(f"発見したコンテナ数: {len(containers)}")
                
                # 上位5コンテナの詳細分析
                for i, container in enumerate(containers[:5], 1):
                    book_info = scraper._extract_book_info_from_container(container)
                    print(f"\nコンテナ {i}:")
                    if book_info:
                        print(f"  タイトル: {book_info.get('title', 'N/A')}")
                        print(f"  URL: {book_info.get('url', 'N/A')}")
                        print(f"  著者: {book_info.get('author', 'N/A')}")
                        
                        # スコア計算
                        if book_info.get('title'):
                            score = scraper.calculate_similarity_score(test_query, book_info['title'])
                            print(f"  類似度スコア: {score:.3f}")
                    else:
                        print(f"  情報抽出失敗")
            
        except Exception as e:
            print(f"コンテナ抽出テストエラー: {e}")


async def main():
    """メイン処理"""
    # ログディレクトリ作成
    Path('logs').mkdir(exist_ok=True)
    
    try:
        # コンテナ抽出機能テスト
        await test_container_extraction()
        
        # ebookjapanスクレイパーテスト
        await test_ebookjapan()
        
    except KeyboardInterrupt:
        print("\n⚠️ テストが中断されました")
    except Exception as e:
        logger.error(f"テストエラー: {e}")
        print(f"💥 予期しないエラー: {e}")


if __name__ == "__main__":
    asyncio.run(main())
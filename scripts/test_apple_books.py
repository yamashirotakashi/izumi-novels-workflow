#!/usr/bin/env python3
"""
Apple Books スクレイパーテストスクリプト
iTunes Search API ハイブリッド戦略
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

from src.scraping.apple_books_scraper import AppleBooksLinkGenerator

# ログ設定
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/apple_books_test.log')
    ]
)
logger = logging.getLogger(__name__)


async def test_apple_books():
    """Apple Books リンク生成器のテスト実行"""
    
    # テストデータ（ISBN含む、シートから取得できる情報を模擬）
    test_books = [
        {
            'n_code': 'N0230FK',
            'title': 'パラレイドデイズ④',
            'isbn': '9784040738222',  # 仮のISBN
            'description': 'KADOKAWA系ライトノベル（丸数字巻数、ISBN付き）'
        },
        {
            'n_code': 'N7975EJ',
            'title': 'エアボーンウイッチ④',
            'isbn': '9784040739151',  # 仮のISBN
            'description': 'KADOKAWA系ライトノベル（丸数字巻数、ISBN付き）'
        },
        {
            'n_code': 'N0000TEST',
            'title': 'ソードアート・オンライン1',
            'isbn': '9784048671811',  # SAO実際のISBN
            'description': '人気シリーズ（実際のISBN使用）'
        },
        {
            'n_code': 'N0000TEST2',
            'title': '転生したらスライムだった件1',
            'isbn': '',  # ISBNなしケース
            'description': 'ISBNなしタイトル検索テスト'
        }
    ]
    
    print("=== Apple Books リンク生成器テスト開始 ===")
    print(f"テスト開始時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"テスト対象: {len(test_books)}冊")
    print("技術: iTunes Search API主軸ハイブリッド戦略")
    print("特色: ISBN優先検索 + タイトルフォールバック")
    print()
    
    # リンク生成器初期化
    generator = AppleBooksLinkGenerator(
        timeout=20,
        max_retries=2
    )
    
    results = []
    
    try:
        async with generator:
            for i, book in enumerate(test_books, 1):
                print(f"📚 テスト {i}/{len(test_books)}: {book['title']}")
                print(f"   説明: {book['description']}")
                print(f"   ISBN: {book['isbn'] if book['isbn'] else 'なし'}")
                
                start_time = datetime.now()
                
                try:
                    # Apple Books URL生成実行
                    url = await generator.search_book(
                        book['title'], 
                        book['n_code'],
                        book['isbn']
                    )
                    
                    end_time = datetime.now()
                    processing_time = (end_time - start_time).total_seconds()
                    
                    result = {
                        'n_code': book['n_code'],
                        'title': book['title'],
                        'isbn': book['isbn'],
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
                        'isbn': book['isbn'],
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
                
                # 書籍間の待機（API制限対応）
                if i < len(test_books):
                    await asyncio.sleep(3)  # iTunes API制限配慮
    
    except Exception as e:
        logger.error(f"リンク生成器初期化エラー: {e}")
        print(f"💥 リンク生成器初期化エラー: {e}")
        return
    
    # 結果サマリー
    print("=== Apple Books テスト結果サマリー ===")
    
    successful_results = [r for r in results if r['success']]
    failed_results = [r for r in results if not r['success']]
    isbn_results = [r for r in results if r['isbn']]
    no_isbn_results = [r for r in results if not r['isbn']]
    
    success_rate = (len(successful_results) / len(results)) * 100 if results else 0
    avg_processing_time = sum(r['processing_time'] for r in results) / len(results) if results else 0
    
    print(f"総実行数: {len(results)}")
    print(f"成功: {len(successful_results)}件")
    print(f"失敗: {len(failed_results)}件")
    print(f"成功率: {success_rate:.1f}%")
    print(f"平均処理時間: {avg_processing_time:.1f}秒")
    
    # ISBN別統計
    isbn_success = len([r for r in isbn_results if r['success']])
    no_isbn_success = len([r for r in no_isbn_results if r['success']])
    
    print(f"\nISBN別統計:")
    print(f"  ISBN有り: {isbn_success}/{len(isbn_results)} ({(isbn_success/len(isbn_results)*100) if isbn_results else 0:.1f}%)")
    print(f"  ISBN無し: {no_isbn_success}/{len(no_isbn_results)} ({(no_isbn_success/len(no_isbn_results)*100) if no_isbn_results else 0:.1f}%)")
    
    # 生成器統計
    stats = generator.get_stats()
    print(f"\nApple Books生成器統計:")
    print(f"  検索回数: {stats.get('total_searches', 0)}")
    print(f"  成功回数: {stats.get('successful_searches', 0)}")
    print(f"  キャッシュサイズ: {stats.get('cache_size', 0)}")
    print(f"  API端点: {stats.get('api_endpoint', 'N/A')}")
    print(f"  検索方式: {stats.get('search_method', 'N/A')}")
    
    # 詳細結果の保存
    results_data = {
        'test_info': {
            'scraper': 'AppleBooksLinkGenerator',
            'test_date': datetime.now().isoformat(),
            'total_tests': len(results),
            'success_count': len(successful_results),
            'failure_count': len(failed_results),
            'success_rate': success_rate,
            'average_processing_time': avg_processing_time,
            'isbn_success_rate': (isbn_success/len(isbn_results)*100) if isbn_results else 0,
            'no_isbn_success_rate': (no_isbn_success/len(no_isbn_results)*100) if no_isbn_results else 0,
            'improvements': [
                'iTunes Search API主軸実装',
                'ISBN優先検索戦略',
                'タイトル検索フォールバック',
                'APIキャッシュ機能',
                '多段階マッチング戦略'
            ]
        },
        'results': results,
        'generator_stats': stats
    }
    
    # 結果をJSONファイルに保存
    output_file = f"logs/apple_books_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n📄 詳細結果を保存: {output_file}")
    
    # 成功ケースの詳細表示
    if successful_results:
        print(f"\n✅ 成功ケース詳細:")
        for result in successful_results:
            print(f"  - {result['title']}")
            print(f"    URL: {result['url']}")
            print(f"    ISBN: {result['isbn'] if result['isbn'] else 'なし'}")
    
    # 失敗ケースの詳細表示
    if failed_results:
        print(f"\n❌ 失敗ケース詳細:")
        for result in failed_results:
            print(f"  - {result['title']}")
            print(f"    ISBN: {result['isbn'] if result['isbn'] else 'なし'}")
            if 'error' in result:
                print(f"    エラー: {result['error']}")
    
    # 他サイトとの比較
    print(f"\n📊 他サイトとの比較:")
    print(f"  BOOK☆WALKER: 成功率 66.7% (2/3)")
    print(f"  ebookjapan: 成功率 100.0% (3/3)")
    print(f"  BookLive: 成功率 66.7% (2/3)")
    print(f"  Apple Books（今回）: 成功率 {success_rate:.1f}% ({len(successful_results)}/{len(results)})")
    
    if success_rate >= 75.0:
        print(f"  🎉 高性能！iTunes API戦略成功")
    elif success_rate >= 50.0:
        print(f"  📈 良好な結果、特殊サイトとして満足")
    else:
        print(f"  🤔 iTunes API調整が必要")
    
    print(f"\n=== Apple Books テスト完了 ===")
    return results


async def test_itunes_api_direct():
    """iTunes Search API 直接テスト"""
    print("\n=== iTunes Search API 直接テスト ===")
    
    generator = AppleBooksLinkGenerator()
    
    # 実在するISBNでテスト
    test_isbn = "9784048671811"  # ソードアート・オンライン1巻
    
    async with generator:
        try:
            result = await generator._search_by_itunes_api(test_isbn, search_type='isbn')
            if result:
                print(f"✅ iTunes API成功: {test_isbn}")
                print(f"   結果URL: {result}")
            else:
                print(f"❌ iTunes API失敗: {test_isbn}")
            
        except Exception as e:
            print(f"💥 iTunes API直接テストエラー: {e}")


async def main():
    """メイン処理"""
    # ログディレクトリ作成
    Path('logs').mkdir(exist_ok=True)
    
    try:
        # iTunes API直接テスト
        await test_itunes_api_direct()
        
        # Apple Books リンク生成器テスト
        await test_apple_books()
        
    except KeyboardInterrupt:
        print("\n⚠️ テストが中断されました")
    except Exception as e:
        logger.error(f"テストエラー: {e}")
        print(f"💥 予期しないエラー: {e}")


if __name__ == "__main__":
    asyncio.run(main())
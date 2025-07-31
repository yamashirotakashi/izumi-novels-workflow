#!/usr/bin/env python3
"""
Kinoppy Playwright版スクレイパーテスト
JavaScript対応・動的サイト攻略最終版
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime
import logging

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.scraping.kinoppy_playwright_scraper import KinoppyPlaywrightScraper

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


async def test_kinoppy_playwright():
    """Kinoppy Playwright版テスト"""
    
    # テスト書籍
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
        }
    ]
    
    print("=== Kinoppy Playwright版 テスト ===")
    print(f"開始時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("対象: JavaScript対応・動的サイト攻略")
    print(f"テスト書籍: {len(test_books)}冊")
    print()
    
    results = []
    
    try:
        # Playwright版スクレイパー起動
        async with KinoppyPlaywrightScraper(headless=True, timeout=20000) as scraper:
            
            for i, book in enumerate(test_books, 1):
                print(f"📚 テスト {i}/{len(test_books)}: {book['title']}")
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
                    await asyncio.sleep(3)
        
        # 結果サマリー
        print(f"\n{'='*60}")
        print("🎯 Kinoppy Playwright版 結果サマリー")
        print(f"{'='*60}")
        
        successful = [r for r in results if r['success']]
        success_rate = (len(successful) / len(results)) * 100 if results else 0
        avg_time = sum(r['processing_time'] for r in results) / len(results) if results else 0
        
        print(f"📚 テスト書籍: {len(test_books)}冊")
        print(f"🎯 総合成績: {len(successful)}/{len(results)} ({success_rate:.1f}%)")
        print(f"⚡ 平均時間: {avg_time:.1f}秒")
        print()
        
        # 詳細結果
        for result in results:
            if result['success']:
                emoji = "✅"
                status = f"{result['processing_time']:.1f}s"
            else:
                emoji = "❌"
                error = result.get('error', '見つからず')
                status = f"失敗: {error[:30]}... ({result['processing_time']:.1f}s)"
            
            print(f"  {emoji} {result['title'][:30]}...: {status}")
        
        # 成功詳細
        if successful:
            print(f"\n✅ 成功ケース:")
            for result in successful:
                print(f"  - {result['title']}: {result['url']}")
        
        # 評価
        print(f"\n📊 Playwright vs Requests比較:")
        print(f"  Requests版: 0% (全失敗)")
        print(f"  Playwright版: {success_rate:.1f}%")
        
        if success_rate > 0:
            print(f"  🎉 Playwright効果: +{success_rate:.1f}%の改善！")
            print(f"  🚀 JavaScript対応により動的サイト攻略成功")
        else:
            print(f"  🤔 さらなる深層分析が必要")
            print(f"  💡 次段階: DevTools解析、API逆解析検討")
        
        print(f"\n=== Kinoppy Playwright版 テスト完了 ===")
        return results
        
    except Exception as e:
        logger.error(f"テストエラー: {e}")
        print(f"💥 テスト実行エラー: {e}")
        return []


async def main():
    """メイン処理"""
    try:
        await test_kinoppy_playwright()
        
    except KeyboardInterrupt:
        print("\n⚠️ テストが中断されました")
    except Exception as e:
        logger.error(f"メインエラー: {e}")
        print(f"💥 予期しないエラー: {e}")


if __name__ == "__main__":
    asyncio.run(main())
#!/usr/bin/env python3
"""
新しい書籍「クソゲー悪役令嬢①新装版」での
3つの高速サイト（ebookjapan, honto, Apple Books）のクイックテスト
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
from src.scraping.honto_scraper import HontoScraper
from src.scraping.apple_books_scraper import AppleBooksLinkGenerator

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


async def test_new_book():
    """新書籍での高速サイトテスト"""
    
    # 新しい書籍情報
    test_book = {
        'n_code': 'N02402',
        'title': 'クソゲー悪役令嬢①新装版',
        'description': '実際のなろう作品（シート未設定）'
    }
    
    print("=== 新書籍クイックテスト ===")
    print(f"テスト書籍: {test_book['title']} ({test_book['n_code']})")
    print(f"開始時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("対象: 高速3サイト（ebookjapan, honto, Apple Books）")
    print()
    
    # 高速スクレイパー設定
    scrapers = [
        (EbookjapanScraper, "ebookjapan", "🥇 100%成功基準"),
        (HontoScraper, "honto", "✨ ebookjapan継承"),
        (AppleBooksLinkGenerator, "Apple Books", "🎯 iTunes API")
    ]
    
    results = {}
    
    # 各スクレイパーのテスト実行
    for scraper_class, scraper_name, description in scrapers:
        print(f"\n📋 {scraper_name}: {description}")
        
        start_time = datetime.now()
        
        try:
            # スクレイパー初期化（サイト別パラメータ）
            if scraper_name == "Apple Books":
                scraper = scraper_class(timeout=15, max_retries=2)
            else:
                scraper = scraper_class(timeout=15, max_retries=2)
            
            async with scraper:
                # Apple Books用特殊対応（ISBNなし）
                if scraper_name == "Apple Books":
                    url = await scraper.search_book(test_book['title'], test_book['n_code'], "")
                else:
                    url = await scraper.search_book(test_book['title'], test_book['n_code'])
                
                end_time = datetime.now()
                processing_time = (end_time - start_time).total_seconds()
                
                if url:
                    print(f"  ✅ 成功: {url}")
                    print(f"  ⏱️  処理時間: {processing_time:.1f}秒")
                    success = True
                else:
                    print(f"  ❌ 見つからず")
                    print(f"  ⏱️  処理時間: {processing_time:.1f}秒")
                    success = False
                
                results[scraper_name] = {
                    'url': url,
                    'success': success,
                    'processing_time': processing_time,
                    'timestamp': end_time.isoformat()
                }
                
        except Exception as e:
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            
            print(f"  💥 エラー: {str(e)}")
            print(f"  ⏱️  処理時間: {processing_time:.1f}秒")
            
            results[scraper_name] = {
                'url': None,
                'success': False,
                'error': str(e),
                'processing_time': processing_time,
                'timestamp': end_time.isoformat()
            }
        
        # サイト間待機
        await asyncio.sleep(2)
    
    # 結果サマリー
    print(f"\n{'='*60}")
    print("🎯 新書籍クイックテスト結果")
    print(f"{'='*60}")
    
    successful_sites = [name for name, result in results.items() if result['success']]
    failed_sites = [name for name, result in results.items() if not result['success']]
    
    overall_success_rate = len(successful_sites) / len(results) * 100
    avg_time = sum(r['processing_time'] for r in results.values()) / len(results)
    
    print(f"📚 書籍: {test_book['title']}")
    print(f"🎯 総合成績: {len(successful_sites)}/{len(results)} ({overall_success_rate:.1f}%)")
    print(f"⚡ 平均時間: {avg_time:.1f}秒")
    print()
    print("📊 サイト別結果:")
    
    for scraper_name, result in results.items():
        if result['success']:
            emoji = "✅"
            status = f"{result['processing_time']:.1f}s"
        else:
            emoji = "❌"
            status = f"失敗 ({result['processing_time']:.1f}s)"
        
        print(f"  {emoji} {scraper_name:15}: {status}")
    
    # 成功サイト詳細
    if successful_sites:
        print(f"\n✅ 成功サイト詳細:")
        for site in successful_sites:
            result = results[site]
            print(f"  - {site}: {result['url']}")
    
    # 失敗サイト詳細
    if failed_sites:
        print(f"\n❌ 失敗サイト詳細:")
        for site in failed_sites:
            result = results[site]
            error = result.get('error', '見つからず')
            print(f"  - {site}: {error}")
    
    # 期待値との比較
    print(f"\n📊 他書籍との比較:")
    print(f"  SAO, スライム: ebookjapan 100%, honto 100%, Apple Books 100%")
    print(f"  クソゲー悪役令嬢: ebookjapan {('100%' if 'ebookjapan' in successful_sites else '0%')}, honto {('100%' if 'honto' in successful_sites else '0%')}, Apple Books {('100%' if 'Apple Books' in successful_sites else '0%')}")
    
    if overall_success_rate >= 80:
        print(f"  🎉 Excellent! 高スコア達成")
    elif overall_success_rate >= 60:
        print(f"  📈 Good! 改善の余地あり")
    else:
        print(f"  🤔 要調査: 新書籍での検索精度課題")
    
    print(f"\n=== 新書籍クイックテスト完了 ===")
    return results


async def main():
    """メイン処理"""
    try:
        await test_new_book()
        
    except KeyboardInterrupt:
        print("\n⚠️ テストが中断されました")
    except Exception as e:
        logger.error(f"テストエラー: {e}")
        print(f"💥 予期しないエラー: {e}")


if __name__ == "__main__":
    asyncio.run(main())
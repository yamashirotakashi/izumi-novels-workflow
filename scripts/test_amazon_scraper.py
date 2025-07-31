#!/usr/bin/env python3
"""
Amazon Kindleスクレイパーのテストスクリプト
"""
import asyncio
import sys
import json
from pathlib import Path
import logging

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.scraping.amazon_kindle_scraper import AmazonKindleScraper

# ロガー設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_amazon_scraper():
    """Amazon Kindleスクレイパーのテスト"""
    
    # テストデータの読み込み
    test_data_path = project_root / 'config' / 'test_data.json'
    with open(test_data_path, 'r', encoding='utf-8') as f:
        test_data = json.load(f)
    
    test_books = test_data['test_books']
    
    print("=== Amazon Kindleスクレイパー テスト ===")
    print(f"テスト対象: {len(test_books)}冊")
    print()
    
    # スクレイパー設定
    screenshot_dir = project_root / 'logs' / 'screenshots'
    screenshot_dir.mkdir(parents=True, exist_ok=True)
    
    results = []
    
    async with AmazonKindleScraper(
        headless=False,  # 初回テストはブラウザ表示
        timeout=30000,
        screenshot_dir=screenshot_dir
    ) as scraper:
        
        for book in test_books:
            n_code = book['n_code']
            title = book['title']
            
            print(f"📖 検索中: {title} ({n_code})")
            
            try:
                # 検索実行
                url = await scraper.search_book(title, n_code)
                
                if url:
                    print(f"✅ 成功: {url}")
                    result = {
                        'n_code': n_code,
                        'title': title,
                        'status': 'success',
                        'url': url,
                        'error': None
                    }
                else:
                    print(f"❌ 失敗: URLが見つかりませんでした")
                    result = {
                        'n_code': n_code,
                        'title': title,
                        'status': 'not_found',
                        'url': None,
                        'error': 'No URL found'
                    }
                
                results.append(result)
                
            except Exception as e:
                print(f"💥 エラー: {e}")
                result = {
                    'n_code': n_code,
                    'title': title,
                    'status': 'error',
                    'url': None,
                    'error': str(e)
                }
                results.append(result)
            
            print()
            # 書籍間の待機
            await asyncio.sleep(3)
        
        # 統計情報の表示
        print("=== テスト結果サマリー ===")
        stats = scraper.get_search_stats()
        for key, value in stats.items():
            print(f"{key}: {value}")
        print()
        
        # 結果の詳細表示
        success_count = len([r for r in results if r['status'] == 'success'])
        not_found_count = len([r for r in results if r['status'] == 'not_found'])
        error_count = len([r for r in results if r['status'] == 'error'])
        
        print(f"成功: {success_count}件")
        print(f"見つからず: {not_found_count}件")
        print(f"エラー: {error_count}件")
        print(f"成功率: {(success_count / len(results)) * 100:.1f}%")
    
    # 結果をJSONファイルに保存
    results_path = project_root / 'logs' / 'amazon_test_results.json'
    results_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(results_path, 'w', encoding='utf-8') as f:
        json.dump({
            'test_results': results,
            'summary': {
                'total_books': len(results),
                'success_count': success_count,
                'not_found_count': not_found_count,
                'error_count': error_count,
                'success_rate': f"{(success_count / len(results)) * 100:.1f}%"
            },
            'scraper_stats': stats
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n結果をファイルに保存: {results_path}")
    
    return results


async def test_volume_variants():
    """巻数バリエーションのテスト"""
    print("=== 巻数バリエーション テスト ===")
    
    scraper = AmazonKindleScraper()
    
    test_titles = [
        "パラレイドデイズ④",
        "エアボーンウイッチ④"
    ]
    
    for title in test_titles:
        print(f"\n📚 タイトル: {title}")
        variants = scraper.create_volume_variants(title)
        
        for i, variant in enumerate(variants, 1):
            print(f"  {i}. {variant}")


async def main():
    """メイン処理"""
    print("Amazon Kindleスクレイパー テストツール")
    print("1. 巻数バリエーションテスト")
    print("2. 実際のスクレイピングテスト")
    print()
    
    choice = input("選択してください (1/2): ").strip()
    
    if choice == "1":
        await test_volume_variants()
    elif choice == "2":
        await test_amazon_scraper()
    else:
        print("無効な選択です")


if __name__ == "__main__":
    asyncio.run(main())
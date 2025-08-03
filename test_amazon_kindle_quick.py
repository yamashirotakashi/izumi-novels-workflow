#!/usr/bin/env python3
"""
Amazon Kindleスクレイパー クイックテスト - Chrome for Testing統合版
Amazon Kindle Scraper Quick Test - Chrome for Testing Integration
"""
import asyncio
import sys
from pathlib import Path

# プロジェクトルートを追加
project_root = Path(__file__).parent
sys.path.append(str(project_root / 'src'))

from scrapers.amazon_kindle_scraper import AmazonKindleScraper

async def quick_test():
    """クイックテスト実行"""
    print("🚀 Amazon Kindleスクレイパー クイックテスト開始")
    print("=" * 50)
    
    try:
        scraper = AmazonKindleScraper()
        
        # ブラウザセットアップ
        print("🌐 ブラウザセットアップ中...")
        await scraper.setup_browser(headless=True)
        
        # 簡単なテスト検索
        print("🔍 テスト検索実行...")
        result = await scraper.search_books("Python プログラミング")
        
        # 結果表示
        if result.success:
            print(f"✅ 検索成功: {len(result.books_found)}冊発見")
            print(f"⏱️ 実行時間: {result.execution_time:.2f}秒")
            
            # 最初の1冊の詳細表示
            if result.books_found:
                book = result.books_found[0]
                print(f"\n📚 サンプル書籍:")
                print(f"  タイトル: {book.title}")
                print(f"  価格: {book.price or '不明'}")
                print(f"  著者: {book.author or '不明'}")
                print(f"  URL: {book.url[:60]}...")
        else:
            print(f"❌ 検索失敗: {result.error_message}")
        
        # クリーンアップ
        await scraper.cleanup()
        
        print("\n🎉 クイックテスト完了")
        return result.success if result else False
        
    except Exception as e:
        print(f"❌ テストエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = asyncio.run(quick_test())
    print(f"\n📊 テスト結果: {'✅ 成功' if success else '❌ 失敗'}")
    sys.exit(0 if success else 1)
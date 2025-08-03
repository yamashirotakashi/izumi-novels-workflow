#!/usr/bin/env python3
"""
Amazon Kindle実動スクレイピングテスト
Amazon Kindle Production Scraping Test
"""
import sys
import time
from pathlib import Path

# プロジェクトルートを追加
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root / 'src'))

from scrapers.amazon_scraper import AmazonKindleScraper

def test_amazon_production():
    """Amazon Kindle実動テスト"""
    print("🚀 Amazon Kindle実動スクレイピングテスト開始")
    print("=" * 60)
    
    scraper = None
    try:
        # スクレイパー初期化
        scraper = AmazonKindleScraper()
        
        # テストクエリ
        test_queries = [
            "課長が目覚めたら異世界SF艦隊の提督になってた件です",
            "異世界転生",
            "小説"
        ]
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n📖 テスト{i}: '{query}'")
            print("-" * 40)
            
            # スクレイピング実行
            start_time = time.time()
            result = scraper.scrape_with_retry(query)
            execution_time = time.time() - start_time
            
            # 結果表示
            print(f"⏱️ 実行時間: {execution_time:.2f}秒")
            print(f"🎯 サイト: {result.site_name}")
            print(f"📊 成功: {'✅' if result.success else '❌'}")
            print(f"📚 書籍数: {len(result.books_found)}件")
            print(f"🔄 リトライ: {result.retry_count}回")
            
            if result.error_message:
                print(f"❌ エラー: {result.error_message}")
            
            # 書籍詳細表示（最大3件）
            if result.books_found:
                print(f"\n📋 書籍詳細 (上位{min(3, len(result.books_found))}件):")
                for j, book in enumerate(result.books_found[:3], 1):
                    print(f"  {j}. {book.title}")
                    print(f"     URL: {book.url}")
                    if book.price:
                        print(f"     価格: {book.price}")
                    if book.author:
                        print(f"     著者: {book.author}")
                    print()
            
            # 結果検証
            is_valid = scraper.validate_result(result)
            print(f"✅ 検証結果: {'合格' if is_valid else '不合格'}")
            
            # テスト間の待機
            if i < len(test_queries):
                print(f"\n⏳ 次のテストまで3秒待機...")
                time.sleep(3)
        
        print(f"\n🎉 Amazon Kindle実動テスト完了")
        return True
        
    except Exception as e:
        print(f"❌ テスト実行エラー: {e}")
        return False
        
    finally:
        if scraper:
            scraper.cleanup()

def main():
    """メイン実行"""
    print("Amazon Kindle Production Scraper Test")
    print("=" * 60)
    
    success = test_amazon_production()
    
    print("\n" + "=" * 60)
    print(f"🏁 テスト結果: {'✅ 成功' if success else '❌ 失敗'}")
    
    # 終了コード設定
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
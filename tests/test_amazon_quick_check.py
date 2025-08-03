#!/usr/bin/env python3
"""
Amazon Kindle高速チェックテスト
Quick check test for Amazon Kindle scraper
"""
import sys
from pathlib import Path

# プロジェクトルートを追加
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root / 'src'))

def test_amazon_import():
    """Amazon Kindleスクレイパーインポートテスト"""
    try:
        print("🔍 Amazon Kindleスクレイパーモジュールテスト")
        
        # インポートテスト
        from scrapers.amazon_scraper import AmazonKindleScraper
        from scrapers.base_scraper import BaseScraper, BookInfo, ScrapingResult
        
        print("✅ モジュールインポート成功")
        
        # インスタンス化テスト
        scraper = AmazonKindleScraper()
        print(f"✅ スクレイパー初期化成功: {scraper.site_name}")
        
        # 設定確認
        print(f"📋 ベースURL: {scraper.base_url}")
        print(f"📋 検索URL: {scraper.search_url}")
        print(f"📋 セレクタ数: {len(scraper.selectors)}個")
        
        # セレクタ詳細表示
        if scraper.selectors:
            print("\n🔍 設定セレクタ:")
            for key, value in scraper.selectors.items():
                count = len(value) if isinstance(value, list) else 1
                print(f"  {key}: {count}個")
        
        print("\n✅ Amazon Kindleスクレイパー基本チェック完了")
        return True
        
    except Exception as e:
        print(f"❌ テストエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """メイン実行"""
    print("Amazon Kindle Scraper Quick Check")
    print("=" * 50)
    
    success = test_amazon_import()
    
    print("\n" + "=" * 50)
    print(f"🏁 結果: {'✅ 成功' if success else '❌ 失敗'}")
    
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
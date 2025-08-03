#!/usr/bin/env python3
"""
Amazon Kindle設定テスト（WebDriverなし）
Configuration-only test for Amazon Kindle scraper
"""
import sys
from pathlib import Path

# プロジェクトルートを追加
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root / 'src'))

def test_amazon_configuration():
    """Amazon Kindle設定テスト"""
    print("🔍 Amazon Kindle設定テスト開始")
    print("=" * 50)
    
    try:
        # インポートテスト
        from scrapers.amazon_scraper import AmazonKindleScraper
        from scrapers.base_scraper import BaseScraper, BookInfo, ScrapingResult
        
        print("✅ モジュールインポート成功")
        
        # インスタンス化テスト
        scraper = AmazonKindleScraper()
        print(f"✅ スクレイパー初期化成功: {scraper.site_name}")
        
        # 設定確認
        print(f"📋 サイトID: {scraper.site_id}")
        print(f"📋 ベースURL: {scraper.base_url}")
        print(f"📋 検索URL: {scraper.search_url}")
        print(f"📋 セレクタ数: {len(scraper.selectors)}個")
        
        # セレクタ詳細表示
        if scraper.selectors:
            print("\n🔍 設定セレクタ:")
            for key, value in scraper.selectors.items():
                count = len(value) if isinstance(value, list) else 1
                print(f"  {key}: {count}個")
                if isinstance(value, list) and value:
                    print(f"    例: {value[0]}")
        
        # 設定値チェック
        required_configs = ['base_url', 'search_url', 'selectors']
        missing_configs = [config for config in required_configs 
                          if not getattr(scraper, config.replace('_url', '_url' if '_url' in config else config))]
        
        if missing_configs:
            print(f"⚠️ 不足している設定: {missing_configs}")
            return False
        
        # 必須セレクタチェック  
        required_selectors = ['search_input', 'search_results', 'book_title', 'book_link']
        missing_selectors = [sel for sel in required_selectors if sel not in scraper.selectors]
        
        if missing_selectors:
            print(f"⚠️ 不足しているセレクタ: {missing_selectors}")
            return False
        
        print("\n✅ Amazon Kindle設定テスト完了")
        print("📊 設定状態: EXCELLENT")
        return True
        
    except Exception as e:
        print(f"❌ テストエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """メイン実行"""
    print("Amazon Kindle Configuration Test")
    print("=" * 50)
    
    success = test_amazon_configuration()
    
    print("\n" + "=" * 50)
    if success:
        print("🏁 結果: ✅ 設定テスト成功")
        print("💡 注意: WebDriver接続テストは別途実行が必要")
    else:
        print("🏁 結果: ❌ 設定テスト失敗")
    
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
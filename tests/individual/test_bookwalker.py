#!/usr/bin/env python3
"""
BOOK☆WALKER 個別テスト
Individual Test for BOOK☆WALKER
"""
import sys
import asyncio
from pathlib import Path

# プロジェクトルートを追加
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root / 'src'))

from core.flexible_scraper import FlexibleScraper

class BookWalkerIndividualTest:
    """BOOK☆WALKER 専用テストクラス"""
    
    def __init__(self):
        self.scraper = FlexibleScraper()
        self.site_id = "bookwalker"
        self.site_name = "BOOK☆WALKER"
        self.test_query = "課長が目覚めたら異世界SF艦隊の提督になってた件です"
    
    async def run_test(self):
        """BOOK☆WALKER テスト実行"""
        print(f"🚀 {self.site_name} 個別テスト開始")
        print("=" * 50)
        
        try:
            # WebDriverセットアップ
            print("🔧 Chrome WebDriver設定中...")
            self.scraper.setup_driver()
            
            # サイト存在確認
            available_sites = self.scraper.get_available_sites()
            if self.site_id not in available_sites:
                print(f"❌ {self.site_name} の設定が見つかりません")
                return self._create_error_result("設定なし")
            
            print(f"✅ {self.site_name} 設定確認完了")
            print(f"🎯 検索クエリ: '{self.test_query}'")
            print("-" * 50)
            
            # 検索実行
            result = self.scraper.search_site(self.site_id, self.test_query)
            
            # 結果表示
            self._display_result(result)
            return result
            
        except Exception as e:
            print(f"❌ {self.site_name} テストエラー: {e}")
            return self._create_error_result(str(e))
        
        finally:
            self.scraper.cleanup()
    
    def _display_result(self, result):
        """結果表示"""
        status_icon = "✅" if result.status == "SUCCESS" else (
            "⚠️" if result.status == "NO_RESULTS" else "❌"
        )
        
        print(f"{status_icon} {result.site} テスト結果:")
        print(f"   ステータス: {result.status}")
        print(f"   検索結果数: {result.results_count}件")
        print(f"   URL: {result.url}")
        
        if result.books_found:
            print(f"   発見書籍:")
            for i, book in enumerate(result.books_found[:3], 1):
                title = book.get('title', 'タイトル不明')[:50]
                print(f"     {i}. {title}")
        
        if result.error_message:
            print(f"   エラー: {result.error_message}")
        
        # 判定
        if result.status == "SUCCESS":
            print("🎉 判定: 成功 - 検索結果を正常取得")
        elif result.status == "NO_RESULTS":
            print("⚠️ 判定: 部分成功 - 検索実行したが結果なし")
        else:
            print("❌ 判定: 失敗 - エラーまたは検索失敗")
    
    def _create_error_result(self, error_message):
        """エラー結果作成"""
        from core.flexible_scraper import SearchResult
        return SearchResult(
            site=self.site_name,
            query=self.test_query,
            results_count=0,
            status="ERROR",
            url="",
            error_message=error_message
        )

async def main():
    """メイン実行"""
    test = BookWalkerIndividualTest()
    result = await test.run_test()
    
    print("\n" + "=" * 50)
    print(f"🏁 {test.site_name} 個別テスト完了")
    
    # 終了コード設定
    if result.status == "SUCCESS":
        sys.exit(0)  # 成功
    elif result.status == "NO_RESULTS":
        sys.exit(1)  # 部分成功
    else:
        sys.exit(2)  # 失敗

if __name__ == '__main__':
    asyncio.run(main())
#!/usr/bin/env python3
"""
Amazon Kindle  items別test
Individual Test for Amazon Kindle
"""
import sys
import asyncio
from pathlib import Path

# プロジェクトルートを追加
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root / 'src'))

from core.flexible_scraper import FlexibleScraper

class AmazonIndividualTest:
    """Amazon Kindle 専用testクラス"""
    
    def __init__(self):
        self.scraper = FlexibleScraper()
        self.site_id = "amazon"
        self.site_name = "Amazon Kindle"
        self.test_query = "課長が目覚めたら異世界SF艦隊の提督になってた件です"
    
    async def run_test(self):
        """Amazon Kindle test実行"""
        print(f"🚀 {self.site_name}  items別test開始")
        print("=" * 50)
        
        try:
            # WebDriverセットアップ
            print("🔧 Chrome WebDriver設定中...")
            self.scraper.setup_driver()
            
            # サイト存在確認
            available_sites = self.scraper.get_available_sites()
            if self.site_id not in available_sites:
                print(f"[FAIL] {self.site_name} config not found")
                return self._create_error_result("設定None")
            
            print(f"[OK] {self.site_name} Config Check完了")
            print(f"[TARGET] 検索クエリ: '{self.test_query}'")
            print("-" * 50)
            
            # 検索実行
            result = self.scraper.search_site(self.site_id, self.test_query)
            
            # 結果表示
            self._display_result(result)
            return result
            
        except Exception as e:
            print(f"[FAIL] {self.site_name} testエラー: {e}")
            return self._create_error_result(str(e))
        
        finally:
            self.scraper.cleanup()
    
    def _display_result(self, result):
        """結果表示"""
        status_icon = "[OK]" if result.status == "SUCCESS" else (
            "[WARN]" if result.status == "NO_RESULTS" else "[FAIL]"
        )
        
        print(f"{status_icon} {result.site} Test Results:")
        print(f"   ステータス: {result.status}")
        print(f"   検索結果数: {result.results_count}件")
        print(f"   URL: {result.url}")
        
        if result.books_found:
            print(f"   発見書籍:")
            for i, book in enumerate(result.books_found[:3], 1):
                title = book.get('title', 'タイトルUnknown')[:50]
                print(f"     {i}. {title}")
        
        if result.error_message:
            print(f"   エラー: {result.error_message}")
        
        # 判定
        if result.status == "SUCCESS":
            print("[RESULT] Result: 成功 - 検索結果を正常取得")
        elif result.status == "NO_RESULTS":
            print("[WARN] Result: 部分成功 - 検索実行したが結果None")
        else:
            print("[FAIL] Result: 失敗 - エラーまたは検索失敗")
    
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
    """Main Execution"""
    test = AmazonIndividualTest()
    result = await test.run_test()
    
    print("\n" + "=" * 50)
    print(f"[FINISH] {test.site_name}  items別test完了")
    
    # Set exit code
    if result.status == "SUCCESS":
        sys.exit(0)  # 成功
    elif result.status == "NO_RESULTS":
        sys.exit(1)  # 部分成功
    else:
        sys.exit(2)  # 失敗

if __name__ == '__main__':
    asyncio.run(main())
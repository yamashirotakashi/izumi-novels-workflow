#!/usr/bin/env python3
"""
改良された類似度スコア計算のテスト
"""
import sys
import os

# パス追加
sys.path.append('/mnt/c/Users/tky99/DEV/izumi-novels-workflow/src')

from scraping.selenium_base_scraper import SeleniumBaseScraper

class TestScraper(SeleniumBaseScraper):
    async def _search_impl(self, book_title: str, n_code: str):
        return None
    async def _verify_url(self, url: str, expected_title: str):
        return True

def test_improved_similarity():
    """改良された類似度スコア計算のテスト"""
    scraper = TestScraper()
    
    print("🧪 改良された類似度スコア計算テスト")
    print("="*50)
    
    # テストケース（Phase 1検証で失敗したケースを含む）
    test_cases = [
        # 高類似度（期待値: ≥0.8）
        ("課長が目覚めたら異世界SF艦隊の提督になってた件です①", "課長が目覚めたら異世界SF艦隊の提督になってた件です 1", 0.8),
        
        # 中高類似度（期待値: ≥0.7）
        ("課長が目覚めたら異世界SF艦隊の提督になってた件です①", "課長が目覚めたら異世界SF艦隊の提督になってた件です", 0.7),
        
        # 中類似度（期待値: ≥0.3）
        ("課長が目覚めたら異世界SF艦隊の提督になってた件です①", "異世界転生RPG物語", 0.3),
        
        # 低類似度（期待値: ≥0.1）
        ("課長が目覚めたら異世界SF艦隊の提督になってた件です①", "全く関係ない本", 0.1),
        
        # 部分マッチテスト
        ("異世界ファンタジー", "異世界ファンタジー小説集", 0.5),
        ("プログラミング入門", "Python プログラミング入門", 0.4),
        
        # 単語共通性テスト
        ("魔法使いの冒険", "冒険者と魔法使い", 0.4),
        ("デザインパターン", "パターン設計手法", 0.3),
    ]
    
    results = []
    passed = 0
    total = len(test_cases)
    
    for i, (query, title, expected_min) in enumerate(test_cases, 1):
        score = scraper.calculate_similarity_score(query, title)
        is_pass = score >= expected_min
        
        status = "✅ PASS" if is_pass else "❌ FAIL"
        
        print(f"{i:2d}. {status}")
        print(f"    クエリ: '{query}'")
        print(f"    タイトル: '{title}'")
        print(f"    スコア: {score:.4f} (期待: ≥{expected_min})")
        print()
        
        if is_pass:
            passed += 1
        
        results.append({
            'query': query,
            'title': title,
            'score': score,
            'expected_min': expected_min,
            'pass': is_pass
        })
    
    # 結果サマリー
    print("="*50)
    print(f"📊 テスト結果サマリー")
    print(f"合格: {passed}/{total} ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 すべてのテストが合格しました！")
    else:
        print("⚠️  一部のテストが失敗しました。")
        print("\n失敗したテスト:")
        for i, result in enumerate(results, 1):
            if not result['pass']:
                print(f"  {i}. スコア {result['score']:.4f} < {result['expected_min']} (期待)")
    
    return passed == total

if __name__ == '__main__':
    success = test_improved_similarity()
    exit(0 if success else 1)
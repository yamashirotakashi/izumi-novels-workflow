#!/usr/bin/env python3
"""
類似度計算のデバッグ用ツール
"""
import sys
import os
sys.path.append('/mnt/c/Users/tky99/DEV/izumi-novels-workflow/src')

from scraping.selenium_base_scraper import SeleniumBaseScraper

class DebugScraper(SeleniumBaseScraper):
    async def _search_impl(self, book_title: str, n_code: str):
        return None
    async def _verify_url(self, url: str, expected_title: str):
        return True
    
    def debug_similarity_score(self, query: str, title: str) -> float:
        """類似度スコア計算のデバッグ版（改良版キーワード抽出対応）"""
        print(f"\n🔍 デバッグ: '{query}' vs '{title}'")
        
        # 正規化
        query_norm = self.normalize_title(query)
        title_norm = self.normalize_title(title)
        print(f"  正規化後: '{query_norm}' vs '{title_norm}'")
        
        # 完全一致
        if query_norm == title_norm:
            print("  → 完全一致: 1.0")
            return 1.0
        
        # 部分一致（クエリがタイトルに含まれる）
        if query_norm in title_norm:
            print("  → 部分一致（クエリ in タイトル）: 0.9")
            return 0.9
        
        # 逆方向の部分一致（タイトルがクエリに含まれる）
        if title_norm in query_norm:
            print("  → 逆部分一致（タイトル in クエリ）: 0.85")
            return 0.85
        
        # キーワード抽出による類似度計算
        query_keywords = self._extract_keywords(query_norm)
        title_keywords = self._extract_keywords(title_norm)
        print(f"  クエリキーワード: {query_keywords}")
        print(f"  タイトルキーワード: {title_keywords}")
        
        # キーワードレベルの類似度計算
        if query_keywords and title_keywords:
            # 共通キーワード
            common_keywords = query_keywords.intersection(title_keywords)
            total_keywords = query_keywords.union(title_keywords)
            
            if common_keywords:
                # Jaccard係数
                jaccard = len(common_keywords) / len(total_keywords)
                
                # 共通キーワード比率
                common_ratio = len(common_keywords) / min(len(query_keywords), len(title_keywords))
                
                print(f"  共通キーワード: {common_keywords}")
                print(f"  Jaccard係数: {jaccard:.4f}")
                print(f"  共通キーワード比率: {common_ratio:.4f}")
                
                # 高い類似度の場合
                if jaccard >= 0.3 or common_ratio >= 0.5:
                    result = max(0.6, min(0.9, jaccard * 1.5 + common_ratio * 0.5))
                    print(f"  → キーワード類似度（高）: {result:.4f}")
                    return result
                
                # 中程度の類似度の場合
                elif jaccard >= 0.15 or common_ratio >= 0.3:
                    result = max(0.4, min(0.7, jaccard * 1.8 + common_ratio * 0.6))
                    print(f"  → キーワード類似度（中）: {result:.4f}")
                    return result
                
                # 低い類似度でも共通点がある場合
                else:
                    result = max(0.25, min(0.5, jaccard * 2.0 + common_ratio * 0.8))
                    print(f"  → キーワード類似度（低）: {result:.4f}")
                    return result
        
        # 単語レベルでの類似度計算（英語等の場合）
        query_words = set(query_norm.split())
        title_words = set(title_norm.split())
        print(f"  クエリ単語: {query_words}")
        print(f"  タイトル単語: {title_words}")
        
        if query_words and title_words and len(query_words) > 1 and len(title_words) > 1:
            # Jaccard係数（共通単語/全単語）
            common_words = query_words.intersection(title_words)
            total_words = query_words.union(title_words)
            jaccard = len(common_words) / len(total_words) if total_words else 0
            
            # 共通単語の重みを考慮した類似度
            common_ratio = len(common_words) / min(len(query_words), len(title_words)) if min(len(query_words), len(title_words)) > 0 else 0
            
            print(f"  共通単語: {common_words}")
            print(f"  Jaccard係数: {jaccard:.4f}")
            print(f"  共通単語比率: {common_ratio:.4f}")
            
            # 単語レベルの類似度計算（改良版）
            if jaccard > 0.15:  # 閾値を下げる
                word_similarity = max(jaccard * 1.2, common_ratio * 0.8)
                result = max(0.3, min(0.8, word_similarity))
                print(f"  → 単語類似度（高）: {result:.4f}")
                return result
            elif common_words:  # 何らかの共通単語がある場合
                result = max(0.25, jaccard * 1.5)
                print(f"  → 単語類似度（低）: {result:.4f}")
                return result
        
        # 編集距離による類似度計算（改良版）
        import editdistance
        max_len = max(len(query_norm), len(title_norm))
        if max_len == 0:
            return 0.0
        
        distance = editdistance.eval(query_norm, title_norm)
        print(f"  編集距離: {distance}, 最大長: {max_len}")
        
        # 長い文字列の場合は編集距離の影響を軽減
        if max_len > 20:
            # 長い文字列では相対的な類似度を重視
            similarity = 1 - (distance / max_len)
            # 最低スコアを0.15に設定（完全に無関係でも少しは残る）
            result = max(0.15, similarity)
            print(f"  → 編集距離（長）: {result:.4f}")
            return result
        else:
            # 短い文字列では編集距離をそのまま利用
            similarity = 1 - (distance / max_len)
            result = max(0.0, similarity)
            print(f"  → 編集距離（短）: {result:.4f}")
            return result

def debug_failed_cases():
    """失敗したケースのデバッグ"""
    scraper = DebugScraper()
    
    print("🐛 失敗したケースのデバッグ分析")
    print("="*60)
    
    failed_cases = [
        ("課長が目覚めたら異世界SF艦隊の提督になってた件です①", "異世界転生RPG物語", 0.3),
        ("魔法使いの冒険", "冒険者と魔法使い", 0.4),
        ("デザインパターン", "パターン設計手法", 0.3),
    ]
    
    for i, (query, title, expected) in enumerate(failed_cases, 1):
        print(f"\n【ケース {i}】期待値: ≥{expected}")
        score = scraper.debug_similarity_score(query, title)
        status = "✅ PASS" if score >= expected else "❌ FAIL"
        print(f"  最終スコア: {score:.4f} {status}")

if __name__ == '__main__':
    debug_failed_cases()
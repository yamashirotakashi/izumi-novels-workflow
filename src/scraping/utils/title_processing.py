"""
Title Processing Utility Module

Consolidated title processing functions for all scrapers.
Eliminates code duplication across base classes and provides
framework-agnostic title normalization and matching capabilities.

Phase 1.6A: Strategic consolidation targeting 300+ line elimination.
"""
import re
import unicodedata
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)


class TitleProcessor:
    """
    Framework-agnostic title processing utility.
    
    Consolidates all title processing functionality from base classes
    to eliminate duplication and provide a single source of truth.
    """
    
    @staticmethod
    def normalize_title(title: str) -> str:
        """
        タイトルの正規化
        
        全角・半角統一、記号除去、スペース正規化など
        NFKC正規化により丸数字は通常の数字に変換される
        
        Args:
            title: 正規化対象のタイトル
            
        Returns:
            正規化されたタイトル
        """
        if not title:
            return ""
            
        # Unicode正規化（丸数字④→4に変換など）
        title = unicodedata.normalize('NFKC', title)
        
        # 記号の除去
        title = re.sub(r'[【】\[\]（）\(\)「」『』《》〈〉]', '', title)
        
        # 連続するスペースを単一スペースに
        title = re.sub(r'\s+', ' ', title)
        
        # 前後の空白を除去
        title = title.strip()
        
        return title.lower()
    
    @staticmethod  
    def is_title_match(expected: str, actual: str, threshold: float = 0.85) -> bool:
        """
        タイトルのマッチング判定
        
        Args:
            expected: 期待されるタイトル
            actual: 実際のタイトル
            threshold: 類似度の閾値（0-1）
            
        Returns:
            マッチするかどうか
        """
        # 正規化
        expected_norm = TitleProcessor.normalize_title(expected)
        actual_norm = TitleProcessor.normalize_title(actual)
        
        # 完全一致
        if expected_norm == actual_norm:
            return True
        
        # 部分一致（期待タイトルが実際のタイトルに含まれる）
        if expected_norm in actual_norm:
            return True
        
        # 編集距離による類似度計算（純Python実装）
        max_len = max(len(expected_norm), len(actual_norm))
        if max_len == 0:
            return False
        
        distance = TitleProcessor._levenshtein_distance(expected_norm, actual_norm)
        similarity = 1 - (distance / max_len)
        
        return similarity >= threshold
    
    @staticmethod
    def _levenshtein_distance(s1: str, s2: str) -> int:
        """
        レーベンシュタイン距離の純Python実装
        
        Args:
            s1: 文字列1
            s2: 文字列2
            
        Returns:
            編集距離
        """
        if len(s1) < len(s2):
            return TitleProcessor._levenshtein_distance(s2, s1)
        
        if len(s2) == 0:
            return len(s1)
        
        previous_row = list(range(len(s2) + 1))
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]
    
    @staticmethod
    def extract_volume_number(title: str) -> Optional[int]:
        """
        タイトルから巻数を抽出
        
        Args:
            title: タイトル文字列
            
        Returns:
            巻数（抽出できない場合はNone）
        """
        if not title:
            return None
            
        patterns = [
            r'第(\d+)巻',
            r'(\d+)巻',
            r'[①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳]',
            r'[\(（](\d+)[\)）]',
            r'vol\.?\s*(\d+)',
            r'volume\s*(\d+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, title, re.IGNORECASE)
            if match:
                # 丸数字の変換
                if pattern == r'[①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳]':
                    circled_nums = '①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳'
                    num_char = match.group(0)
                    try:
                        return circled_nums.index(num_char) + 1
                    except ValueError:
                        logger.warning(f"Unknown circled number: {num_char}")
                        return None
                else:
                    return int(match.group(1))
        
        return None
    
    @staticmethod
    def normalize_volume_notation(title: str, target_format: str = 'circled') -> str:
        """
        巻数表記を統一形式に変換
        
        Args:
            title: 変換対象のタイトル
            target_format: 'circled'（④）, 'arabic'（4）, 'kanji'（第4巻）, 'paren'（(4)）
            
        Returns:
            統一形式に変換されたタイトル
        """
        if not title:
            return ""
            
        volume = TitleProcessor.extract_volume_number(title)
        if volume is None:
            return title
        
        # 現在の巻数表記を除去
        cleaned_title = re.sub(r'[①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳]', '', title)
        cleaned_title = re.sub(r'第?\d+巻', '', cleaned_title)
        cleaned_title = re.sub(r'[\(（]\d+[\)）]', '', cleaned_title)
        cleaned_title = re.sub(r'\s*\d+\s*$', '', cleaned_title)  # 末尾の数字
        cleaned_title = re.sub(r'vol\.?\s*\d+', '', cleaned_title, flags=re.IGNORECASE)
        cleaned_title = re.sub(r'volume\s*\d+', '', cleaned_title, flags=re.IGNORECASE)
        cleaned_title = cleaned_title.strip()
        
        # 目的の形式に変換
        circled_nums = '①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳'
        
        if target_format == 'circled' and 1 <= volume <= 20:
            return f"{cleaned_title}{circled_nums[volume-1]}"
        elif target_format == 'arabic':
            return f"{cleaned_title} {volume}"
        elif target_format == 'kanji':
            return f"{cleaned_title} 第{volume}巻"
        elif target_format == 'paren':
            return f"{cleaned_title}({volume})"
        else:
            return title
    
    @staticmethod
    def create_volume_variants(title: str) -> List[str]:
        """
        タイトルの巻数表記バリエーションを生成
        
        Args:
            title: 元のタイトル
            
        Returns:
            異なる巻数表記のタイトルリスト
        """
        if not title:
            return []
            
        volume = TitleProcessor.extract_volume_number(title)
        if volume is None:
            return [title]
        
        variants = []
        formats = ['circled', 'arabic', 'kanji', 'paren']
        
        for fmt in formats:
            variant = TitleProcessor.normalize_volume_notation(title, fmt)
            if variant not in variants:
                variants.append(variant)
        
        # 追加のバリエーション
        cleaned_title = re.sub(r'[①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳]', '', title)
        cleaned_title = re.sub(r'第?\d+巻', '', cleaned_title)
        cleaned_title = re.sub(r'[\(（]\d+[\)）]', '', cleaned_title)
        cleaned_title = re.sub(r'\s*\d+\s*$', '', cleaned_title)
        cleaned_title = cleaned_title.strip()
        
        # スペースなしバージョン
        variants.append(f"{cleaned_title}{volume}")
        
        # 全角数字バージョン
        zenkaku_nums = '０１２３４５６７８９'
        if 0 <= volume <= 9:
            variants.append(f"{cleaned_title}{zenkaku_nums[volume]}")
        
        return list(dict.fromkeys(variants))  # 重複除去

# Create common directory structure by adding files
# This will be moved to src/scraping/common/ structure


class JapaneseTitleProcessor(TitleProcessor):
    """
    Japanese-specific title processing enhancements.
    
    Optimized for Japanese light novels and web novels.
    """
    
    @staticmethod
    def normalize_japanese_title(title: str) -> str:
        """
        日本語小説向け特化正規化
        
        Args:
            title: 日本語タイトル
            
        Returns:
            正規化されたタイトル
        """
        if not title:
            return ""
        
        # 基本正規化
        normalized = TitleProcessor.normalize_title(title)
        
        # 日本語特有の処理
        # 1. ひらがな・カタカナの統一化（オプション）
        # 2. 長音記号の統一
        normalized = re.sub(r'[ー−―‐]', 'ー', normalized)
        
        # 3. 全角英数字を半角英数字に統一
        normalized = JapaneseTitleProcessor._zenkaku_to_hankaku(normalized)
        
        return normalized
    
    @staticmethod
    def _zenkaku_to_hankaku(text: str) -> str:
        """
        全角英数字を半角に変換
        
        Args:
            text: 変換対象テキスト
            
        Returns:
            半角英数字に変換されたテキスト
        """
        if not text:
            return ""
        
        # 全角英数字の変換テーブル
        zenkaku = "０１２３４５６７８９ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚ"
        hankaku = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
        
        for z, h in zip(zenkaku, hankaku):
            text = text.replace(z, h)
        
        return text
    
    @staticmethod
    def extract_genre_keywords(title: str) -> List[str]:
        """
        タイトルからジャンルキーワードを抽出
        
        Args:
            title: タイトル文字列
            
        Returns:
            抽出されたキーワードリスト
        """
        if not title:
            return []
        
        # 小説ジャンルの典型的なキーワード
        genre_patterns = [
            r'異世界', r'転生', r'転移', r'魔法', r'魔王', r'勇者',
            r'冒険', r'ファンタジー', r'SF', r'学園', r'恋愛',
            r'ハーレム', r'チート', r'最強', r'無双', r'スキル',
            r'レベル', r'ステータス', r'ゲーム', r'VRMMO', r'RPG',
            r'艦隊', r'提督', r'課長', r'サラリーマン', r'社畜'
        ]
        
        keywords = []
        for pattern in genre_patterns:
            if re.search(pattern, title):
                keywords.append(pattern)
        
        return keywords


# Convenience functions for backward compatibility
def normalize_title(title: str) -> str:
    """Convenience function - delegates to TitleProcessor.normalize_title"""
    return TitleProcessor.normalize_title(title)


class SearchStrategies:
    """
    Common search strategy patterns used across scrapers.
    
    Consolidates search query generation and strategy patterns
    to eliminate duplication while allowing site-specific customizations.
    """
    
    @staticmethod
    def generate_basic_queries(title: str, max_queries: int = 4) -> List[str]:
        """
        Generate basic search queries for a book title.
        
        Args:
            title: Book title to search for
            max_queries: Maximum number of queries to generate
            
        Returns:
            List of search query strings
        """
        queries = []
        
        if not title:
            return queries
            
        # Basic normalized query
        base_title = TitleProcessor.normalize_title(title)
        queries.append(base_title)
        
        # Partial search for long titles
        if len(base_title) > 10:
            words = base_title.split()
            if len(words) >= 2:
                main_part = ' '.join(words[:2])
                queries.append(main_part)
        
        # Volume variants
        volume_variants = TitleProcessor.create_volume_variants(title)
        for variant in volume_variants[:2]:  # Top 2 variants
            if variant not in queries:
                queries.append(variant)
        
        # Series name only (without volume numbers)
        series_name = SearchStrategies._extract_series_name(title)
        if series_name != title and len(series_name) > 5:
            queries.append(series_name)
        
        return queries[:max_queries]
    
    @staticmethod 
    def generate_site_queries(title: str, site_domain: str, max_queries: int = 4) -> List[str]:
        """
        Generate site-specific search queries using site: operator.
        
        Args:
            title: Book title to search for
            site_domain: Target site domain (e.g., 'bookwalker.jp')
            max_queries: Maximum number of queries to generate
            
        Returns:
            List of site-specific search query strings 
        """
        basic_queries = SearchStrategies.generate_basic_queries(title, max_queries)
        return [f'site:{site_domain} "{query}"' for query in basic_queries]
    
    @staticmethod
    def generate_author_combined_queries(title: str, author: str, max_queries: int = 3) -> List[str]:
        """
        Generate queries combining title and author.
        
        Args:
            title: Book title
            author: Author name
            max_queries: Maximum number of queries to generate
            
        Returns:
            List of title+author combined queries
        """
        queries = []
        
        if not title or not author:
            return queries
            
        base_queries = SearchStrategies.generate_basic_queries(title, max_queries)
        
        for query in base_queries:
            combined = f"{query} {author}"
            queries.append(combined)
            
        return queries
    
    @staticmethod
    def _extract_series_name(title: str) -> str:
        """Extract series name by removing volume indicators."""
        if not title:
            return ""
            
        # Remove volume patterns
        patterns = [
            r'[①-⑳]',                      # Circled numbers  
            r'第\d+巻',                   # 第X巻
            r'\d+巻',                     # X巻
            r'\(\d+\)',                 # (X)
            r'[上中下]',                   # 上中下
            r'前編|後編|完結編',            # 前編|後編|完結編
            r'【[^】]*】',                  # 【】内
            r'vol\.?\s*\d+',            # vol.X or volX
            r'volume\s*\d+',             # volume X
        ]
        
        series_name = title
        for pattern in patterns:
            series_name = re.sub(pattern, '', series_name, flags=re.IGNORECASE).strip()
        
        return series_name if series_name else title


class URLValidators:
    """
    Common URL validation utilities used across scrapers.
    
    Provides standardized URL validation and format checking
    to eliminate duplicate validation logic.
    """
    
    @staticmethod
    def is_valid_book_url(url: str, expected_domain: str = None) -> bool:
        """
        Validate if URL appears to be a valid book URL.
        
        Args:
            url: URL to validate
            expected_domain: Expected domain (optional)
            
        Returns:
            True if URL appears valid for book content
        """
        if not url or not url.strip():
            return False
            
        # Basic URL format check
        if not (url.startswith('http://') or url.startswith('https://')):
            return False
            
        # Domain check if specified
        if expected_domain:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            if expected_domain not in parsed.netloc:
                return False
                
        # Common invalid patterns
        invalid_patterns = [
            'javascript:',
            'mailto:',
            '#',
            'void(0)',
        ]
        
        for pattern in invalid_patterns:
            if pattern in url.lower():
                return False
                
        return True
    
    @staticmethod
    def normalize_book_url(url: str, base_url: str = None) -> str:
        """
        Normalize and clean book URL.
        
        Args:
            url: URL to normalize
            base_url: Base URL for relative links
            
        Returns:
            Normalized absolute URL
        """
        if not url:
            return ""
            
        url = url.strip()
        
        # Convert relative to absolute
        if url.startswith('/') and base_url:
            url = base_url.rstrip('/') + url
        
        # Remove common tracking parameters
        tracking_params = ['utm_source', 'utm_medium', 'utm_campaign', 'ref', 'affiliate']
        
        from urllib.parse import urlparse, parse_qs, urlunparse, urlencode
        parsed = urlparse(url)
        query_params = parse_qs(parsed.query)
        
        # Filter out tracking parameters
        filtered_params = {k: v for k, v in query_params.items() 
                          if k not in tracking_params}
        
        # Rebuild query string
        new_query = urlencode(filtered_params, doseq=True)
        
        # Reconstruct URL
        new_parsed = parsed._replace(query=new_query)
        return urlunparse(new_parsed)
    
    @staticmethod 
    def extract_book_id_from_url(url: str, pattern: str = None) -> str:
        """
        Extract book ID from URL using pattern.
        
        Args:
            url: URL to extract ID from
            pattern: Regex pattern to extract ID (optional)
            
        Returns:
            Extracted book ID or empty string
        """
        if not url:
            return ""
            
        # Default patterns for common book sites
        if not pattern:
            patterns = [
                r'/book/(\d+)',           # /book/123456
                r'/product/(\d+)',        # /product/123456  
                r'/item/(\d+)',           # /item/123456
                r'id=(\d+)',              # ?id=123456
                r'/(\d+)/?$',             # /123456/ or /123456
            ]
        else:
            patterns = [pattern]
            
        for p in patterns:
            match = re.search(p, url)
            if match:
                return match.group(1)
                
        return ""


def is_title_match(expected: str, actual: str, threshold: float = 0.85) -> bool:
    """Convenience function - delegates to TitleProcessor.is_title_match"""
    return TitleProcessor.is_title_match(expected, actual, threshold)


def create_volume_variants(title: str) -> List[str]:
    """Convenience function - delegates to TitleProcessor.create_volume_variants"""
    return TitleProcessor.create_volume_variants(title)


def extract_volume_number(title: str) -> Optional[int]:
    """Convenience function - delegates to TitleProcessor.extract_volume_number"""
    return TitleProcessor.extract_volume_number(title)


def normalize_volume_notation(title: str, target_format: str = 'circled') -> str:
    """Convenience function - delegates to TitleProcessor.normalize_volume_notation"""
    return TitleProcessor.normalize_volume_notation(title, target_format)
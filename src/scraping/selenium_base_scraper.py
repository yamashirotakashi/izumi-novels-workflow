"""
Selenium用基盤スクレイパークラス
undetected-chromedriver対応
"""
import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
import re
import unicodedata
from urllib.parse import quote, urljoin
import json
from pathlib import Path
import editdistance

logger = logging.getLogger(__name__)


class ScrapingError(Exception):
    """スクレイピングエラーの基底クラス"""
    pass


class CaptchaError(ScrapingError):
    """CAPTCHA検出エラー"""
    pass


class RateLimitError(ScrapingError):
    """レート制限エラー"""
    pass


class NoResultError(ScrapingError):
    """検索結果なしエラー"""
    pass


class SeleniumBaseScraper(ABC):
    """
    Selenium用販売サイトスクレイパーの基底クラス
    
    undetected-chromedriver対応版
    """
    
    # サイト固有の設定（サブクラスでオーバーライド）
    SITE_NAME: str = "Unknown"
    BASE_URL: str = ""
    SEARCH_URL: str = ""
    USER_AGENT: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
    
    # デフォルト設定
    DEFAULT_TIMEOUT: int = 30  # 30秒
    DEFAULT_WAIT_TIME: int = 2  # 2秒
    MAX_RETRIES: int = 3
    RETRY_DELAY: int = 2  # 秒
    
    def __init__(self, 
                 headless: bool = True,
                 timeout: int = None,
                 screenshot_dir: Optional[Path] = None):
        """
        Args:
            headless: ヘッドレスモード
            timeout: タイムアウト時間（秒）
            screenshot_dir: スクリーンショット保存ディレクトリ
        """
        self.headless = headless
        self.timeout = timeout or self.DEFAULT_TIMEOUT
        self.screenshot_dir = screenshot_dir
        self.driver = None
        
        # 統計情報
        self.stats = {
            'total_searches': 0,
            'successful_searches': 0,
            'failed_searches': 0,
            'captcha_encounters': 0,
            'rate_limit_encounters': 0
        }
    
    async def search_book(self, book_title: str, n_code: str = "") -> Optional[str]:
        """
        書籍を検索してURLを取得
        
        Args:
            book_title: 書籍タイトル
            n_code: Nコード
            
        Returns:
            販売ページのURL（見つからない場合はNone）
        """
        self.stats['total_searches'] += 1
        
        for attempt in range(self.MAX_RETRIES):
            try:
                result = await self._try_search_with_retry(book_title, n_code, attempt)
                if result:
                    return result
                
            except Exception as e:
                await self._handle_search_error(e, book_title, n_code, attempt)
            
            # リトライ前の待機
            if attempt < self.MAX_RETRIES - 1:
                await asyncio.sleep(self.RETRY_DELAY)
        
        self.stats['failed_searches'] += 1
        logger.error(f"検索失敗（全試行終了）: {book_title} ({n_code})")
        return None
    
    async def _try_search_with_retry(self, book_title: str, n_code: str, attempt: int) -> Optional[str]:
        """単一試行での検索実行"""
        logger.info(f"検索開始: {book_title} ({n_code}) - 試行 {attempt + 1}/{self.MAX_RETRIES}")
        
        # 基本検索
        url = await self._search_impl(book_title, n_code)
        if url and await self._verify_url(url, book_title):
            self.stats['successful_searches'] += 1
            logger.info(f"検索成功: {book_title} -> {url}")
            return url
        elif url:
            logger.warning(f"URL検証失敗: {url}")
        
        # 代替検索
        url = await self._search_alternative(book_title, n_code)
        if url and await self._verify_url(url, book_title):
            self.stats['successful_searches'] += 1
            logger.info(f"代替検索成功: {book_title} -> {url}")
            return url
        
        return None
    
    async def _handle_search_error(self, error: Exception, book_title: str, n_code: str, attempt: int):
        """検索エラーのハンドリング"""
        if isinstance(error, CaptchaError):
            self.stats['captcha_encounters'] += 1
            logger.warning(f"CAPTCHA検出: {self.SITE_NAME}")
            await self._handle_captcha()
        elif isinstance(error, RateLimitError):
            self.stats['rate_limit_encounters'] += 1
            wait_time = self.RETRY_DELAY * (2 ** attempt)
            logger.warning(f"レート制限: {wait_time}秒待機")
            await asyncio.sleep(wait_time)
        else:
            logger.error(f"予期しないエラー: {error}", exc_info=True)
        
        raise error
    
    @abstractmethod
    async def _search_impl(self, book_title: str, n_code: str) -> Optional[str]:
        """
        サイト固有の検索実装
        
        サブクラスで実装必須
        """
        pass
    
    @abstractmethod
    async def _verify_url(self, url: str, expected_title: str) -> bool:
        """
        取得したURLの検証
        
        サブクラスで実装必須
        """
        pass
    
    async def _search_alternative(self, book_title: str, n_code: str) -> Optional[str]:
        """
        代替検索戦略（オプション）
        
        デフォルトではNoneを返す。必要に応じてサブクラスでオーバーライド
        """
        return None
    
    async def _handle_captcha(self):
        """
        CAPTCHA対応（オプション）
        
        デフォルトでは待機のみ。必要に応じてサブクラスでオーバーライド
        """
        logger.info("CAPTCHA待機中...")
        await asyncio.sleep(30)
    
    @staticmethod
    def normalize_title(title: str) -> str:
        """
        タイトルの正規化
        
        全角・半角統一、記号除去、スペース正規化など
        """
        # Unicode正規化
        title = unicodedata.normalize('NFKC', title)
        
        # 記号の除去
        title = re.sub(r'[【】\[\]（）\(\)「」『』《》〈〉]', '', title)
        
        # 連続するスペースを単一スペースに
        title = re.sub(r'\s+', ' ', title)
        
        # 前後の空白を除去
        title = title.strip()
        
        return title.lower()
    
    def _extract_keywords(self, text: str) -> set:
        """
        テキストからキーワードを抽出
        
        日本語テキストから意味のあるキーワードを抽出する
        """
        if not text:
            return set()
        
        # 基本的なキーワード抽出（文字ベース）
        keywords = set()
        
        # 英数字の単語
        import re
        english_words = re.findall(r'[a-zA-Z0-9]+', text)
        keywords.update(english_words)
        
        # 日本語のキーワード抽出（簡易版）
        # 一般的な日本語のパターンを抽出
        japanese_patterns = [
            r'異世界',
            r'転生',
            r'魔法',
            r'冒険',
            r'勇者',
            r'魔王',
            r'RPG',
            r'SF',
            r'艦隊',
            r'提督',
            r'課長',
            r'デザイン',
            r'パターン',
            r'設計',
            r'手法',
            r'入門',
            r'プログラミング',
            r'Python',
            r'ファンタジー',
            r'小説',
            r'物語',
            r'件',
            r'者',
            r'使い',
            r'目覚め',
            r'なって',
            r'って',
            r'た',
            r'です',
            r'の',
            r'と',
            r'が',
            r'に',
            r'を',
            r'は',
            r'で',
            r'から',
            r'まで'
        ]
        
        # 重要なキーワードのみを抽出（助詞などは除外）
        important_keywords = [
            '異世界', '転生', '魔法', '冒険', '勇者', '魔王', 'RPG', 'SF', 
            '艦隊', '提督', '課長', 'デザイン', 'パターン', '設計', '手法', 
            '入門', 'プログラミング', 'Python', 'ファンタジー', '小説', '物語'
        ]
        
        for keyword in important_keywords:
            if keyword in text:
                keywords.add(keyword)
        
        # 数字も重要なキーワードとして扱う
        numbers = re.findall(r'\d+', text)
        keywords.update(numbers)
        
        # 長い日本語文字列から意味のある部分を抽出（簡易版）
        # 3文字以上の連続した日本語文字
        japanese_segments = re.findall(r'[ぁ-んァ-ヶ一-龯]{3,10}', text)
        
        # より具体的なパターンマッチング
        specific_patterns = re.findall(r'課長|提督|魔法使い|冒険者|異世界|転生|RPG|SF|艦隊', text)
        keywords.update(specific_patterns)
        
        return keywords
    
    def calculate_similarity_score(self, query: str, title: str) -> float:
        """
        類似度スコア計算（改良版）
        
        Args:
            query: 検索クエリ
            title: 比較対象タイトル
            
        Returns:
            類似度スコア（0-1）
        """
        # 正規化
        query_norm = self.normalize_title(query)
        title_norm = self.normalize_title(title)
        
        # 完全一致
        if query_norm == title_norm:
            return 1.0
        
        # 部分一致（クエリがタイトルに含まれる）
        if query_norm in title_norm:
            return 0.9
        
        # 逆方向の部分一致（タイトルがクエリに含まれる）
        if title_norm in query_norm:
            return 0.85
        
        # 日本語テキストの場合はキーワード抽出による類似度計算
        query_keywords = self._extract_keywords(query_norm)
        title_keywords = self._extract_keywords(title_norm)
        
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
                
                # 高い類似度の場合
                if jaccard >= 0.3 or common_ratio >= 0.5:
                    return max(0.6, min(0.9, jaccard * 1.5 + common_ratio * 0.5))
                
                # 中程度の類似度の場合
                elif jaccard >= 0.15 or common_ratio >= 0.3:
                    return max(0.4, min(0.7, jaccard * 1.8 + common_ratio * 0.6))
                
                # 低い類似度でも共通点がある場合
                else:
                    return max(0.25, min(0.5, jaccard * 2.0 + common_ratio * 0.8))
        
        # 単語レベルでの類似度計算（英語等の場合）
        query_words = set(query_norm.split())
        title_words = set(title_norm.split())
        
        if query_words and title_words and len(query_words) > 1 and len(title_words) > 1:
            # Jaccard係数（共通単語/全単語）
            common_words = query_words.intersection(title_words)
            total_words = query_words.union(title_words)
            jaccard = len(common_words) / len(total_words) if total_words else 0
            
            # 共通単語の重みを考慮した類似度
            common_ratio = len(common_words) / min(len(query_words), len(title_words)) if min(len(query_words), len(title_words)) > 0 else 0
            
            # 単語レベルの類似度計算（改良版）
            if jaccard > 0.15:  # 閾値を下げる
                word_similarity = max(jaccard * 1.2, common_ratio * 0.8)
                return max(0.3, min(0.8, word_similarity))  # 0.3-0.8の範囲で返す
            elif common_words:  # 何らかの共通単語がある場合
                return max(0.25, jaccard * 1.5)  # 少しでも共通点があれば最低0.25
        
        # 編集距離による類似度計算（改良版）
        max_len = max(len(query_norm), len(title_norm))
        if max_len == 0:
            return 0.0
        
        distance = editdistance.eval(query_norm, title_norm)
        
        # 長い文字列の場合は編集距離の影響を軽減
        if max_len > 20:
            # 長い文字列では相対的な類似度を重視
            similarity = 1 - (distance / max_len)
            # 最低スコアを0.15に設定（完全に無関係でも少しは残る）
            return max(0.15, similarity)
        else:
            # 短い文字列では編集距離をそのまま利用
            similarity = 1 - (distance / max_len)
            return max(0.0, similarity)
    
    def is_title_match(self, expected: str, actual: str, threshold: float = 0.85) -> bool:
        """
        タイトルのマッチング判定
        
        Args:
            expected: 期待されるタイトル
            actual: 実際のタイトル
            threshold: 類似度の閾値（0-1）
            
        Returns:
            マッチするかどうか
        """
        return self.calculate_similarity_score(expected, actual) >= threshold
    
    def extract_volume_number(self, title: str) -> Optional[int]:
        """
        タイトルから巻数を抽出
        
        Returns:
            巻数（抽出できない場合はNone）
        """
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
    
    def create_volume_variants(self, title: str) -> List[str]:
        """
        タイトルの巻数表記バリエーションを生成
        
        Returns:
            異なる巻数表記のタイトルリスト
        """
        volume = self.extract_volume_number(title)
        if volume is None:
            return [title]
        
        variants = []
        
        # 基本クリーンアップ（巻数情報を除去）
        cleaned_title = re.sub(r'[①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳]', '', title)
        cleaned_title = re.sub(r'第?\d+巻', '', cleaned_title)
        cleaned_title = re.sub(r'[\(（]\d+[\)）]', '', cleaned_title)
        cleaned_title = re.sub(r'\s*\d+\s*$', '', cleaned_title)
        cleaned_title = cleaned_title.strip()
        
        # 各種バリエーション生成
        formats = {
            'circled': '①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳',
            'arabic': str(volume),
            'kanji': f'第{volume}巻',
            'paren': f'({volume})',
            'space': f' {volume}',
            'zenkaku': '０１２３４５６７８９'[volume] if 0 <= volume <= 9 else str(volume)
        }
        
        for fmt_name, fmt_value in formats.items():
            if fmt_name == 'circled' and 1 <= volume <= 20:
                variants.append(f"{cleaned_title}{fmt_value[volume-1]}")
            elif fmt_name == 'zenkaku':
                variants.append(f"{cleaned_title}{fmt_value}")
            else:
                variants.append(f"{cleaned_title}{fmt_value}")
        
        # 元のタイトルも含める
        variants.append(title)
        
        # 重複除去
        return list(dict.fromkeys(variants))
    
    def get_stats(self) -> Dict[str, Any]:
        """統計情報を取得"""
        success_rate = 0
        if self.stats['total_searches'] > 0:
            success_rate = (self.stats['successful_searches'] / 
                          self.stats['total_searches']) * 100
        
        return {
            **self.stats,
            'success_rate': f"{success_rate:.1f}%",
            'site_name': self.SITE_NAME
        }
    
    async def batch_search(self, books: List[Tuple[str, str]], 
                          delay_between: int = 2) -> Dict[str, Optional[str]]:
        """
        複数書籍の一括検索
        
        Args:
            books: (タイトル, Nコード)のリスト
            delay_between: 検索間の遅延（秒）
            
        Returns:
            {Nコード: URL}の辞書
        """
        results = {}
        
        for i, (title, n_code) in enumerate(books):
            if i > 0:
                await asyncio.sleep(delay_between)
            
            url = await self.search_book(title, n_code)
            results[n_code] = url
            
            # 進捗ログ
            logger.info(f"バッチ進捗: {i+1}/{len(books)} ({(i+1)/len(books)*100:.1f}%)")
        
        return results
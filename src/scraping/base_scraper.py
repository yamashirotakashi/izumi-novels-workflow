"""
基盤スクレイパークラス
すべての販売サイトスクレイパーの基底クラス
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

from playwright.async_api import Page, Browser, async_playwright, TimeoutError as PlaywrightTimeout

# Import unified title processing utility
from .utils.title_processing import TitleProcessor

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


class BaseScraper(ABC):
    """
    販売サイトスクレイパーの基底クラス
    
    各販売サイト固有のスクレイパーはこのクラスを継承して実装する
    """
    
    # サイト固有の設定（サブクラスでオーバーライド）
    SITE_NAME: str = "Unknown"
    BASE_URL: str = ""
    SEARCH_URL: str = ""
    USER_AGENT: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    
    # デフォルト設定
    DEFAULT_TIMEOUT: int = 30000  # 30秒
    DEFAULT_WAIT_TIME: int = 2000  # 2秒
    MAX_RETRIES: int = 3
    RETRY_DELAY: int = 2  # 秒
    
    def __init__(self, 
                 headless: bool = True,
                 timeout: int = None,
                 screenshot_dir: Optional[Path] = None):
        """
        Args:
            headless: ヘッドレスモード
            timeout: タイムアウト時間（ミリ秒）
            screenshot_dir: スクリーンショット保存ディレクトリ
        """
        self.headless = headless
        self.timeout = timeout or self.DEFAULT_TIMEOUT
        self.screenshot_dir = screenshot_dir
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        
        # 統計情報
        self.stats = {
            'total_searches': 0,
            'successful_searches': 0,
            'failed_searches': 0,
            'captcha_encounters': 0,
            'rate_limit_encounters': 0
        }
    
    async def __aenter__(self):
        """コンテキストマネージャー開始"""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """コンテキストマネージャー終了"""
        await self.cleanup()
    
    async def initialize(self):
        """ブラウザとページの初期化"""
        playwright = await async_playwright().start()
        
        # ブラウザ起動オプション
        launch_options = {
            'headless': self.headless,
            'args': [
                '--disable-blink-features=AutomationControlled',
                '--disable-features=site-per-process',
                f'--user-agent={self.USER_AGENT}'
            ]
        }
        
        self.browser = await playwright.chromium.launch(**launch_options)
        
        # コンテキスト作成（追加の設定）
        context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent=self.USER_AGENT,
            locale='ja-JP',
            timezone_id='Asia/Tokyo'
        )
        
        self.page = await context.new_page()
        
        # 自動化検出の回避
        await self.page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => false,
            });
        """)
        
        logger.info(f"{self.SITE_NAME}スクレイパーを初期化しました")
    
    async def cleanup(self):
        """リソースのクリーンアップ"""
        if self.page:
            await self.page.close()
        if self.browser:
            await self.browser.close()
        logger.info(f"{self.SITE_NAME}スクレイパーをクリーンアップしました")
    
    async def search_book(self, book_title: str, n_code: str) -> Optional[str]:
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
                
            except (CaptchaError, RateLimitError, PlaywrightTimeout, Exception) as e:
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
        elif isinstance(error, PlaywrightTimeout):
            logger.error(f"タイムアウト: {book_title}")
            await self._save_screenshot(f"timeout_{n_code}")
        else:
            logger.error(f"予期しないエラー: {error}", exc_info=True)
            await self._save_screenshot(f"error_{n_code}")
        
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
    
    async def _save_screenshot(self, name: str):
        """スクリーンショット保存"""
        if self.screenshot_dir and self.page:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = self.screenshot_dir / f"{self.SITE_NAME}_{name}_{timestamp}.png"
            await self.page.screenshot(path=str(filename))
            logger.debug(f"スクリーンショット保存: {filename}")
    
    async def wait_and_click(self, selector: str, timeout: int = None):
        """要素を待機してクリック"""
        timeout = timeout or self.timeout
        element = await self.page.wait_for_selector(selector, timeout=timeout)
        await element.click()
    
    async def wait_and_type(self, selector: str, text: str, timeout: int = None):
        """要素を待機してテキスト入力"""
        timeout = timeout or self.timeout
        element = await self.page.wait_for_selector(selector, timeout=timeout)
        await element.fill(text)
    
    async def get_text_content(self, selector: str) -> Optional[str]:
        """要素のテキストを取得"""
        element = await self.page.query_selector(selector)
        if element:
            return await element.text_content()
        return None
    
    @staticmethod
    def normalize_title(title: str) -> str:
        """
        タイトルの正規化 - 統合タイトル処理ユーティリティに委譲
        
        全角・半角統一、記号除去、スペース正規化など
        """
        return TitleProcessor.normalize_title(title)
    
    def is_title_match(self, expected: str, actual: str, threshold: float = 0.85) -> bool:
        """
        タイトルのマッチング判定 - 統合タイトル処理ユーティリティに委譲
        
        Args:
            expected: 期待されるタイトル
            actual: 実際のタイトル
            threshold: 類似度の閾値（0-1）
            
        Returns:
            マッチするかどうか
        """
        return TitleProcessor.is_title_match(expected, actual, threshold)
    
    # Levenshtein distance calculation moved to TitleProcessor utility
    
    def extract_volume_number(self, title: str) -> Optional[int]:
        """
        タイトルから巻数を抽出 - 統合タイトル処理ユーティリティに委譲
        
        Returns:
            巻数（抽出できない場合はNone）
        """
        return TitleProcessor.extract_volume_number(title)
    
    def normalize_volume_notation(self, title: str, target_format: str = 'circled') -> str:
        """
        巻数表記を統一形式に変換 - 統合タイトル処理ユーティリティに委譲
        
        Args:
            title: 変換対象のタイトル
            target_format: 'circled'（④）, 'arabic'（4）, 'kanji'（第4巻）, 'paren'（(4)）
            
        Returns:
            統一形式に変換されたタイトル
        """
        return TitleProcessor.normalize_volume_notation(title, target_format)
    
    def create_volume_variants(self, title: str) -> List[str]:
        """
        タイトルの巻数表記バリエーションを生成 - 統合タイトル処理ユーティリティに委譲
        
        Returns:
            異なる巻数表記のタイトルリスト
        """
        return TitleProcessor.create_volume_variants(title)
    
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
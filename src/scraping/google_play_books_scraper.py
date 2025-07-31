"""
Google Play Booksスクレイパー
いずみノベルズタイトルのGoogle Play Books URLを取得
"""
import asyncio
import logging
import os
from typing import Optional, List
from urllib.parse import quote_plus, urlencode
import re

from playwright.async_api import TimeoutError as PlaywrightTimeout
from .base_scraper import BaseScraper, NoResultError

logger = logging.getLogger(__name__)


class GooglePlayBooksScraper(BaseScraper):
    """Google Play Booksスクレイパー"""
    
    SITE_NAME = "Google Play Books"
    BASE_URL = "https://play.google.com"
    SEARCH_URL = "https://play.google.com/store/search"
    
    # Google Play Books固有の設定
    COOKIE_SELECTORS = [
        'button:has-text("すべて承諾")',
        'button:has-text("Accept all")',
        'button[aria-label="Accept all"]',
        'div[role="button"]:has-text("OK")'
    ]
    
    AGE_VERIFICATION_SELECTORS = [
        'button:has-text("続行")',
        'button:has-text("Continue")',
        'input[type="date"]'
    ]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    
    async def _search_impl(self, book_title: str, n_code: str) -> Optional[str]:
        """Google Play Books検索の実装"""
        
        # タイトルのバリエーションを生成
        title_variants = self.create_volume_variants(book_title)
        
        for variant in title_variants:
            # 基本検索（出版社名付き）
            url = await self._search_with_query(variant, "いずみノベルズ")
            if url:
                return url
            
            # 出版社名なしで再検索
            url = await self._search_with_query(variant, "")
            if url:
                return url
            
            # 短い待機
            await asyncio.sleep(1)
        
        return None
    
    async def _search_with_query(self, title: str, publisher: str) -> Optional[str]:
        """指定クエリでの検索実行"""
        try:
            # 検索クエリの構築
            if publisher:
                search_query = f'{title} {publisher}'
            else:
                search_query = title
            
            # 検索パラメータ
            params = {
                'q': search_query,
                'c': 'books',  # 書籍カテゴリ
                'hl': 'ja',    # 日本語
                'gl': 'JP'     # 日本
            }
            
            # URLの構築
            param_string = urlencode(params)
            search_url = f"{self.SEARCH_URL}?{param_string}"
            
            logger.debug(f"Google Play Books検索: {search_url}")
            
            # ページ読み込み
            await self.page.goto(search_url, wait_until='networkidle')
            
            # Cookie同意・年齢確認の処理
            await self._handle_consent_dialogs()
            
            # 検索結果の解析
            return await self._parse_search_results(title)
            
        except PlaywrightTimeout:
            logger.warning(f"Google Play Books検索タイムアウト: {title}")
            return None
        except Exception as e:
            logger.error(f"Google Play Books検索エラー: {e}")
            return None
    
    async def _handle_consent_dialogs(self):
        """Cookie同意・年齢確認ダイアログの処理"""
        # Cookie同意
        for selector in self.COOKIE_SELECTORS:
            try:
                element = await self.page.query_selector(selector)
                if element:
                    await element.click()
                    await asyncio.sleep(1)
                    logger.debug(f"Cookie同意ダイアログを処理: {selector}")
                    break
            except Exception:
                continue
        
        # 年齢確認
        for selector in self.AGE_VERIFICATION_SELECTORS:
            try:
                element = await self.page.query_selector(selector)
                if element:
                    await element.click()
                    await asyncio.sleep(1)
                    logger.debug(f"年齢確認ダイアログを処理: {selector}")
                    break
            except Exception:
                continue
    
    async def _parse_search_results(self, expected_title: str) -> Optional[str]:
        """検索結果の解析"""
        try:
            # 検索結果の待機（複数のセレクタを試行）
            result_selectors = [
                'div[data-n="COMMON_CLUSTERS"]',
                'div[role="listitem"]',
                'div.ULeU3b',  # 検索結果アイテム
                'div.mpg5gc'   # 書籍結果アイテム
            ]
            
            results = None
            for selector in result_selectors:
                try:
                    await self.page.wait_for_selector(selector, timeout=8000)
                    results = await self.page.query_selector_all(selector)
                    if results:
                        break
                except PlaywrightTimeout:
                    continue
            
            if not results:
                logger.debug("Google Play Books検索結果なし")
                return None
            
            logger.debug(f"Google Play Books検索結果: {len(results)}件")
            
            # 上位10件をチェック
            for i, result in enumerate(results[:10]):
                try:
                    # タイトル取得（複数パターン）
                    title_elem = await result.query_selector('div[role="heading"], h3, .Epkrse, .DdYX5')
                    if not title_elem:
                        # リンク内のタイトルも試行
                        title_elem = await result.query_selector('a[aria-label]')
                    
                    if not title_elem:
                        continue
                    
                    # タイトルテキストの取得
                    result_title = await title_elem.get_attribute('aria-label')
                    if not result_title:
                        result_title = await title_elem.text_content()
                    
                    if not result_title:
                        continue
                    
                    # タイトルマッチング
                    if not self.is_title_match(expected_title, result_title):
                        continue
                    
                    # 出版社チェック（オプション）
                    if await self._check_publisher_in_result(result):
                        # リンク取得
                        link_elem = await result.query_selector('a[href*="/store/books/details"]')
                        if not link_elem:
                            # 代替リンクパターン
                            link_elem = await result.query_selector('a[href*="play.google.com"]')
                        
                        if link_elem:
                            href = await link_elem.get_attribute('href')
                            if href:
                                # 絶対URLに変換
                                if href.startswith('/'):
                                    return f"{self.BASE_URL}{href}"
                                return href
                
                except Exception as e:
                    logger.debug(f"結果{i}解析エラー: {e}")
                    continue
            
            return None
            
        except PlaywrightTimeout:
            logger.warning("Google Play Books検索結果の解析でタイムアウト")
            return None
    
    async def _check_publisher_in_result(self, result_element) -> bool:
        """検索結果内で出版社をチェック"""
        try:
            # 出版社情報を取得（複数パターン）
            publisher_selectors = [
                '.P2Luy',  # 出版社名
                '.LbUacb', # サブタイトル・著者情報
                '.oJL8od', # 詳細情報
                'div[role="button"] + div' # ボタン下の情報
            ]
            
            for selector in publisher_selectors:
                elements = await result_element.query_selector_all(selector)
                for elem in elements:
                    text = await elem.text_content()
                    if text and ('いずみノベルズ' in text or 'イズミノベルズ' in text):
                        return True
            
            return True  # 出版社情報が見つからない場合はTrueを返す（検証は後で行う）
            
        except Exception:
            return True
    
    async def _verify_url(self, url: str, expected_title: str) -> bool:
        """取得したURLの検証"""
        try:
            # 商品ページに移動
            await self.page.goto(url, wait_until='networkidle', timeout=15000)
            
            # 同意ダイアログの処理
            await self._handle_consent_dialogs()
            
            # タイトル確認
            title_selectors = [
                'h1[itemprop="name"]',
                'h1.AHFaub',
                'div[role="heading"]',
                '.oOKOub'
            ]
            
            actual_title = None
            for selector in title_selectors:
                title_elem = await self.page.query_selector(selector)
                if title_elem:
                    actual_title = await title_elem.text_content()
                    if actual_title:
                        break
            
            if actual_title and not self.is_title_match(expected_title, actual_title.strip()):
                logger.debug(f"タイトル不一致: 期待={expected_title}, 実際={actual_title}")
                return False
            
            # 出版社確認
            if not await self._verify_publisher():
                logger.debug("出版社確認失敗")
                return False
            
            # 電子書籍確認
            if not await self._verify_ebook_format():
                logger.debug("電子書籍確認失敗")
                return False
            
            return True
            
        except PlaywrightTimeout:
            logger.warning(f"URL検証タイムアウト: {url}")
            return False
        except Exception as e:
            logger.error(f"URL検証エラー: {e}")
            return False
    
    async def _verify_publisher(self) -> bool:
        """出版社の確認"""
        try:
            # 出版社情報の確認（複数パターン）
            publisher_selectors = [
                '.Q1Lxfc',     # 出版社名
                '.bARER',      # 著者・出版社情報
                '[role="button"]:has-text("出版社")',
                'div:has-text("出版社")'
            ]
            
            for selector in publisher_selectors:
                elements = await self.page.query_selector_all(selector)
                for elem in elements:
                    text = await elem.text_content()
                    if text and ('いずみノベルズ' in text or 'イズミノベルズ' in text):
                        return True
            
            # より広範囲での検索
            page_content = await self.page.content()
            if 'いずみノベルズ' in page_content or 'イズミノベルズ' in page_content:
                return True
            
            logger.debug("出版社情報が見つかりません")
            return False
            
        except Exception as e:
            logger.debug(f"出版社確認エラー: {e}")
            return False
    
    async def _verify_ebook_format(self) -> bool:
        """電子書籍フォーマットの確認"""
        try:
            # 電子書籍表示の確認
            ebook_indicators = [
                'div:has-text("電子書籍")',
                'span:has-text("ePub")',
                'div:has-text("Google Play")',
                '.Z1hOCe:has-text("読む")',  # 読むボタン
                'button:has-text("読む")'
            ]
            
            for selector in ebook_indicators:
                element = await self.page.query_selector(selector)
                if element:
                    return True
            
            # URLからの判定（Google Play BooksのURL）
            current_url = self.page.url
            if 'play.google.com/store/books' in current_url:
                return True
            
            return False
            
        except Exception as e:
            logger.debug(f"電子書籍フォーマット確認エラー: {e}")
            return False
    
    async def _search_alternative(self, book_title: str, n_code: str) -> Optional[str]:
        """代替検索戦略"""
        try:
            # より短縮したタイトルでの検索
            if len(book_title) > 8:
                short_title = book_title[:8]
                return await self._search_with_query(short_title, "いずみノベルズ")
            
            # 英語キーワードでの検索
            english_keywords = ["light novel", "novel", "book"]
            for keyword in english_keywords:
                url = await self._search_with_query(f"{book_title} {keyword}", "")
                if url:
                    return url
            
            return None
            
        except Exception as e:
            logger.debug(f"代替検索エラー: {e}")
            return None
    
    def normalize_google_title(self, title: str) -> str:
        """Google Play Books特有のタイトル正規化"""
        # Google特有の表記を除去
        title = re.sub(r'\s*-\s*Google Play ブックス', '', title)
        title = re.sub(r'\s*\|\s*Google Play', '', title)
        
        # 基本正規化
        return self.normalize_title(title)
    
    def get_search_stats(self) -> dict:
        """Google Play Books固有の統計情報"""
        base_stats = self.get_stats()
        return {
            **base_stats,
            'consent_dialogs_handled': True,
            'search_categories': ['books']
        }
"""
楽天Koboスクレイパー
いずみノベルズタイトルの楽天Kobo URLを取得
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


class RakutenKoboScraper(BaseScraper):
    """楽天Koboスクレイパー"""
    
    SITE_NAME = "楽天Kobo"
    BASE_URL = "https://books.rakuten.co.jp"
    SEARCH_URL = "https://search.books.rakuten.co.jp/bksearch/dt"
    
    # 楽天固有の設定
    POPUP_SELECTORS = [
        'button.popup-close',
        'button[aria-label="閉じる"]',
        'div.campaign-popup button',
        '.modal-close'
    ]
    
    def __init__(self, affiliate_id: Optional[str] = None, **kwargs):
        super().__init__(**kwargs)
        # 楽天アフィリエイトID（環境変数からも取得可能）
        self.affiliate_id = affiliate_id or os.getenv('RAKUTEN_AFFILIATE_ID')
        if self.affiliate_id:
            logger.info(f"楽天アフィリエイトID設定: {self.affiliate_id}")
    
    async def _search_impl(self, book_title: str, n_code: str) -> Optional[str]:
        """楽天Kobo検索の実装"""
        
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
                'g': '101',  # 電子書籍
                'sitem': search_query,
                'v': '2',    # リスト表示
                'f': '2'     # 電子書籍のみ
            }
            
            # URLの構築
            param_string = urlencode(params)
            search_url = f"{self.SEARCH_URL}?{param_string}"
            
            logger.debug(f"楽天Kobo検索: {search_url}")
            
            # ページ読み込み
            await self.page.goto(search_url, wait_until='networkidle')
            
            # ポップアップを閉じる
            await self._close_popups()
            
            # 検索結果の解析
            return await self._parse_search_results(title)
            
        except PlaywrightTimeout:
            logger.warning(f"楽天Kobo検索タイムアウト: {title}")
            return None
        except Exception as e:
            logger.error(f"楽天Kobo検索エラー: {e}")
            return None
    
    async def _close_popups(self):
        """ポップアップを閉じる"""
        for selector in self.POPUP_SELECTORS:
            try:
                element = await self.page.query_selector(selector)
                if element:
                    await element.click()
                    await asyncio.sleep(0.5)
                    logger.debug(f"ポップアップを閉じました: {selector}")
            except Exception:
                continue
    
    async def _parse_search_results(self, expected_title: str) -> Optional[str]:
        """検索結果の解析"""
        try:
            # 検索結果の待機
            await self.page.wait_for_selector(
                'div.rbcomp__item',
                timeout=10000
            )
            
            # 結果要素を取得
            results = await self.page.query_selector_all('div.rbcomp__item')
            
            if not results:
                # 結果なしメッセージの確認
                no_result = await self.page.query_selector('p.rbcomp__noresult')
                if no_result:
                    logger.debug("楽天Kobo検索結果なし")
                return None
            
            logger.debug(f"楽天Kobo検索結果: {len(results)}件")
            
            # 上位10件をチェック
            for i, result in enumerate(results[:10]):
                try:
                    # 出版社チェック（優先）
                    if not await self._check_publisher_in_result(result):
                        continue
                    
                    # タイトル取得
                    title_elem = await result.query_selector('div.rbcomp__item-info__title a')
                    if not title_elem:
                        continue
                    
                    result_title = await title_elem.text_content()
                    if not result_title:
                        continue
                    
                    # タイトルマッチング
                    if not self.is_title_match(expected_title, result_title):
                        continue
                    
                    # リンク取得
                    href = await title_elem.get_attribute('href')
                    if href:
                        # 絶対URLに変換
                        if href.startswith('/'):
                            full_url = f"{self.BASE_URL}{href}"
                        else:
                            full_url = href
                        
                        # アフィリエイトID付きURLに変換
                        return self._add_affiliate_id(full_url)
                
                except Exception as e:
                    logger.debug(f"結果{i}解析エラー: {e}")
                    continue
            
            return None
            
        except PlaywrightTimeout:
            logger.warning("楽天Kobo検索結果の解析でタイムアウト")
            return None
    
    async def _check_publisher_in_result(self, result_element) -> bool:
        """検索結果内で出版社をチェック"""
        try:
            # 詳細情報を取得
            details_elem = await result_element.query_selector('div.rbcomp__item-info__details')
            if details_elem:
                details_text = await details_elem.text_content()
                if details_text and ('いずみノベルズ' in details_text or 'イズミノベルズ' in details_text):
                    return True
            
            # 著者情報もチェック
            author_elem = await result_element.query_selector('div.rbcomp__item-info__author')
            if author_elem:
                author_text = await author_elem.text_content()
                if author_text and ('いずみノベルズ' in author_text or 'イズミノベルズ' in author_text):
                    return True
            
            return True  # 出版社情報が見つからない場合はTrueを返す（検証は後で行う）
            
        except Exception:
            return True
    
    async def _verify_url(self, url: str, expected_title: str) -> bool:
        """取得したURLの検証"""
        try:
            # 商品ページに移動
            await self.page.goto(url, wait_until='networkidle', timeout=15000)
            
            # ポップアップを閉じる
            await self._close_popups()
            
            # タイトル確認
            title_elem = await self.page.query_selector('h1[itemprop="name"]')
            if title_elem:
                actual_title = await title_elem.text_content()
                if actual_title and not self.is_title_match(expected_title, actual_title.strip()):
                    logger.debug(f"タイトル不一致: 期待={expected_title}, 実際={actual_title}")
                    return False
            
            # 出版社確認
            if not await self._verify_publisher():
                logger.debug("出版社確認失敗")
                return False
            
            # 電子書籍フォーマット確認
            if not await self._verify_ebook_format():
                logger.debug("電子書籍フォーマット確認失敗")
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
            # 出版社情報の確認
            publisher_elem = await self.page.query_selector('div.productPublisher a')
            if publisher_elem:
                publisher_text = await publisher_elem.text_content()
                if publisher_text and ('いずみノベルズ' in publisher_text or 'イズミノベルズ' in publisher_text):
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
            # フォーマット表示の確認
            format_indicators = [
                'span.format',
                'div:has-text("kobo")',
                'div:has-text("電子書籍")',
                'span:has-text("ePub")'
            ]
            
            for selector in format_indicators:
                element = await self.page.query_selector(selector)
                if element:
                    text = await element.text_content()
                    if text and ('kobo' in text.lower() or '電子書籍' in text or 'epub' in text.lower()):
                        return True
            
            # URLからの判定（楽天koboのURL）
            current_url = self.page.url
            if 'books.rakuten.co.jp' in current_url and '/rk/' in current_url:
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
            
            return None
            
        except Exception as e:
            logger.debug(f"代替検索エラー: {e}")
            return None
    
    def _add_affiliate_id(self, url: str) -> str:
        """URLにアフィリエイトIDを付加"""
        if not self.affiliate_id:
            return url
        
        try:
            # 楽天のアフィリエイトリンクに変換
            # 実装は楽天アフィリエイトの仕様に依存
            # 基本的にはclickイベント経由でのアフィリエイト処理が一般的
            
            # URLの厳密な検証
            from urllib.parse import urlparse
            parsed = urlparse(url)
            
            if not parsed.netloc.endswith('books.rakuten.co.jp'):
                logger.warning(f"Invalid Rakuten URL domain: {parsed.netloc}")
                return url
            
            if parsed.scheme != 'https':
                logger.warning(f"Non-HTTPS Rakuten URL: {parsed.scheme}")
                return url
            
            # 簡単な実装（実際はより複雑な処理が必要）
            separator = '&' if '?' in url else '?'
            return f"{url}{separator}affiliate_id={self.affiliate_id}"
            
            return url
            
        except Exception as e:
            logger.debug(f"アフィリエイトID付加エラー: {e}")
            return url
    
    def normalize_kobo_title(self, title: str) -> str:
        """楽天Kobo特有のタイトル正規化"""
        # 楽天特有の表記を除去
        title = re.sub(r'【.*?】', '', title)  # 【電子書籍】など
        title = re.sub(r'\[.*?\]', '', title)  # [楽天Kobo]など
        
        # 基本正規化
        return self.normalize_title(title)
    
    def extract_main_title_from_series(self, full_title: str) -> str:
        """シリーズ名から作品名を抽出"""
        # パターン1: 「シリーズ名」作品名
        match = re.match(r'「(.+?)」(.+)', full_title)
        if match:
            return match.group(2).strip()
        
        return full_title
    
    def get_search_stats(self) -> dict:
        """楽天Kobo固有の統計情報"""
        base_stats = self.get_stats()
        return {
            **base_stats,
            'affiliate_enabled': bool(self.affiliate_id)
        }
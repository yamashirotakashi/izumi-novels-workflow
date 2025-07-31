"""
Amazon Kindleスクレイパー
いずみノベルズタイトルのAmazon Kindle URLを取得
"""
import asyncio
import logging
import os
from typing import Optional, List
from urllib.parse import quote_plus, urlparse, parse_qs, urlencode
import re

from playwright.async_api import TimeoutError as PlaywrightTimeout
from .base_scraper import BaseScraper, CaptchaError, NoResultError

logger = logging.getLogger(__name__)


class AmazonKindleScraper(BaseScraper):
    """Amazon Kindleスクレイパー"""
    
    SITE_NAME = "Amazon Kindle"
    BASE_URL = "https://www.amazon.co.jp"
    SEARCH_URL = "https://www.amazon.co.jp/s"
    
    # Amazon固有の設定
    CAPTCHA_SELECTORS = [
        'form[action="/errors/validateCaptcha"]',
        'div.a-row.a-text-center img[src*="captcha"]',
        'input[name="field-keywords"][placeholder*="文字"]'
    ]
    
    BLOCKED_SELECTORS = [
        'div:has-text("申し訳ございませんが、このリクエストを処理することができませんでした")',
        'div:has-text("リクエストがブロックされました")'
    ]
    
    def __init__(self, associate_id: Optional[str] = None, **kwargs):
        super().__init__(**kwargs)
        self.session_cookies = None
        # アソシエイトIDの設定（環境変数からも取得可能）
        self.associate_id = associate_id or os.getenv('AMAZON_ASSOCIATE_ID')
        if self.associate_id:
            logger.info(f"アソシエイトID設定: {self.associate_id}")
    
    async def _search_impl(self, book_title: str, n_code: str) -> Optional[str]:
        """Amazon Kindle検索の実装"""
        
        # タイトルのバリエーションを生成
        title_variants = self.create_volume_variants(book_title)
        
        for variant in title_variants:
            # 基本検索
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
                search_query = f'"{title}" {publisher}'
            else:
                search_query = f'"{title}"'
            
            # 検索パラメータ
            params = {
                'k': search_query,
                'i': 'digital-text',  # Kindleストア
                's': 'relevancerank',  # 関連度順
                'ref': 'sr_st_relevancerank'
            }
            
            # URLの構築
            param_string = '&'.join([f'{k}={quote_plus(str(v))}' for k, v in params.items()])
            search_url = f"{self.SEARCH_URL}?{param_string}"
            
            logger.debug(f"Amazon検索: {search_url}")
            
            # ページ読み込み
            await self.page.goto(search_url, wait_until='networkidle')
            
            # ブロック・CAPTCHA検出
            await self._check_blocking()
            
            # 検索結果の解析
            return await self._parse_search_results(title)
            
        except CaptchaError:
            raise
        except PlaywrightTimeout:
            logger.warning(f"Amazon検索タイムアウト: {title}")
            return None
        except Exception as e:
            logger.error(f"Amazon検索エラー: {e}")
            return None
    
    async def _check_blocking(self):
        """ブロック・CAPTCHA検出"""
        # CAPTCHA検出
        for selector in self.CAPTCHA_SELECTORS:
            element = await self.page.query_selector(selector)
            if element:
                await self._save_screenshot("captcha_detected")
                raise CaptchaError("Amazon CAPTCHA detected")
        
        # ブロック検出
        for selector in self.BLOCKED_SELECTORS:
            element = await self.page.query_selector(selector)
            if element:
                logger.warning("Amazon access blocked")
                await asyncio.sleep(10)
                raise CaptchaError("Amazon access blocked")
    
    async def _parse_search_results(self, expected_title: str) -> Optional[str]:
        """検索結果の解析"""
        try:
            # 検索結果の待機
            await self.page.wait_for_selector(
                'div[data-component-type="s-search-result"]',
                timeout=10000
            )
            
            # 結果要素を取得
            results = await self.page.query_selector_all(
                'div[data-component-type="s-search-result"]'
            )
            
            if not results:
                logger.debug("Amazon検索結果なし")
                return None
            
            logger.debug(f"Amazon検索結果: {len(results)}件")
            
            # 上位10件をチェック
            for i, result in enumerate(results[:10]):
                try:
                    # タイトル取得
                    title_elem = await result.query_selector('h2 a span')
                    if not title_elem:
                        continue
                    
                    result_title = await title_elem.text_content()
                    if not result_title:
                        continue
                    
                    # タイトルマッチング
                    if not self.is_title_match(expected_title, result_title):
                        continue
                    
                    # 出版社チェック（オプション）
                    if await self._check_publisher_in_result(result):
                        # リンク取得
                        link_elem = await result.query_selector('h2 a')
                        if link_elem:
                            href = await link_elem.get_attribute('href')
                            if href:
                                # 相対URLを絶対URLに変換
                                if href.startswith('/'):
                                    full_url = f"{self.BASE_URL}{href}"
                                else:
                                    full_url = href
                                
                                # アソシエイトID付きURLに変換
                                return self._add_associate_id(full_url)
                
                except Exception as e:
                    logger.debug(f"結果{i}解析エラー: {e}")
                    continue
            
            return None
            
        except PlaywrightTimeout:
            logger.warning("Amazon検索結果の解析でタイムアウト")
            return None
    
    async def _check_publisher_in_result(self, result_element) -> bool:
        """検索結果内で出版社をチェック"""
        try:
            # 著者・出版社情報を取得
            author_elements = await result_element.query_selector_all('span.a-size-base')
            
            for elem in author_elements:
                text = await elem.text_content()
                if text and ('いずみノベルズ' in text or 'イズミノベルズ' in text):
                    return True
            
            # 詳細情報もチェック
            detail_elements = await result_element.query_selector_all('span.a-size-base-plus')
            for elem in detail_elements:
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
            
            # ブロック・CAPTCHA検出
            await self._check_blocking()
            
            # タイトル確認
            title_elem = await self.page.query_selector('span#productTitle')
            if title_elem:
                actual_title = await title_elem.text_content()
                if actual_title and not self.is_title_match(expected_title, actual_title.strip()):
                    logger.debug(f"タイトル不一致: 期待={expected_title}, 実際={actual_title}")
                    return False
            
            # 出版社確認
            if not await self._verify_publisher():
                logger.debug("出版社確認失敗")
                return False
            
            # Kindle形式確認
            if not await self._verify_kindle_format():
                logger.debug("Kindle形式確認失敗")
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
            # 複数の場所で出版社情報を確認
            selectors = [
                '#detailBullets_feature_div li:has-text("出版社")',
                '#detail-bullets li:has-text("出版社")',
                '.a-section:has-text("出版社")',
                '#bookDetails_container_div li:has-text("出版社")'
            ]
            
            for selector in selectors:
                elements = await self.page.query_selector_all(selector)
                for elem in elements:
                    text = await elem.text_content()
                    if text and ('いずみノベルズ' in text or 'イズミノベルズ' in text or 'IZUMI' in text.upper()):
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
    
    async def _verify_kindle_format(self) -> bool:
        """Kindle形式の確認"""
        try:
            # Kindle表示の確認
            kindle_indicators = [
                'span:has-text("Kindle版")',
                'span:has-text("電子書籍")',
                '#format .a-button-text:has-text("Kindle")',
                '.a-button-group .a-button:has-text("Kindle")'
            ]
            
            for selector in kindle_indicators:
                element = await self.page.query_selector(selector)
                if element:
                    return True
            
            # URLからの判定（/dp/で始まるAmazon商品URL）
            current_url = self.page.url
            if '/dp/' in current_url and 'amazon.co.jp' in current_url:
                return True
            
            return False
            
        except Exception as e:
            logger.debug(f"Kindle形式確認エラー: {e}")
            return False
    
    async def _search_alternative(self, book_title: str, n_code: str) -> Optional[str]:
        """代替検索戦略"""
        try:
            # ASINが既知の場合の検索（将来の拡張用）
            # ASIN検索は今回はスキップ
            
            # より短縮したタイトルでの検索
            if len(book_title) > 10:
                short_title = book_title[:10]
                return await self._search_with_query(short_title, "いずみノベルズ")
            
            return None
            
        except Exception as e:
            logger.debug(f"代替検索エラー: {e}")
            return None
    
    async def _handle_captcha(self):
        """CAPTCHA対応"""
        logger.warning("Amazon CAPTCHA encountered - 長時間待機")
        await self._save_screenshot("captcha_handling")
        
        # 長時間待機（手動解決を期待）
        if not self.headless:
            logger.info("ヘッドレス無効 - 手動でCAPTCHAを解決してください（60秒待機）")
            await asyncio.sleep(60)
        else:
            # より長い待機
            await asyncio.sleep(120)
    
    def _add_associate_id(self, url: str) -> str:
        """URLにアソシエイトIDを付加"""
        if not self.associate_id:
            return url
        
        try:
            # URLを解析
            parsed = urlparse(url)
            
            # Amazon.co.jpのURLかチェック（厳密な検証）
            if not parsed.netloc.endswith('amazon.co.jp'):
                logger.warning(f"Invalid Amazon URL domain: {parsed.netloc}")
                return url
            
            # HTTPSのみ許可
            if parsed.scheme != 'https':
                logger.warning(f"Non-HTTPS Amazon URL: {parsed.scheme}")
                return url
            
            # クエリパラメータを取得
            query_params = parse_qs(parsed.query)
            
            # アソシエイトIDを追加
            query_params['tag'] = [self.associate_id]
            
            # URLを再構築
            new_query = urlencode(query_params, doseq=True)
            new_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}?{new_query}"
            
            return new_url
            
        except Exception as e:
            logger.debug(f"アソシエイトID付加エラー: {e}")
            return url
    
    def _extract_asin(self, url: str) -> Optional[str]:
        """AmazonのURLからASINを抽出"""
        try:
            # /dp/ASIN パターン
            dp_match = re.search(r'/dp/([A-Z0-9]{10})', url)
            if dp_match:
                return dp_match.group(1)
            
            # /gp/product/ASIN パターン
            gp_match = re.search(r'/gp/product/([A-Z0-9]{10})', url)
            if gp_match:
                return gp_match.group(1)
            
            return None
            
        except Exception:
            return None
    
    def create_amazon_affiliate_url(self, asin: str) -> str:
        """ASINからアフィリエイトURLを生成"""
        base_url = f"https://www.amazon.co.jp/dp/{asin}"
        
        if self.associate_id:
            return f"{base_url}?tag={self.associate_id}"
        else:
            return base_url
    
    def get_search_stats(self) -> dict:
        """Amazon固有の統計情報"""
        base_stats = self.get_stats()
        return {
            **base_stats,
            'captcha_rate': f"{(self.stats['captcha_encounters'] / max(1, self.stats['total_searches'])) * 100:.1f}%",
            'rate_limit_rate': f"{(self.stats['rate_limit_encounters'] / max(1, self.stats['total_searches'])) * 100:.1f}%"
        }
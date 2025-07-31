"""
Kinoppy Playwright版スクレイパー
JavaScript対応・動的コンテンツ完全対応版
"""
import asyncio
import logging
from typing import Optional, List, Dict, Any
from urllib.parse import quote, urljoin
import re

from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from bs4 import BeautifulSoup

from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class KinoppyPlaywrightScraper(BaseScraper):
    """Kinoppy Playwright版スクレイパー（JavaScript対応）"""
    
    SITE_NAME = "kinoppy_playwright"
    BASE_URL = "https://www.kinokuniya.co.jp"
    SEARCH_URL = "https://www.kinokuniya.co.jp/kinoppystore/search.php"
    
    def __init__(self, headless: bool = True, timeout: int = 30000):
        super().__init__()
        self.headless = headless
        self.timeout = timeout
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        
    async def __aenter__(self):
        """Playwright起動"""
        try:
            self.playwright = await async_playwright().start()
            
            # ブラウザ起動設定
            self.browser = await self.playwright.chromium.launch(
                headless=self.headless,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor'
                ]
            )
            
            # コンテキスト作成
            self.context = await self.browser.new_context(
                viewport={'width': 1280, 'height': 720},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            
            # ページ作成
            self.page = await self.context.new_page()
            self.page.set_default_timeout(self.timeout)
            
            logger.info(f"Kinoppy Playwright起動完了 (headless={self.headless})")
            return self
            
        except Exception as e:
            logger.error(f"Playwright起動エラー: {e}")
            await self._cleanup()
            raise
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Playwright終了"""
        await self._cleanup()
    
    async def _cleanup(self):
        """リソースクリーンアップ"""
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if hasattr(self, 'playwright'):
                await self.playwright.stop()
        except Exception as e:
            logger.warning(f"クリーンアップエラー: {e}")
    
    async def search_book(self, book_title: str, n_code: str = "") -> Optional[str]:
        """書籍検索のメイン処理"""
        try:
            logger.info(f"Playwright検索開始: {book_title} ({n_code})")
            
            # 検索戦略実行
            result = await self._search_impl(book_title, n_code)
            
            if result:
                logger.info(f"Playwright検索成功: {book_title} -> {result}")
                return result
            else:
                logger.warning(f"Playwright検索失敗: {book_title}")
                return None
                
        except Exception as e:
            logger.error(f"Playwright検索エラー: {book_title} - {str(e)}")
            return None
    
    async def _search_impl(self, book_title: str, n_code: str) -> Optional[str]:
        """Playwright検索実装"""
        try:
            # 検索ページに移動
            logger.debug(f"検索ページへ移動: {self.SEARCH_URL}")
            await self.page.goto(self.SEARCH_URL, wait_until='networkidle')
            
            # ページ読み込み待機
            await self.page.wait_for_load_state('domcontentloaded')
            
            # タイトルバリエーション生成
            title_variants = self._create_kinoppy_title_variants(book_title)
            
            for i, variant in enumerate(title_variants):
                logger.debug(f"検索バリエーション {i+1}/{len(title_variants)}: '{variant}'")
                
                try:
                    # 検索実行
                    result = await self._perform_search(variant)
                    if result:
                        return result
                        
                    # 戦略間待機
                    if i < len(title_variants) - 1:
                        await asyncio.sleep(1)
                        
                except Exception as e:
                    logger.warning(f"検索バリエーション失敗 '{variant}': {str(e)}")
                    continue
            
            return None
            
        except Exception as e:
            logger.error(f"Playwright検索実装エラー: {str(e)}")
            return None
    
    async def _perform_search(self, query: str) -> Optional[str]:
        """実際の検索実行"""
        try:
            # 検索フォームを探して入力
            search_input = None
            
            # 複数のセレクタを試行
            input_selectors = [
                'input[name="q"]',
                'input[type="text"]',
                'input[placeholder*="検索"]',
                '#search',
                '.search-input'
            ]
            
            for selector in input_selectors:
                try:
                    search_input = await self.page.query_selector(selector)
                    if search_input:
                        logger.debug(f"検索入力フィールド発見: {selector}")
                        break
                except:
                    continue
            
            if not search_input:
                logger.warning("検索入力フィールドが見つかりません")
                return None
            
            # 既存の値をクリア
            await search_input.fill("")
            await asyncio.sleep(0.5)
            
            # 検索クエリ入力
            await search_input.fill(query)
            await asyncio.sleep(0.5)
            
            # 検索実行（複数の方法を試行）
            search_executed = False
            
            # 方法1: Enterキー
            try:
                await search_input.press('Enter')
                search_executed = True
                logger.debug("Enterキーで検索実行")
            except:
                pass
            
            # 方法2: 検索ボタン
            if not search_executed:
                button_selectors = [
                    'input[type="submit"]',
                    'button[type="submit"]',
                    '.search-button',
                    '.btn-search'
                ]
                
                for selector in button_selectors:
                    try:
                        button = await self.page.query_selector(selector)
                        if button:
                            await button.click()
                            search_executed = True
                            logger.debug(f"検索ボタンで実行: {selector}")
                            break
                    except:
                        continue
            
            if not search_executed:
                logger.warning("検索実行方法が見つかりません")
                return None
            
            # 結果読み込み待機
            try:
                await self.page.wait_for_load_state('networkidle', timeout=10000)
            except:
                await asyncio.sleep(3)  # フォールバック待機
            
            # 結果解析
            return await self._extract_search_results(query)
            
        except Exception as e:
            logger.error(f"検索実行エラー '{query}': {str(e)}")
            return None
    
    async def _extract_search_results(self, query: str) -> Optional[str]:
        """検索結果の抽出"""
        try:
            # ページHTMLを取得
            html_content = await self.page.content()
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 検索結果コンテナを探す
            result_containers = self._find_book_containers(soup)
            
            if not result_containers:
                logger.debug(f"検索結果コンテナが見つかりません: {query}")
                return None
            
            logger.debug(f"検索結果コンテナ数: {len(result_containers)}")
            
            best_match = None
            best_score = 0
            
            for i, container in enumerate(result_containers[:10]):
                try:
                    # 書籍情報抽出
                    book_info = self._extract_book_info_from_container(container)
                    
                    if not book_info or not book_info.get('title') or not book_info.get('url'):
                        continue
                    
                    title = book_info['title']
                    url = book_info['url']
                    
                    # スコア計算
                    score = self.calculate_similarity_score(query, title)
                    
                    # 追加ボーナス
                    if 'kinokuniya.co.jp' in url:
                        score += 0.1
                    if len(title) > 5:
                        score += 0.05
                    
                    logger.debug(f"書籍候補 {i+1}: '{title[:50]}...' -> スコア {score:.3f}")
                    
                    if score > best_score and score >= 0.3:  # Playwrightではより高い閾値
                        best_match = url
                        best_score = score
                        
                except Exception as e:
                    logger.warning(f"書籍情報抽出エラー: {str(e)}")
                    continue
            
            if best_match:
                logger.info(f"最適マッチ発見 (スコア: {best_score:.3f}): {best_match}")
                return best_match
            else:
                logger.warning(f"適切なマッチが見つかりませんでした: {query}")
                return None
            
        except Exception as e:
            logger.error(f"検索結果抽出エラー: {str(e)}")
            return None
    
    def _find_book_containers(self, soup: BeautifulSoup) -> List:
        """書籍コンテナ発見（Playwright版強化）"""
        container_selectors = [
            # Kinoppy特有のパターン
            '.searchDetailBox',
            '.searchListDetail',
            '.bookListBox',
            '.book-item',
            '.search-result-item',
            'li[class*="book"]',
            'div[class*="book"]',
            'article',
            '.item',
            'li',
            
            # より広範囲
            'div[class*="product"]',
            'div[class*="detail"]',
            'div[class*="search"]',
            'div[class*="list"]',
        ]
        
        all_containers = []
        
        for selector in container_selectors:
            try:
                containers = soup.select(selector)
                for container in containers:
                    # 書籍リンクを含むかチェック
                    links = container.find_all('a', href=True)
                    book_links = [link for link in links if '/dsg-' in link.get('href', '') or 'book' in link.get('href', '').lower()]
                    
                    if book_links:
                        all_containers.append(container)
                        
            except Exception as e:
                logger.debug(f"セレクタエラー {selector}: {e}")
                continue
        
        # 重複除去
        unique_containers = []
        seen = set()
        
        for container in all_containers:
            container_id = id(container)
            if container_id not in seen:
                unique_containers.append(container)
                seen.add(container_id)
        
        return unique_containers[:20]  # 上位20個まで
    
    def _extract_book_info_from_container(self, container) -> Optional[Dict[str, str]]:
        """書籍情報抽出（Playwright版強化）"""
        try:
            info = {}
            
            # URL抽出
            url_selectors = [
                'a[href*="/dsg-"]',
                'a[href*="/book/"]',
                'a[href*="/detail/"]',
                'a[href]'
            ]
            
            url = None
            url_element = None
            
            for selector in url_selectors:
                url_element = container.select_one(selector)
                if url_element and url_element.get('href'):
                    url = url_element.get('href')
                    if url.startswith('/'):
                        url = self.BASE_URL + url
                    break
            
            if not url:
                return None
            
            info['url'] = url
            
            # タイトル抽出
            title = self._extract_title_from_container(container, url_element)
            
            if not title or len(title.strip()) < 3:
                return None
                
            info['title'] = title.strip()
            
            return info
            
        except Exception as e:
            logger.debug(f"書籍情報抽出エラー: {str(e)}")
            return None
    
    def _extract_title_from_container(self, container, url_element=None) -> Optional[str]:
        """タイトル抽出（多段階）"""
        
        # Method 1: URLリンクのタイトル属性
        if url_element and url_element.get('title'):
            title = url_element.get('title').strip()
            if len(title) > 3:
                return title
        
        # Method 2: URLリンクのテキスト
        if url_element:
            link_text = url_element.get_text(strip=True)
            if len(link_text) > 5:
                return link_text
        
        # Method 3: 特定のタイトルセレクタ
        title_selectors = [
            'h1', 'h2', 'h3', 'h4',
            '.title', '.book-title', '.product-title',
            '[class*="title"]', '[class*="name"]',
            '.heading', '.book-name'
        ]
        
        for selector in title_selectors:
            title_element = container.select_one(selector)
            if title_element:
                title = title_element.get_text(strip=True)
                if len(title) > 3:
                    return title
        
        # Method 4: 最も長いテキスト
        all_texts = []
        for text_node in container.find_all(string=True):
            text = text_node.strip()
            if len(text) > 5:
                all_texts.append(text)
        
        if all_texts:
            longest_text = max(all_texts, key=len)
            if len(longest_text) > 3:
                return longest_text
        
        return None
    
    def _create_kinoppy_title_variants(self, title: str) -> List[str]:
        """Kinoppy用タイトルバリエーション生成"""
        variants = set()
        
        # 基本正規化
        base_title = self.normalize_title(title)
        variants.add(base_title)
        variants.add(title)
        
        # 巻数表記のバリエーション
        circle_to_variants = {
            '①': ['1', '第1巻', '(1)', ' 1'],
            '②': ['2', '第2巻', '(2)', ' 2'],
            '③': ['3', '第3巻', '(3)', ' 3'],
            '④': ['4', '第4巻', '(4)', ' 4'],
            '⑤': ['5', '第5巻', '(5)', ' 5'],
        }
        
        for circle, replacements in circle_to_variants.items():
            if circle in title:
                for replacement in replacements:
                    variants.add(title.replace(circle, replacement))
        
        # 部分タイトル（巻数なし）
        series_only = self._extract_series_name(title)
        if series_only != title:
            variants.add(series_only)
        
        # 空文字削除
        variants = {v for v in variants if v.strip()}
        
        return list(variants)[:5]  # 上位5個まで
    
    def _extract_series_name(self, title: str) -> str:
        """シリーズ名抽出"""
        patterns = [
            r'[①-⑳]',
            r'第\\d+巻',
            r'\\d+巻',
            r'\\(\\d+\\)',
            r'[１２３４５６７８９０]+',
            r'[上中下]',
            r'前編|後編|完結編',
            r'【[^】]*】',
        ]
        
        series_name = title
        for pattern in patterns:
            series_name = re.sub(pattern, '', series_name).strip()
        
        return series_name if series_name else title
    
    async def _verify_url(self, url: str, expected_title: str) -> bool:
        """URL検証（Playwright版）"""
        try:
            if not url or not url.startswith(self.BASE_URL):
                return False
            
            # Kinoppyの書籍URLパターンチェック
            valid_patterns = ['/dsg-', '/detail/', '/book/']
            return any(pattern in url for pattern in valid_patterns)
            
        except Exception as e:
            logger.error(f"URL検証エラー: {url} - {str(e)}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """統計情報取得"""
        return {
            'site_name': self.SITE_NAME,
            'scraper_type': 'Playwright + BeautifulSoup',
            'javascript_support': True,
            'dynamic_content': True,
            'search_method': 'Form Interaction + Dynamic Analysis',
            'browser_engine': 'Chromium',
            'headless_mode': self.headless
        }
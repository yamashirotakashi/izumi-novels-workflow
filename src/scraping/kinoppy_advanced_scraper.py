"""
Kinoppy 高度ブラウザ自動化スクレイパー
undetected-chromedriver + 人間らしい動作パターン + bot検知回避
"""
import asyncio
import logging
import random
import time
import math
from typing import Optional, List, Dict, Any, Tuple
from urllib.parse import quote, urljoin
import re
from dataclasses import dataclass

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup

from .selenium_base_scraper import SeleniumBaseScraper, ScrapingError, CaptchaError, RateLimitError, NoResultError

logger = logging.getLogger(__name__)


@dataclass
class HumanBehavior:
    """人間らしい動作パラメータ"""
    typing_speed_min: float = 0.05
    typing_speed_max: float = 0.15
    mouse_move_steps: int = 10
    scroll_pause_min: float = 0.5
    scroll_pause_max: float = 2.0
    page_load_wait_min: float = 2.0
    page_load_wait_max: float = 5.0


class KinoppyAdvancedScraper(SeleniumBaseScraper):
    """Kinoppy 高度ブラウザ自動化スクレイパー"""
    
    SITE_NAME = "kinoppy_advanced"
    BASE_URL = "https://www.kinokuniya.co.jp"
    SEARCH_URL = "https://www.kinokuniya.co.jp/kinoppystore/search.php"
    
    def __init__(self, headless: bool = True, timeout: int = 30):
        super().__init__()
        self.headless = headless
        self.timeout = timeout
        self.driver = None
        self.human_behavior = HumanBehavior()
        
    async def __aenter__(self):
        """スクレイパー起動"""
        try:
            logger.info("Kinoppy高度ブラウザ自動化開始")
            
            # Chrome設定（bot検知回避）
            options = uc.ChromeOptions()
            
            # 基本設定
            if self.headless:
                options.add_argument('--headless=new')
            
            # bot検知回避設定
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-setuid-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            
            # リアルな環境設定
            options.add_argument('--window-size=1280,720')
            options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36')
            
            # プリファレンス設定
            prefs = {
                "profile.default_content_setting_values": {
                    "notifications": 2  # 通知を無効化
                },
                "profile.managed_default_content_settings": {
                    "images": 2  # 画像読み込み無効化（高速化）
                }
            }
            options.add_experimental_option("prefs", prefs)
            
            # undetected-chromedriver起動
            self.driver = uc.Chrome(options=options, version_main=None)
            
            # JavaScript実行でwebdriver痕跡を除去
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            logger.info("Chrome起動完了（bot検知回避設定済み）")
            return self
            
        except Exception as e:
            logger.error(f"スクレイパー起動エラー: {e}")
            await self._cleanup()
            raise
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """スクレイパー終了"""
        await self._cleanup()
    
    async def _cleanup(self):
        """リソースクリーンアップ"""
        try:
            if self.driver:
                self.driver.quit()
                logger.info("Chrome終了完了")
        except Exception as e:
            logger.warning(f"クリーンアップエラー: {e}")
    
    async def search_book(self, book_title: str, n_code: str = "") -> Optional[str]:
        """書籍検索のメイン処理"""
        try:
            logger.info(f"高度検索開始: {book_title} ({n_code})")
            
            # 検索ページに移動（人間らしい動作）
            await self._navigate_to_search_page()
            
            # タイトルバリエーション生成
            title_variants = self._create_kinoppy_title_variants(book_title)
            
            for i, variant in enumerate(title_variants):
                logger.debug(f"検索バリエーション {i+1}/{len(title_variants)}: '{variant}'")
                
                try:
                    # 検索実行
                    result = await self._perform_advanced_search(variant)
                    if result:
                        logger.info(f"高度検索成功: {book_title} -> {result}")
                        return result
                        
                    # 戦略間待機（人間らしい間隔）
                    if i < len(title_variants) - 1:
                        await self._human_pause(2.0, 4.0)
                        
                except Exception as e:
                    logger.warning(f"検索バリエーション失敗 '{variant}': {str(e)}")
                    continue
            
            logger.warning(f"高度検索失敗: {book_title}")
            return None
            
        except Exception as e:
            logger.error(f"高度検索エラー: {book_title} - {str(e)}")
            return None
    
    async def _navigate_to_search_page(self):
        """検索ページへの人間らしいナビゲーション"""
        try:
            logger.debug(f"検索ページへ移動: {self.SEARCH_URL}")
            
            # ページ移動
            self.driver.get(self.SEARCH_URL)
            
            # 人間らしい待機
            await self._human_pause(
                self.human_behavior.page_load_wait_min,
                self.human_behavior.page_load_wait_max
            )
            
            # ページ読み込み完了まで待機
            WebDriverWait(self.driver, self.timeout).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # 軽いスクロール（人間らしい動作）
            await self._human_scroll(200, 500)
            
            logger.debug("検索ページ移動完了")
            
        except Exception as e:
            logger.error(f"検索ページ移動エラー: {str(e)}")
            raise
    
    async def _perform_advanced_search(self, query: str) -> Optional[str]:
        """高度検索実行（人間らしい動作パターン）"""
        try:
            # 検索入力フィールドを探す
            search_input = await self._find_search_input()
            if not search_input:
                logger.warning("検索入力フィールドが見つかりません")
                return None
            
            # 既存の値をクリア（人間らしく）
            await self._human_clear_input(search_input)
            
            # 検索クエリを人間らしく入力
            await self._human_type(search_input, query)
            
            # 少し待機
            await self._human_pause(0.5, 1.5)
            
            # 検索実行
            await self._human_submit_search(search_input)
            
            # 結果読み込み待機
            await self._wait_for_search_results()
            
            # 結果解析
            return await self._extract_advanced_search_results(query)
            
        except Exception as e:
            logger.error(f"高度検索実行エラー '{query}': {str(e)}")
            return None
    
    async def _find_search_input(self) -> Optional:
        """検索入力フィールドを発見"""
        input_selectors = [
            'input[name="q"]',
            'input[type="text"]',
            'input[placeholder*="検索"]',
            '#search',
            '.search-input',
            'input[class*="search"]'
        ]
        
        for selector in input_selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    if element.is_displayed() and element.is_enabled():
                        logger.debug(f"検索入力フィールド発見: {selector}")
                        return element
            except:
                continue
        
        return None
    
    async def _human_clear_input(self, element):
        """人間らしい入力クリア"""
        try:
            # フィールドをクリック
            element.click()
            await self._human_pause(0.2, 0.5)
            
            # 全選択してクリア
            element.send_keys(Keys.CONTROL + "a")
            await self._human_pause(0.1, 0.3)
            element.send_keys(Keys.DELETE)
            await self._human_pause(0.2, 0.4)
            
        except Exception as e:
            logger.debug(f"入力クリアエラー: {e}")
    
    async def _human_type(self, element, text: str):
        """人間らしいタイピング"""
        try:
            for char in text:
                element.send_keys(char)
                
                # タイピング速度をランダム化
                typing_delay = random.uniform(
                    self.human_behavior.typing_speed_min,
                    self.human_behavior.typing_speed_max
                )
                await asyncio.sleep(typing_delay)
                
                # 時々少し長い間隔（人間の癖を模倣）
                if random.random() < 0.1:  # 10%の確率
                    await asyncio.sleep(random.uniform(0.3, 0.8))
            
            logger.debug(f"人間らしいタイピング完了: '{text}'")
            
        except Exception as e:
            logger.error(f"タイピングエラー: {e}")
            raise
    
    async def _human_submit_search(self, search_input):
        """人間らしい検索実行"""
        try:
            # 方法1: Enterキー
            search_input.send_keys(Keys.RETURN)
            logger.debug("Enterキーで検索実行")
            
        except Exception as e:
            # 方法2: 検索ボタンをクリック
            try:
                button_selectors = [
                    'input[type="submit"]',
                    'button[type="submit"]',
                    '.search-button',
                    '.btn-search',
                    'button[class*="search"]'
                ]
                
                for selector in button_selectors:
                    try:
                        button = self.driver.find_element(By.CSS_SELECTOR, selector)
                        if button.is_displayed() and button.is_enabled():
                            button.click()
                            logger.debug(f"検索ボタンクリック: {selector}")
                            return
                    except:
                        continue
                
                logger.warning("検索実行方法が見つかりません")
                
            except Exception as e2:
                logger.error(f"検索実行エラー: {e}, {e2}")
                raise
    
    async def _wait_for_search_results(self):
        """検索結果の読み込み待機"""
        try:
            # 検索結果要素の出現を待機
            result_selectors = [
                '.searchDetailBox',
                '.searchListDetail',
                '.book-item',
                '.search-result',
                'article',
                'li'
            ]
            
            wait = WebDriverWait(self.driver, self.timeout)
            
            for selector in result_selectors:
                try:
                    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                    logger.debug(f"検索結果要素発見: {selector}")
                    break
                except TimeoutException:
                    continue
            
            # 追加の待機（JavaScript処理完了）
            await self._human_pause(2.0, 4.0)
            
            # 軽いスクロール（検索結果の表示確認）
            await self._human_scroll(300, 600)
            
        except Exception as e:
            logger.warning(f"検索結果待機エラー: {e}")
    
    async def _extract_advanced_search_results(self, query: str) -> Optional[str]:
        """高度検索結果の抽出"""
        try:
            # ページソースを取得
            html_content = self.driver.page_source
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 検索結果コンテナを探す
            result_containers = self._find_book_containers_advanced(soup)
            
            if not result_containers:
                logger.debug(f"検索結果コンテナが見つかりません: {query}")
                return None
            
            logger.debug(f"検索結果コンテナ数: {len(result_containers)}")
            
            best_match = None
            best_score = 0
            
            for i, container in enumerate(result_containers[:15]):
                try:
                    # 書籍情報抽出
                    book_info = self._extract_book_info_advanced(container)
                    
                    if not book_info or not book_info.get('title') or not book_info.get('url'):
                        continue
                    
                    title = book_info['title']
                    url = book_info['url']
                    
                    # スコア計算
                    score = self.calculate_similarity_score(query, title)
                    
                    # 追加ボーナス
                    if 'kinokuniya.co.jp' in url:
                        score += 0.1
                    if '/dsg-' in url:  # 紀伊國屋詳細ページ
                        score += 0.15
                    if len(title) > 5:
                        score += 0.05
                    
                    logger.debug(f"書籍候補 {i+1}: '{title[:50]}...' -> スコア {score:.3f}")
                    
                    if score > best_score and score >= 0.25:  # 高度手法では少し低めの閾値
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
    
    def _find_book_containers_advanced(self, soup: BeautifulSoup) -> List:
        """書籍コンテナ発見（高度版）"""
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
            '*[class*="result"]'
        ]
        
        all_containers = []
        
        for selector in container_selectors:
            try:
                containers = soup.select(selector)
                for container in containers:
                    # 書籍リンクを含むかチェック
                    links = container.find_all('a', href=True)
                    book_links = [link for link in links 
                                if any(pattern in link.get('href', '') 
                                      for pattern in ['/dsg-', '/detail/', '/book/', 'kinokuniya.co.jp'])]
                    
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
    
    def _extract_book_info_advanced(self, container) -> Optional[Dict[str, str]]:
        """書籍情報抽出（高度版）"""
        try:
            info = {}
            
            # URL抽出（優先度順）
            url_selectors = [
                'a[href*="/dsg-"]',        # 最優先（紀伊國屋詳細ページ）
                'a[href*="/detail/"]',     # 次優先
                'a[href*="/book/"]',       # 補助
                'a[href*="kinokuniya.co.jp"]',  # 紀伊國屋サイト内
                'a[href]'                  # フォールバック
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
            
            # タイトル抽出（複数の方法を試行）
            title = self._extract_title_advanced(container, url_element)
            
            if not title or len(title.strip()) < 3:
                return None
                
            info['title'] = title.strip()
            
            return info
            
        except Exception as e:
            logger.debug(f"書籍情報抽出エラー: {str(e)}")
            return None
    
    def _extract_title_advanced(self, container, url_element=None) -> Optional[str]:
        """タイトル抽出（高度版）"""
        
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
            '.heading', '.book-name',
            'strong', 'b'
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
            if len(text) > 5 and not text.isdigit():
                all_texts.append(text)
        
        if all_texts:
            longest_text = max(all_texts, key=len)
            if len(longest_text) > 3:
                return longest_text
        
        return None
    
    def _create_kinoppy_title_variants(self, title: str) -> List[str]:
        """Kinoppy用タイトルバリエーション生成（高度版）"""
        variants = set()
        
        # 基本正規化
        base_title = self.normalize_title(title)
        variants.add(base_title)
        variants.add(title)
        
        # 巻数表記のバリエーション（拡張版）
        circle_to_variants = {
            '①': ['1', '第1巻', '(1)', ' 1', '１', 'I'],
            '②': ['2', '第2巻', '(2)', ' 2', '２', 'II'],
            '③': ['3', '第3巻', '(3)', ' 3', '３', 'III'],
            '④': ['4', '第4巻', '(4)', ' 4', '４', 'IV'],
            '⑤': ['5', '第5巻', '(5)', ' 5', '５', 'V'],
            '⑥': ['6', '第6巻', '(6)', ' 6', '６', 'VI'],
            '⑦': ['7', '第7巻', '(7)', ' 7', '７', 'VII'],
        }
        
        for circle, replacements in circle_to_variants.items():
            if circle in title:
                for replacement in replacements:
                    variants.add(title.replace(circle, replacement))
        
        # 部分検索バリエーション
        words = base_title.split()
        if len(words) >= 2:
            # 最初の2単語
            variants.add(' '.join(words[:2]))
            # 最初の3単語（あるなら）
            if len(words) >= 3:
                variants.add(' '.join(words[:3]))
        
        # シリーズ名のみ
        series_only = self._extract_series_name_advanced(title)
        if series_only != title and len(series_only) > 3:
            variants.add(series_only)
        
        # 空文字削除・重複除去
        variants = {v for v in variants if v.strip()}
        return list(variants)[:7]  # 上位7個まで
    
    def _extract_series_name_advanced(self, title: str) -> str:
        """シリーズ名抽出（高度版）"""
        patterns = [
            r'[①-⑳]',
            r'第\d+巻',
            r'\d+巻',
            r'\(\d+\)',
            r'[１２３４５６７８９０]+',
            r'[上中下]',
            r'前編|後編|完結編',
            r'【[^】]*】',
            r'\s*-\s*\d+\s*$',  # 末尾の「- 1」など
            r'\s*\d+\s*$',      # 末尾の数字
        ]
        
        series_name = title
        for pattern in patterns:
            series_name = re.sub(pattern, '', series_name).strip()
        
        return series_name if series_name else title
    
    async def _human_pause(self, min_seconds: float, max_seconds: float):
        """人間らしい待機"""
        pause_time = random.uniform(min_seconds, max_seconds)
        await asyncio.sleep(pause_time)
    
    async def _human_scroll(self, min_pixels: int, max_pixels: int):
        """人間らしいスクロール"""
        try:
            scroll_amount = random.randint(min_pixels, max_pixels)
            self.driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
            
            await self._human_pause(
                self.human_behavior.scroll_pause_min,
                self.human_behavior.scroll_pause_max
            )
        except Exception as e:
            logger.debug(f"スクロールエラー: {e}")
    
    # 抽象メソッドの実装（基底クラス互換性のため）
    async def _search_impl(self, book_title: str, n_code: str) -> Optional[str]:
        """検索実装（search_bookのラッパー）"""
        return await self.search_book(book_title, n_code)
    
    async def _verify_url(self, url: str, expected_title: str) -> bool:
        """URL検証"""
        try:
            if not url or not url.startswith(self.BASE_URL):
                return False
            
            # 紀伊國屋の書籍URLパターンチェック
            valid_patterns = ['/dsg-', '/detail/', '/book/']
            return any(pattern in url for pattern in valid_patterns)
            
        except Exception as e:
            logger.error(f"URL検証エラー: {url} - {str(e)}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """統計情報取得"""
        return {
            'site_name': self.SITE_NAME,
            'scraper_type': 'undetected-chromedriver + Human-like Behavior',
            'bot_detection_evasion': True,
            'human_behavior_simulation': True,
            'search_method': 'Advanced Browser Automation',
            'detection_resistance': 'High',
            'javascript_support': True,
            'dynamic_content': True
        }
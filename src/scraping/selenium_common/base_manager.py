"""
Selenium基底ブラウザ管理クラス
共通のブラウザ操作とライフサイクル管理
"""
import asyncio
import logging
from typing import Optional, Dict, Any, List
from abc import ABC, abstractmethod
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup

from .chrome_setup import create_undetected_chrome, get_undetected_chrome_options
from .human_behavior import HumanBehaviorSimulator, HumanBehavior
from ..selenium_base_scraper import SeleniumBaseScraper, ScrapingError, CaptchaError, RateLimitError, NoResultError

logger = logging.getLogger(__name__)


class BaseBrowserManager(SeleniumBaseScraper):
    """
    Selenium基底ブラウザ管理クラス
    共通のブラウザ操作とbot検知回避機能を提供
    """
    
    def __init__(self, 
                 site_name: str,
                 base_url: str,
                 search_url: str,
                 headless: bool = True, 
                 timeout: int = 30,
                 custom_behavior: Optional[HumanBehavior] = None):
        """
        Args:
            site_name: サイト名
            base_url: ベースURL
            search_url: 検索URL
            headless: ヘッドレスモード
            timeout: タイムアウト時間
            custom_behavior: カスタム動作パラメータ
        """
        super().__init__()
        self.site_name = site_name
        self.base_url = base_url
        self.search_url = search_url
        self.headless = headless
        self.timeout = timeout
        self.driver = None
        
        # 人間らしい動作シミュレーター
        self.human_simulator = HumanBehaviorSimulator(custom_behavior)
        
    async def __aenter__(self):
        """スクレイパー起動"""
        try:
            logger.info(f"{self.site_name} 高度ブラウザ自動化開始")
            
            # Chrome設定取得
            options = get_undetected_chrome_options(
                headless=self.headless,
                disable_images=True
            )
            
            # undetected-chromedriver起動
            self.driver = create_undetected_chrome(options=options)
            
            logger.info(f"{self.site_name} Chrome起動完了（bot検知回避設定済み）")
            return self
            
        except Exception as e:
            logger.error(f"{self.site_name} スクレイパー起動エラー: {e}")
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
                logger.info(f"{self.site_name} Chrome終了完了")
        except Exception as e:
            logger.warning(f"{self.site_name} クリーンアップエラー: {e}")
    
    async def navigate_to_search_page(self):
        """検索ページへの人間らしいナビゲーション"""
        try:
            logger.debug(f"検索ページへ移動: {self.search_url}")
            
            # ページ移動
            self.driver.get(self.search_url)
            
            # 人間らしい待機
            await self.human_simulator.wait_for_page_load()
            
            # ページ読み込み完了まで待機
            WebDriverWait(self.driver, self.timeout).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # 軽いスクロール（人間らしい動作）
            await self.human_simulator.human_scroll(self.driver, 200, 500)
            
            logger.debug(f"{self.site_name} 検索ページ移動完了")
            
        except Exception as e:
            logger.error(f"{self.site_name} 検索ページ移動エラー: {str(e)}")
            raise
    
    async def find_search_input(self, custom_selectors: Optional[List[str]] = None):
        """検索入力フィールドを発見"""
        default_selectors = [
            'input[name="q"]',
            'input[name="query"]',
            'input[name="keyword"]',
            'input[type="text"]',
            'input[placeholder*="検索"]',
            'input[placeholder*="search"]',
            '#search',
            '.search-input',
            'input[class*="search"]'
        ]
        
        input_selectors = custom_selectors or default_selectors
        
        for selector in input_selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    if element.is_displayed() and element.is_enabled():
                        logger.debug(f"{self.site_name} 検索入力フィールド発見: {selector}")
                        return element
            except:
                continue
        
        return None
    
    async def perform_search(self, query: str, custom_input_selectors: Optional[List[str]] = None) -> bool:
        """検索実行（人間らしい動作パターン）"""
        try:
            # 検索入力フィールドを探す
            search_input = await self.find_search_input(custom_input_selectors)
            if not search_input:
                logger.warning(f"{self.site_name} 検索入力フィールドが見つかりません")
                return False
            
            # 既存の値をクリア（人間らしく）
            await self.human_simulator.human_clear_input(search_input)
            
            # 検索クエリを人間らしく入力
            await self.human_simulator.human_type(search_input, query)
            
            # 少し待機
            await self.human_simulator.human_pause(0.5, 1.5)
            
            # 検索実行
            await self.human_simulator.human_submit_search(search_input, self.driver)
            
            return True
            
        except Exception as e:
            logger.error(f"{self.site_name} 検索実行エラー '{query}': {str(e)}")
            return False
    
    async def wait_for_search_results(self, custom_result_selectors: Optional[List[str]] = None):
        """検索結果の読み込み待機"""
        try:
            default_selectors = [
                'div[class*="product"]',
                'div[class*="book"]',
                'div[class*="item"]',
                '.search-result',
                'article',
                'li'
            ]
            
            result_selectors = custom_result_selectors or default_selectors
            wait = WebDriverWait(self.driver, self.timeout)
            
            for selector in result_selectors:
                try:
                    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                    logger.debug(f"{self.site_name} 検索結果要素発見: {selector}")
                    break
                except TimeoutException:
                    continue
            
            # 追加の待機（JavaScript処理完了）
            await self.human_simulator.human_pause(2.0, 4.0)
            
            # 軽いスクロール（検索結果の表示確認）
            await self.human_simulator.human_scroll(self.driver, 300, 600)
            
        except Exception as e:
            logger.warning(f"{self.site_name} 検索結果待機エラー: {e}")
    
    def get_page_soup(self) -> BeautifulSoup:
        """現在のページのBeautifulSoupオブジェクト取得"""
        html_content = self.driver.page_source
        return BeautifulSoup(html_content, 'html.parser')
    
    def find_book_containers(self, 
                           soup: BeautifulSoup, 
                           custom_selectors: Optional[List[str]] = None,
                           url_patterns: Optional[List[str]] = None) -> List:
        """書籍コンテナ発見（汎用版）"""
        default_selectors = [
            'div[class*="product"]',
            'div[class*="book"]',
            'div[class*="item"]',
            'div[class*="result"]',
            '.search-result-item',
            'li[class*="product"]',
            'li[class*="book"]',
            'article',
            '.item',
            'li'
        ]
        
        default_url_patterns = ['/detail/', '/item/', '/product/', '/book/']
        
        container_selectors = custom_selectors or default_selectors
        url_patterns = url_patterns or default_url_patterns
        
        all_containers = []
        
        for selector in container_selectors:
            try:
                containers = soup.select(selector)
                for container in containers:
                    # 書籍リンクを含むかチェック
                    links = container.find_all('a', href=True)
                    book_links = [link for link in links 
                                if any(pattern in link.get('href', '') 
                                      for pattern in url_patterns)]
                    
                    if book_links:
                        all_containers.append(container)
                        
            except Exception as e:
                logger.debug(f"{self.site_name} セレクタエラー {selector}: {e}")
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
    
    @abstractmethod
    async def search_book(self, book_title: str, n_code: str = "") -> Optional[str]:
        """書籍検索のメイン処理（サブクラスで実装）"""
        pass
    
    @abstractmethod
    def create_title_variants(self, title: str) -> List[str]:
        """タイトルバリエーション生成（サブクラスで実装）"""
        pass
    
    @abstractmethod
    def extract_book_info(self, container) -> Optional[Dict[str, str]]:
        """書籍情報抽出（サブクラスで実装）"""
        pass
    
    # 基底クラス互換性のための実装
    async def _search_impl(self, book_title: str, n_code: str) -> Optional[str]:
        """検索実装（search_bookのラッパー）"""
        return await self.search_book(book_title, n_code)
    
    async def _verify_url(self, url: str, expected_title: str) -> bool:
        """URL検証（基本実装）"""
        try:
            return url and url.startswith(self.base_url)
        except Exception as e:
            logger.error(f"{self.site_name} URL検証エラー: {url} - {str(e)}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """統計情報取得"""
        return {
            'site_name': self.site_name,
            'scraper_type': 'BaseBrowserManager + undetected-chromedriver',
            'bot_detection_evasion': True,
            'human_behavior_simulation': True,
            'search_method': 'Advanced Browser Automation',
            'detection_resistance': 'High',
            'javascript_support': True,
            'dynamic_content': True
        }
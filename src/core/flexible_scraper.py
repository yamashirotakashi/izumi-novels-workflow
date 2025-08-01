#!/usr/bin/env python3
"""
柔軟なスクレイパーシステム
設定ファイルベースのセレクタ管理
"""
import json
import time
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

@dataclass
class SearchResult:
    """検索結果データクラス"""
    site: str
    query: str
    results_count: int
    status: str
    url: str
    page_title: str = ""
    books_found: List[Dict[str, str]] = None
    error_message: str = ""

class FlexibleScraper:
    """設定ファイルベースの柔軟なスクレイパー"""
    
    def __init__(self, config_path: str = None):
        self.config_path = config_path or Path(__file__).parent.parent.parent / "config" / "site_selectors.json"
        self.config = self._load_config()
        self.driver = None
        self.results = []
        self.logger = self._setup_logger()
    
    def _setup_logger(self):
        """ロガー設定"""
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger
    
    def _load_config(self) -> Dict[str, Any]:
        """設定ファイル読み込み"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            self.logger.error(f"設定ファイルが見つかりません: {self.config_path}")
            return {"sites": {}, "global_settings": {}}
        except json.JSONDecodeError as e:
            self.logger.error(f"設定ファイルの解析エラー: {e}")
            return {"sites": {}, "global_settings": {}}
    
    def update_selectors(self, site: str, selector_type: str, new_selectors: List[str]):
        """セレクタを動的に更新"""
        if site in self.config["sites"]:
            self.config["sites"][site]["selectors"][selector_type] = new_selectors
            self._save_config()
            self.logger.info(f"セレクタ更新: {site}.{selector_type}")
    
    def add_site(self, site_config: Dict[str, Any]):
        """新しいサイト設定を追加"""
        site_name = site_config.get("name", "unknown").lower()
        self.config["sites"][site_name] = site_config
        self._save_config()
        self.logger.info(f"新しいサイト追加: {site_name}")
    
    def _save_config(self):
        """設定ファイル保存"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.error(f"設定ファイル保存エラー: {e}")
    
    def setup_driver(self):
        """Chrome WebDriver設定"""
        self.logger.info("Chrome WebDriverを設定中...")
        
        options = uc.ChromeOptions()
        
        # WSL環境用Chrome設定
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # グローバル設定からChromeオプションを適用
        chrome_options = self.config.get("global_settings", {}).get("chrome_options", [])
        for option in chrome_options:
            if not any(opt in option for opt in ['--no-sandbox', '--disable-dev-shm-usage']):
                options.add_argument(option)
        
        try:
            self.driver = uc.Chrome(options=options, version_main=None)
            self.driver.maximize_window()
            self.logger.info("Chrome WebDriver準備完了")
        except Exception as e:
            self.logger.error(f"Chrome WebDriver設定エラー: {e}")
            # フォールバック: 通常のSelenium ChromeDriverを試行
            from selenium import webdriver
            from selenium.webdriver.chrome.service import Service
            from selenium.webdriver.chrome.options import Options
            
            fallback_options = Options()
            fallback_options.add_argument('--no-sandbox')
            fallback_options.add_argument('--disable-dev-shm-usage')
            fallback_options.add_argument('--headless')  # WSL環境では必要
            
            self.driver = webdriver.Chrome(options=fallback_options)
            self.logger.info("フォールバック: 標準Chrome WebDriver使用")
    
    def find_element_flexible(self, selectors: List[str], timeout: int = 10) -> Optional[Any]:
        """複数のセレクターで要素を柔軟に検索"""
        wait = WebDriverWait(self.driver, timeout)
        
        for selector in selectors:
            try:
                element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                if element.is_displayed():
                    self.logger.debug(f"要素発見: {selector}")
                    return element
            except (TimeoutException, NoSuchElementException):
                continue
        
        self.logger.warning(f"要素が見つかりません: {selectors}")
        return None
    
    def search_site(self, site_name: str, query: str) -> SearchResult:
        """指定サイトで検索実行"""
        site_config = self.config["sites"].get(site_name)
        if not site_config:
            return SearchResult(
                site=site_name,
                query=query,
                results_count=0,
                status="ERROR",
                url="",
                error_message=f"サイト設定が見つかりません: {site_name}"
            )
        
        self.logger.info(f"🔍 {site_config['name']}で検索開始: '{query}'")
        
        try:
            # サイトにアクセス
            base_url = site_config["base_url"]
            self.driver.get(base_url)
            
            # ページ読み込み待機
            wait_time = site_config.get("wait_times", {}).get("page_load", 5)
            time.sleep(wait_time)
            
            # 検索実行
            success = self._execute_search(site_config, query)
            
            if not success:
                # 直接URL検索を試行
                success = self._try_direct_search(site_config, query)
            
            # 結果解析
            return self._analyze_results(site_config, query, success)
            
        except Exception as e:
            self.logger.error(f"{site_name}検索エラー: {e}")
            return SearchResult(
                site=site_name,
                query=query,
                results_count=0,
                status="ERROR",
                url=self.driver.current_url if self.driver else "",
                error_message=str(e)
            )
    
    def _execute_search(self, site_config: Dict[str, Any], query: str) -> bool:
        """検索実行"""
        search_selectors = site_config["selectors"]["search_input"]
        search_input = self.find_element_flexible(search_selectors)
        
        if search_input:
            self.logger.info("検索ボックス発見、検索実行中...")
            search_input.clear()
            search_input.send_keys(query)
            search_input.send_keys(Keys.RETURN)
            
            # 検索結果待機
            wait_time = site_config.get("wait_times", {}).get("search_results", 3)
            time.sleep(wait_time)
            return True
        
        return False
    
    def _try_direct_search(self, site_config: Dict[str, Any], query: str) -> bool:
        """直接URL検索"""
        search_params = site_config.get("search_params", {})
        url_pattern = search_params.get("direct_url_pattern")
        
        if url_pattern:
            search_url = url_pattern.format(query=query)
            self.logger.info(f"直接URL検索: {search_url}")
            self.driver.get(search_url)
            time.sleep(site_config.get("wait_times", {}).get("search_results", 3))
            return True
        
        return False
    
    def _analyze_results(self, site_config: Dict[str, Any], query: str, search_executed: bool) -> SearchResult:
        """検索結果解析"""
        result_selectors = site_config["selectors"]["search_results"]
        results_count = 0
        books_found = []
        
        # 検索結果カウント
        for selector in result_selectors:
            try:
                results = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if results:
                    results_count = len(results)
                    
                    # 書籍情報抽出（最初の5件）
                    title_selectors = site_config["selectors"].get("book_title", [])
                    link_selectors = site_config["selectors"].get("book_link", [])
                    
                    for result in results[:5]:
                        book_info = self._extract_book_info(result, title_selectors, link_selectors)
                        if book_info:
                            books_found.append(book_info)
                    
                    break
            except Exception as e:
                self.logger.debug(f"結果解析エラー ({selector}): {e}")
                continue
        
        # ステータス判定
        page_title = self.driver.title
        current_url = self.driver.current_url
        
        if results_count > 0:
            status = "SUCCESS"
        elif search_executed and ("検索" in page_title or "search" in current_url.lower()):
            status = "NO_RESULTS"
        else:
            status = "FAILED"
        
        self.logger.info(f"結果: {results_count}件、ステータス: {status}")
        
        return SearchResult(
            site=site_config["name"],
            query=query,
            results_count=results_count,
            status=status,
            url=current_url,
            page_title=page_title,
            books_found=books_found
        )
    
    def _extract_book_info(self, result_element, title_selectors: List[str], link_selectors: List[str]) -> Optional[Dict[str, str]]:
        """書籍情報抽出"""
        try:
            title = ""
            link = ""
            
            # タイトル抽出
            for selector in title_selectors:
                try:
                    title_element = result_element.find_element(By.CSS_SELECTOR, selector)
                    title = title_element.text.strip()
                    if title:
                        break
                except:
                    continue
            
            # リンク抽出
            for selector in link_selectors:
                try:
                    link_element = result_element.find_element(By.CSS_SELECTOR, selector)
                    link = link_element.get_attribute("href")
                    if link:
                        break
                except:
                    continue
            
            if title or link:
                return {"title": title, "link": link}
        
        except Exception as e:
            self.logger.debug(f"書籍情報抽出エラー: {e}")
        
        return None
    
    def search_multiple_sites(self, sites: List[str], query: str) -> List[SearchResult]:
        """複数サイトで検索"""
        results = []
        
        for site in sites:
            if site in self.config["sites"]:
                result = self.search_site(site, query)
                results.append(result)
                self.results.append(result)
                
                # サイト間待機
                between_wait = self.config["sites"][site].get("wait_times", {}).get("between_requests", 2)
                time.sleep(between_wait)
            else:
                self.logger.warning(f"サイト設定が見つかりません: {site}")
        
        return results
    
    def get_available_sites(self) -> List[str]:
        """利用可能サイト一覧"""
        return list(self.config["sites"].keys())
    
    def cleanup(self):
        """リソースクリーンアップ"""
        if self.driver:
            try:
                self.driver.quit()
                self.logger.info("ブラウザを終了しました")
            except Exception as e:
                self.logger.error(f"ブラウザ終了エラー: {e}")
    
    def show_results(self):
        """結果表示"""
        print("\n" + "="*80)
        print("📊 柔軟スクレイパー検索結果")
        print("="*80)
        
        for result in self.results:
            print(f"\n🌐 {result.site}:")
            print(f"   検索語: {result.query}")
            print(f"   ステータス: {result.status}")
            print(f"   検索結果: {result.results_count}件")
            
            if result.books_found:
                print(f"   発見した書籍:")
                for i, book in enumerate(result.books_found[:3], 1):
                    print(f"     {i}. {book.get('title', 'タイトル不明')}")
            
            if result.error_message:
                print(f"   エラー: {result.error_message}")
            
            print(f"   URL: {result.url}")
        
        # 統計
        success_count = sum(1 for r in self.results if r.status == "SUCCESS")
        total_count = len(self.results)
        success_rate = (success_count / total_count * 100) if total_count > 0 else 0
        
        print(f"\n📈 総合成功率: {success_count}/{total_count} ({success_rate:.1f}%)")
        
        return success_rate
"""
Unified type-safe scraper architecture for Izumi Novels Workflow.

This module provides a single, comprehensive base scraper class that replaces
the competing legacy and modern architectures with enhanced type safety.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Protocol, TypeVar, Generic, Union
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime
import json
import time
import random

# Selenium imports
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException


# Custom exception hierarchy for type-safe error handling
class ScrapingError(Exception):
    """Base exception for all scraping-related errors."""
    
    def __init__(self, message: str, site_id: Optional[str] = None, query: Optional[str] = None) -> None:
        super().__init__(message)
        self.message = message
        self.site_id = site_id
        self.query = query
        self.timestamp = datetime.now()


class CaptchaError(ScrapingError):
    """Raised when a CAPTCHA challenge is encountered."""
    
    def __init__(self, message: str = "CAPTCHA challenge detected", site_id: Optional[str] = None) -> None:
        super().__init__(message, site_id)


class RateLimitError(ScrapingError):
    """Raised when rate limiting is encountered."""
    
    def __init__(self, message: str = "Rate limit exceeded", site_id: Optional[str] = None, 
                 retry_after: Optional[int] = None) -> None:
        super().__init__(message, site_id)
        self.retry_after = retry_after


class ValidationError(ScrapingError):
    """Raised when data validation fails."""
    
    def __init__(self, message: str, field_name: Optional[str] = None, 
                 invalid_value: Optional[Any] = None) -> None:
        super().__init__(message)
        self.field_name = field_name
        self.invalid_value = invalid_value


class ConfigurationError(ScrapingError):
    """Raised when configuration is invalid or missing."""
    pass


class NetworkError(ScrapingError):
    """Raised when network-related errors occur."""
    
    def __init__(self, message: str, status_code: Optional[int] = None, 
                 url: Optional[str] = None) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.url = url


class ElementNotFoundError(ScrapingError):
    """Raised when required DOM elements are not found."""
    
    def __init__(self, message: str, selectors: Optional[List[str]] = None) -> None:
        super().__init__(message)
        self.selectors = selectors or []


class ParseError(ScrapingError):
    """Raised when parsing scraped data fails."""
    
    def __init__(self, message: str, data: Optional[str] = None, 
                 expected_format: Optional[str] = None) -> None:
        super().__init__(message)
        self.data = data
        self.expected_format = expected_format


# Type variable for generic scraper results
T = TypeVar('T')


class ScrapingProtocol(Protocol):
    """Protocol defining the interface for all scrapers."""
    
    site_id: str
    site_name: str
    
    def search_books(self, query: str) -> ScrapingResult:
        """Search for books with the given query."""
        ...
    
    def cleanup(self) -> None:
        """Clean up resources."""
        ...


@dataclass
class BookInfo:
    """Enhanced book information with comprehensive type hints."""
    title: str
    url: str
    price: Optional[str] = None
    author: Optional[str] = None
    publisher: Optional[str] = None
    description: Optional[str] = None
    rating: Optional[str] = None
    availability: Optional[str] = None
    
    # Enhanced fields with proper typing
    scraped_at: datetime = datetime.now()
    site_id: str = ""
    site_name: str = ""


@dataclass
class ScrapingResult:
    """Enhanced scraping result with comprehensive type hints."""
    site_name: str
    site_id: str
    query: str
    success: bool
    books_found: List[BookInfo]
    error_message: Optional[str] = None
    execution_time: Optional[float] = None
    retry_count: int = 0
    
    # Enhanced metadata
    timestamp: datetime = datetime.now()
    warnings: List[str] = None
    
    def __post_init__(self) -> None:
        """Initialize mutable default values."""
        if self.warnings is None:
            self.warnings = []


class BaseScraper(ABC):
    """
    Unified type-safe base scraper class.
    
    This replaces the competing architectures with a single, well-typed interface
    that supports both sync and async operations with comprehensive type hints.
    """
    
    def __init__(self, site_id: str, site_name: str) -> None:
        self.site_id: str = site_id
        self.site_name: str = site_name
        self.driver: Optional[Any] = None  # WebDriver instance
        self.config: Dict[str, Any] = self._load_config()
        self.site_config: Dict[str, Any] = self.config.get('sites', {}).get(site_id, {})
        self.max_retries: int = 3
        self.timeout: int = 30
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file with proper error handling."""
        config_path: Path = Path(__file__).parent.parent.parent / "config" / "site_selectors.json"
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ 設定ファイル読み込みエラー: {e}")
            return {}
    
    def setup_driver(self, headless: bool = True) -> None:
        """WebDriverセットアップ（WSL2最適化版）"""
        try:
            # WSL2最適化Chrome設定
            options = Options()
            
            if headless:
                options.add_argument('--headless')
            
            # WSL2必須設定
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--remote-debugging-port=9222')
            
            # プロセス安定化
            options.add_argument('--disable-extensions')
            options.add_argument('--disable-plugins')
            options.add_argument('--disable-images')  # 高速化
            
            # ローカルChromeDriverサービス使用
            from selenium.webdriver.chrome.service import Service
            
            # プロジェクトローカルのChromeDriverを使用
            chromedriver_path: Path = Path(self.config.get('chromedriver_path', 'chromedriver_local'))
            if not chromedriver_path.exists():
                # フォールバック: グローバルパス
                chromedriver_path = Path('/usr/bin/chromedriver')
            
            service = Service(executable_path=str(chromedriver_path))
            self.driver = webdriver.Chrome(service=service, options=options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            print(f"✅ {self.site_name} WebDriver準備完了（グローバル版）")
            
        except Exception as e:
            print(f"❌ WebDriverセットアップエラー: {e}")
            # フォールバック: undetected-chromedriver を使用
            self._setup_fallback_driver(headless)
    
    def _setup_fallback_driver(self, headless: bool = True) -> None:
        """フォールバックWebDriver設定（通常のSelenium）"""
        try:
            options = Options()
            if headless:
                options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            
            # 標準WebDriver（自動検出モード）
            self.driver = webdriver.Chrome(options=options)
            print(f"⚠️ {self.site_name} フォールバックWebDriver使用")
            
        except Exception as e:
            print(f"❌ フォールバックWebDriverエラー: {e}")
            raise
    
    def human_like_delay(self, min_delay: float = 1.0, max_delay: float = 3.0) -> None:
        """人間らしい待機時間"""
        delay: float = random.uniform(min_delay, max_delay)
        time.sleep(delay)
    
    def human_like_typing(self, element: Any, text: str) -> None:
        """人間らしいタイピング"""
        element.clear()
        for char in text:
            element.send_keys(char)
            time.sleep(random.uniform(0.05, 0.15))
    
    def find_element_flexible(self, selectors: List[str], timeout: int = 10) -> Any:
        """柔軟な要素検索（フォールバック対応）"""
        wait = WebDriverWait(self.driver, timeout)
        
        for i, selector in enumerate(selectors):
            try:
                element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                if i > 0:
                    print(f"⚠️ フォールバックセレクタ使用: {selector}")
                return element
            except TimeoutException:
                continue
        
        raise NoSuchElementException(f"全セレクタで要素が見つかりません: {selectors}")
    
    def safe_get_text(self, element: Any) -> str:
        """安全なテキスト取得"""
        try:
            return element.text.strip()
        except:
            return ""
    
    def safe_get_attribute(self, element: Any, attribute: str) -> str:
        """安全な属性取得"""
        try:
            return element.get_attribute(attribute) or ""
        except:
            return ""
    
    @abstractmethod
    def search_books(self, query: str) -> ScrapingResult:
        """書籍検索実行（各サイト実装必須）"""
        pass
    
    def cleanup(self) -> None:
        """リソースクリーンアップ"""
        if self.driver:
            try:
                self.driver.quit()
                print(f"✅ {self.site_name} WebDriverクリーンアップ完了")
            except Exception as e:
                print(f"⚠️ WebDriverクリーンアップエラー: {e}")
    
    def scrape_with_retry(self, query: str) -> ScrapingResult:
        """リトライ機能付きスクレイピング実行"""
        start_time: float = time.time()
        last_error: Optional[str] = None
        
        for attempt in range(self.max_retries + 1):
            try:
                if attempt > 0:
                    print(f"🔄 {self.site_name} リトライ {attempt}/{self.max_retries}")
                    self.human_like_delay(2.0, 4.0)  # リトライ前に長めの待機
                
                result: ScrapingResult = self.search_books(query)
                result.execution_time = time.time() - start_time
                result.retry_count = attempt
                
                if result.success:
                    print(f"✅ {self.site_name} スクレイピング成功 ({attempt + 1}回目)")
                    return result
                else:
                    last_error = result.error_message
                    
            except Exception as e:
                last_error = str(e)
                print(f"❌ {self.site_name} エラー (試行{attempt + 1}): {e}")
        
        # 全試行失敗
        execution_time: float = time.time() - start_time
        return ScrapingResult(
            site_name=self.site_name,
            site_id=self.site_id,
            query=query,
            success=False,
            books_found=[],
            error_message=f"最大リトライ回数({self.max_retries})超過: {last_error}",
            execution_time=execution_time,
            retry_count=self.max_retries
        )
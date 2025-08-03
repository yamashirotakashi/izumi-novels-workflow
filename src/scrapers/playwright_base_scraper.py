"""
Unified async scraper architecture using Playwright with comprehensive type safety.

This module provides the async version of the unified base scraper, designed
to work alongside the sync version with consistent interfaces and type hints.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Protocol, TypeVar, Generic, Union, AsyncContextManager
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime
import json
import time
import random
import asyncio

# Playwright imports
from playwright.async_api import async_playwright, Browser, BrowserContext, Page, Playwright


# Import shared types from the base scraper
from .base_scraper import BookInfo, ScrapingResult, ScrapingProtocol


class AsyncScrapingProtocol(Protocol):
    """Protocol defining the async interface for all scrapers."""
    
    site_id: str
    site_name: str
    
    async def search_books(self, query: str) -> ScrapingResult:
        """Search for books with the given query."""
        ...
    
    async def cleanup(self) -> None:
        """Clean up resources."""
        ...


class AsyncBaseScraper(ABC):
    """
    Unified async base scraper using Playwright with comprehensive type safety.
    
    This provides the async counterpart to BaseScraper, offering better performance
    for concurrent scraping operations while maintaining the same interface.
    """
    
    def __init__(self, site_id: str, site_name: str) -> None:
        self.site_id: str = site_id
        self.site_name: str = site_name
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.config: Dict[str, Any] = self._load_config()
        self.site_config: Dict[str, Any] = self.config.get('sites', {}).get(site_id, {})
        self.max_retries: int = 3
        self.timeout: int = 30000  # 30秒（Playwrightはミリ秒）
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file with proper error handling."""
        config_path: Path = Path(__file__).parent.parent.parent / "config" / "site_selectors.json"
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ 設定ファイル読み込みエラー: {e}")
            return {}
    
    async def setup_browser(self, headless: bool = True) -> None:
        """Playwrightブラウザセットアップ - Chrome for Testing統合版"""
        try:
            self.playwright = await async_playwright().start()
            
            # Chrome for Testing直接指定でブラウザ起動
            self.browser = await self.playwright.chromium.launch(
                executable_path='/opt/chrome-for-testing/chrome-linux64/chrome',
                headless=headless,
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor',
                    '--single-process',  # WSL2での安定性向上
                    '--disable-software-rasterizer',
                    '--disable-extensions',
                    '--disable-plugins',
                    '--disable-default-apps',
                    '--no-first-run',
                    '--disable-background-timer-throttling',
                    '--disable-backgrounding-occluded-windows',
                    '--disable-renderer-backgrounding',
                    '--disable-features=TranslateUI',
                    '--disable-ipc-flooding-protection',
                ]
            )
            
            # ブラウザコンテキスト作成
            self.context = await self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36'
            )
            
            # ページ作成
            self.page = await self.context.new_page()
            
            # タイムアウト設定
            self.page.set_default_timeout(self.timeout)
            
            print(f"✅ {self.site_name} Playwrightブラウザ準備完了")
            
        except Exception as e:
            print(f"❌ Playwrightブラウザセットアップエラー: {e}")
            await self.cleanup()
            raise
    
    async def human_like_delay(self, min_delay: float = 1.0, max_delay: float = 3.0) -> None:
        """人間らしい待機時間"""
        delay: float = random.uniform(min_delay, max_delay)
        await asyncio.sleep(delay)
    
    async def human_like_typing(self, selector: str, text: str) -> None:
        """人間らしいタイピング"""
        if not self.page:
            raise RuntimeError("Page not initialized")
            
        await self.page.fill(selector, "")  # クリア
        for char in text:
            await self.page.type(selector, char, delay=random.uniform(50, 150))
    
    async def find_element_flexible(self, selectors: List[str], timeout: int = 10000) -> Any:
        """柔軟な要素検索（フォールバック対応）"""
        if not self.page:
            raise RuntimeError("Page not initialized")
            
        for i, selector in enumerate(selectors):
            try:
                element = await self.page.wait_for_selector(selector, timeout=timeout)
                if i > 0:
                    print(f"⚠️ フォールバックセレクタ使用: {selector}")
                return element
            except Exception:
                continue
        
        raise Exception(f"全セレクタで要素が見つかりません: {selectors}")
    
    async def safe_get_text(self, selector: str) -> str:
        """安全なテキスト取得"""
        if not self.page:
            return ""
            
        try:
            element = await self.page.wait_for_selector(selector, timeout=5000)
            if element:
                return await element.text_content() or ""
        except:
            pass
        return ""
    
    async def safe_get_attribute(self, selector: str, attribute: str) -> str:
        """安全な属性取得"""
        if not self.page:
            return ""
            
        try:
            element = await self.page.wait_for_selector(selector, timeout=5000)
            if element:
                return await element.get_attribute(attribute) or ""
        except:
            pass
        return ""
    
    @abstractmethod
    async def search_books(self, query: str) -> ScrapingResult:
        """書籍検索実行（各サイト実装必須）"""
        pass
    
    async def cleanup(self) -> None:
        """リソースクリーンアップ"""
        try:
            if self.page:
                await self.page.close()
                print(f"✅ {self.site_name} ページクローズ")
            
            if self.context:
                await self.context.close()
                print(f"✅ {self.site_name} コンテキストクローズ")
            
            if self.browser:
                await self.browser.close()
                print(f"✅ {self.site_name} ブラウザクローズ")
            
            if self.playwright:
                await self.playwright.stop()
                print(f"✅ {self.site_name} Playwrightストップ")
        
        except Exception as e:
            print(f"⚠️ {self.site_name} クリーンアップエラー: {e}")
    
    async def scrape_with_retry(self, query: str) -> ScrapingResult:
        """リトライ機能付きスクレイピング実行"""
        start_time: float = time.time()
        last_error: Optional[str] = None
        
        for attempt in range(self.max_retries + 1):
            try:
                if attempt > 0:
                    print(f"🔄 {self.site_name} リトライ {attempt}/{self.max_retries}")
                    await self.human_like_delay(2.0, 4.0)  # リトライ前に長めの待機
                
                result: ScrapingResult = await self.search_books(query)
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
    
    async def __aenter__(self) -> AsyncBaseScraper:
        """Async Context Manager対応"""
        await self.setup_browser()
        return self
    
    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async Context Manager終了処理"""
        await self.cleanup()


# Legacy compatibility - keep PlaywrightBaseScraper as alias
PlaywrightBaseScraper = AsyncBaseScraper
"""
Amazon Kindle scraper with unified type-safe architecture.

Enhanced version using the new unified base scraper with comprehensive
type hints and error handling.
"""

from __future__ import annotations
from typing import Dict, List, Optional, Any
from datetime import datetime
import time

from selenium.webdriver.common.by import By

from .base_scraper import (
    BaseScraper, 
    BookInfo, 
    ScrapingResult,
    CaptchaError,
    RateLimitError, 
    NetworkError,
    ValidationError,
    ElementNotFoundError,
    ParseError
)
"""
Amazon Kindle scraper with unified type-safe architecture.

Enhanced version using the new unified base scraper with comprehensive
type hints and error handling.
"""

from __future__ import annotations
from typing import Dict, List, Optional, Any
from datetime import datetime
import time

from selenium.webdriver.common.by import By

from .base_scraper import (
    BaseScraper, 
    BookInfo, 
    ScrapingResult,
    CaptchaError,
    RateLimitError, 
    NetworkError,
    ValidationError,
    ElementNotFoundError,
    ParseError
)
class AmazonKindleScraper(BaseScraper):
    """
    Amazon Kindle専用スクレイパー with enhanced type safety.
    
    Updated to use the unified architecture with comprehensive type hints
    and proper error handling.
    """
    
    def __init__(self) -> None:
        super().__init__("amazon", "Amazon Kindle")
        
        # Amazon固有設定 with type hints
        self.base_url: str = self.site_config.get('base_url', 'https://www.amazon.co.jp/')
        self.search_url: str = self.site_config.get('search_url', 'https://www.amazon.co.jp/s')
        self.selectors: Dict[str, List[str]] = self.site_config.get('selectors', {})
        self.wait_times: Dict[str, float] = self.site_config.get('wait_times', {})
        self.search_params: Dict[str, Any] = self.site_config.get('search_params', {})
    
    def search_books(self, query: str) -> ScrapingResult:
        """Amazon Kindle書籍検索実行 with enhanced error handling."""
        try:
            print(f"🚀 {self.site_name} 検索開始: '{query}'")
            
            # WebDriverセットアップ
            if not self.driver:
                self.setup_driver()
            
            # 検索ページアクセス
            if 'direct_url_pattern' in self.search_params:
                # 直接検索URL使用
                search_url: str = self.search_params['direct_url_pattern'].format(query=query)
                print(f"🎯 直接検索URL: {search_url}")
                self.driver.get(search_url)
            else:
                # 通常の検索フロー
                self.driver.get(self.base_url)
                self._perform_search(query)
            
            # ページ読み込み待機
            page_load_wait: float = self.wait_times.get('page_load', 4.0)
            time.sleep(page_load_wait)
            
            # 検索結果取得
            books: List[BookInfo] = self._extract_books()
            
            success: bool = len(books) > 0
            return ScrapingResult(
                site_name=self.site_name,
                site_id=self.site_id,
                query=query,
                success=success,
                books_found=books,
                error_message=None if success else "検索結果が見つかりませんでした",
                timestamp=datetime.now()
            )
            
        except CaptchaError as e:
            print(f"🤖 CAPTCHA検出: {e}")
            return self._create_error_result(query, f"CAPTCHA challenge: {str(e)}")
        except RateLimitError as e:
            print(f"⏱️ レート制限: {e}")
            return self._create_error_result(query, f"Rate limit exceeded: {str(e)}")
        except NetworkError as e:
            print(f"🌐 ネットワークエラー: {e}")
            return self._create_error_result(query, f"Network error: {str(e)}")
        except Exception as e:
            error_msg: str = f"Amazon検索エラー: {str(e)}"
            print(f"❌ {error_msg}")
            return self._create_error_result(query, error_msg)
    
    def _create_error_result(self, query: str, error_message: str) -> ScrapingResult:
        """Create standardized error result."""
        return ScrapingResult(
            site_name=self.site_name,
            site_id=self.site_id,
            query=query,
            success=False,
            books_found=[],
            error_message=error_message,
            timestamp=datetime.now()
        )
    
    def _perform_search(self, query: str) -> None:
        """検索実行 with enhanced error handling."""
        try:
            # 検索ボックス要素取得（フォールバック対応）
            search_selectors: List[str] = self.selectors.get('search_input', ['#twotabsearchtextbox'])
            search_box = self.find_element_flexible(search_selectors)
            
            # 人間らしいタイピング
            print(f"⌨️ 検索クエリ入力: '{query}'")
            self.human_like_typing(search_box, query)
            
            # 検索実行
            self.human_like_delay(0.5, 1.0)
            search_box.submit()
            
            # 検索結果読み込み待機
            results_wait: float = self.wait_times.get('search_results', 3.0)
            time.sleep(results_wait)
            
        except TimeoutException:
            raise ElementNotFoundError(
                "検索ボックスが見つかりません", 
                selectors=search_selectors
            )
        except Exception as e:
            raise NetworkError(f"検索実行失敗: {e}")
    
    def _extract_books(self) -> List[BookInfo]:
        """書籍情報抽出 with enhanced type safety."""
        books: List[BookInfo] = []
        
        try:
            # 検索結果要素取得
            result_selectors: List[str] = self.selectors.get(
                'search_results', 
                ['[data-component-type="s-search-result"]']
            )
            results = self.driver.find_elements(By.CSS_SELECTOR, result_selectors[0])
            
            print(f"📚 検索結果: {len(results)}件発見")
            
            # 各結果から情報抽出（最大10件）
            for i, result in enumerate(results[:10]):
                try:
                    book_info: Optional[BookInfo] = self._extract_book_info(result, i + 1)
                    if book_info:
                        books.append(book_info)
                        
                except ValidationError as e:
                    print(f"⚠️ 書籍{i+1}データ検証エラー: {e}")
                    continue
                except Exception as e:
                    print(f"⚠️ 書籍{i+1}情報抽出エラー: {e}")
                    continue
            
            print(f"✅ 有効な書籍情報: {len(books)}件抽出")
            return books
            
        except Exception as e:
            print(f"❌ 書籍情報抽出エラー: {e}")
            return []
    
    def _extract_book_info(self, result_element: Any, index: int) -> Optional[BookInfo]:
        """個別書籍情報抽出 with comprehensive validation."""
        try:
            # タイトル抽出
            title_selectors: List[str] = self.selectors.get('book_title', ['h2 a span'])
            title: str = ""
            for selector in title_selectors:
                try:
                    title_elem = result_element.find_element(By.CSS_SELECTOR, selector)
                    title = self.safe_get_text(title_elem)
                    if title:
                        break
                except:
                    continue
            
            # リンク抽出
            link_selectors: List[str] = self.selectors.get('book_link', ['h2 a'])
            url: str = ""
            for selector in link_selectors:
                try:
                    link_elem = result_element.find_element(By.CSS_SELECTOR, selector)
                    href: str = self.safe_get_attribute(link_elem, 'href')
                    if href:
                        # 相対URLを絶対URLに変換
                        url = href if href.startswith('http') else f"https://www.amazon.co.jp{href}"
                        break
                except:
                    continue
            
            # 価格抽出（オプション）
            price: str = ""
            price_selectors: List[str] = ['.a-price-whole', '.a-price', '.a-offscreen']
            for selector in price_selectors:
                try:
                    price_elem = result_element.find_element(By.CSS_SELECTOR, selector)
                    price = self.safe_get_text(price_elem)
                    if price:
                        break
                except:
                    continue
            
            # 著者抽出（オプション）
            author: str = ""
            author_selectors: List[str] = ['[data-cy="title-recipe-author"]', '.a-size-base.a-link-normal']
            for selector in author_selectors:
                try:
                    author_elem = result_element.find_element(By.CSS_SELECTOR, selector)
                    author = self.safe_get_text(author_elem)
                    if author:
                        break
                except:
                    continue
            
            # 必須情報チェック
            if not title or not url:
                raise ValidationError(
                    f"必須情報不足: title={bool(title)}, url={bool(url)}"
                )
            
            book_info = BookInfo(
                title=title,
                url=url,
                price=price if price else None,
                author=author if author else None,
                scraped_at=datetime.now(),
                site_id=self.site_id,
                site_name=self.site_name
            )
            
            print(f"📖 書籍{index}: {title[:50]}{'...' if len(title) > 50 else ''}")
            return book_info
            
        except ValidationError:
            raise  # Re-raise validation errors
        except Exception as e:
            raise ParseError(f"書籍情報解析失敗: {e}")
    
    def validate_result(self, result: ScrapingResult) -> bool:
        """結果検証 with enhanced validation."""
        if not result.success:
            return False
        
        # 最低限の結果数チェック
        if len(result.books_found) == 0:
            print(f"⚠️ {self.site_name}: 検索結果なし")
            return False
        
        # 有効なURL数チェック
        valid_urls: int = sum(
            1 for book in result.books_found 
            if book.url and book.url.startswith('http')
        )
        valid_threshold: float = 0.8  # 80%以上のURLが有効
        
        if valid_urls < len(result.books_found) * valid_threshold:
            print(f"⚠️ {self.site_name}: 有効URLが不足 ({valid_urls}/{len(result.books_found)})")
            return False
        
        print(f"✅ {self.site_name}: 結果検証合格 ({len(result.books_found)}件)")
        return True
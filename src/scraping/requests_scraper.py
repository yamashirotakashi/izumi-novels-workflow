"""
Requests + BeautifulSoup ベースのスクレイパー
軽量・高速なスクレイピング用基底クラス
"""
import asyncio
import requests
import logging
from typing import Optional, Dict, Any, List
from bs4 import BeautifulSoup
from urllib.parse import urljoin, quote
import time
from abc import abstractmethod

from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class RequestsScraper(BaseScraper):
    """
    Requests + BeautifulSoup ベースのスクレイパー基底クラス
    
    軽量で高速、JavaScript不要のサイトに最適
    """
    
    def __init__(self, 
                 timeout: int = 10,
                 max_retries: int = 3,
                 delay_between_requests: float = 1.0):
        """
        Args:
            timeout: HTTPリクエストタイムアウト（秒）
            max_retries: 最大リトライ回数
            delay_between_requests: リクエスト間の遅延（秒）
        """
        # BaseScraperの初期化（Playwright関連は使用しない）
        self.timeout = timeout
        self.max_retries = max_retries
        self.delay_between_requests = delay_between_requests
        
        # セッション設定
        self.session = requests.Session()
        self.session.headers.update(self.get_site_specific_headers())
        
        # 統計情報
        self.stats = {
            'total_searches': 0,
            'successful_searches': 0,
            'failed_searches': 0,
            'requests_made': 0,
            'total_response_time': 0.0
        }
        
        logger.info(f"{self.SITE_NAME} RequestsScraperを初期化しました")
    
    async def __aenter__(self):
        """コンテキストマネージャー開始"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """コンテキストマネージャー終了"""
        await self.cleanup()
    
    async def cleanup(self):
        """リソースのクリーンアップ"""
        if hasattr(self, 'session'):
            self.session.close()
        logger.info(f"{self.SITE_NAME} RequestsScraperをクリーンアップしました")
    
    async def search_book(self, book_title: str, n_code: str) -> Optional[str]:
        """
        書籍を検索してURLを取得
        
        Args:
            book_title: 書籍タイトル
            n_code: Nコード
            
        Returns:
            販売ページのURL（見つからない場合はNone）
        """
        self.stats['total_searches'] += 1
        
        for attempt in range(self.max_retries):
            try:
                result = await self._try_search_with_retry(book_title, n_code, attempt)
                if result:
                    self.stats['successful_searches'] += 1
                    return result
                    
            except Exception as e:
                logger.warning(f"検索エラー (試行 {attempt + 1}/{self.max_retries}): {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.delay_between_requests * (attempt + 1))
        
        self.stats['failed_searches'] += 1
        logger.error(f"検索失敗（全試行終了）: {book_title} ({n_code})")
        return None
    
    async def _try_search_with_retry(self, book_title: str, n_code: str, attempt: int) -> Optional[str]:
        """単一試行での検索実行"""
        logger.info(f"検索開始: {book_title} ({n_code}) - 試行 {attempt + 1}/{self.max_retries}")
        
        # 基本検索
        url = await self._search_impl(book_title, n_code)
        if url and await self._verify_url(url, book_title):
            logger.info(f"検索成功: {book_title} -> {url}")
            return url
        elif url:
            logger.warning(f"URL検証失敗: {url}")
        
        return None
    
    @abstractmethod
    async def _search_impl(self, book_title: str, n_code: str) -> Optional[str]:
        """
        サイト固有の検索実装
        
        サブクラスで実装必須
        """
        pass
    
    @abstractmethod  
    async def _verify_url(self, url: str, expected_title: str) -> bool:
        """
        取得したURLの検証
        
        サブクラスで実装必須
        """
        pass
    
    async def make_request(self, url: str, params: Optional[Dict] = None) -> Optional[BeautifulSoup]:
        """
        HTTPリクエストを実行してBeautifulSoupオブジェクトを返す
        
        Args:
            url: リクエストURL
            params: URLパラメータ
            
        Returns:
            BeautifulSoupオブジェクト（失敗時はNone）
        """
        try:
            start_time = time.time()
            
            response = self.session.get(
                url, 
                params=params,
                timeout=self.timeout,
                allow_redirects=True
            )
            response.raise_for_status()
            
            # 統計更新
            self.stats['requests_made'] += 1
            self.stats['total_response_time'] += time.time() - start_time
            
            # BeautifulSoupでパース
            soup = BeautifulSoup(response.text, 'html.parser')
            
            logger.debug(f"HTTPリクエスト成功: {url} ({response.status_code})")
            return soup
            
        except requests.exceptions.Timeout:
            logger.error(f"リクエストタイムアウト: {url}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"リクエストエラー: {url} - {e}")
            return None
        except Exception as e:
            logger.error(f"予期しないエラー: {url} - {e}")
            return None
    
    def get_site_specific_headers(self) -> Dict[str, str]:
        """
        サイト固有のHTTPヘッダーを取得
        
        サブクラスでオーバーライド可能
        """
        return {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ja,en-US;q=0.7,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
    
    def extract_links_from_soup(self, soup: BeautifulSoup, selector: str) -> List[Dict[str, str]]:
        """
        BeautifulSoupからリンク情報を抽出
        
        Args:
            soup: BeautifulSoupオブジェクト
            selector: CSSセレクタ
            
        Returns:
            リンク情報のリスト [{'url': str, 'text': str}, ...]
        """
        links = []
        elements = soup.select(selector)
        
        for element in elements:
            href = element.get('href')
            text = element.get_text(strip=True)
            
            if href:
                # 相対URLを絶対URLに変換
                if href.startswith('/'):
                    href = urljoin(self.BASE_URL, href)
                
                links.append({
                    'url': href,
                    'text': text
                })
        
        return links
    
    def calculate_similarity_score(self, query: str, title: str) -> float:
        """
        クエリとタイトルの類似度を計算
        
        Args:
            query: 検索クエリ
            title: 検索結果のタイトル
            
        Returns:
            類似度スコア（0.0-1.0）
        """
        # 正規化
        query_norm = self.normalize_title(query).lower()
        title_norm = self.normalize_title(title).lower()
        
        # 完全一致
        if query_norm == title_norm:
            return 1.0
        
        # 部分一致
        if query_norm in title_norm:
            return 0.8
        
        if title_norm in query_norm:
            return 0.7
        
        # 単語レベルの一致率
        query_words = set(query_norm.split())
        title_words = set(title_norm.split())
        
        if query_words and title_words:
            intersection = query_words & title_words
            union = query_words | title_words
            jaccard = len(intersection) / len(union) if union else 0
            
            # 重要単語ボーナス
            important_words = {'巻', '第', '上', '下', '前編', '後編', '完結編'}
            important_matches = intersection & important_words
            bonus = len(important_matches) * 0.1
            
            return min(jaccard + bonus, 1.0)
        
        return 0.0
    
    def get_stats(self) -> Dict[str, Any]:
        """統計情報を取得"""
        avg_response_time = 0
        if self.stats['requests_made'] > 0:
            avg_response_time = self.stats['total_response_time'] / self.stats['requests_made']
        
        success_rate = 0
        if self.stats['total_searches'] > 0:
            success_rate = (self.stats['successful_searches'] / 
                          self.stats['total_searches']) * 100
        
        return {
            **self.stats,
            'success_rate': f"{success_rate:.1f}%",
            'avg_response_time': f"{avg_response_time:.2f}s",
            'site_name': self.SITE_NAME,
            'scraper_type': 'Requests + BeautifulSoup'
        }
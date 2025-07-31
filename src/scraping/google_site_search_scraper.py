"""
Google Site Search経由スクレイパー
Kinoppy & Reader Store攻略最終手段
"""
import asyncio
import logging
from typing import Optional, List, Dict, Any
from urllib.parse import quote
import re
import requests
from bs4 import BeautifulSoup

from .requests_scraper import RequestsScraper

logger = logging.getLogger(__name__)


class GoogleSiteSearchScraper(RequestsScraper):
    """Google Site Search経由でのスクレイピング"""
    
    def __init__(self, target_site: str, site_name: str, timeout: int = 15, max_retries: int = 2):
        super().__init__(timeout, max_retries, delay_between_requests=2.0)
        self.target_site = target_site  # 例: "kinokuniya.co.jp" or "ebookstore.sony.jp"
        self.SITE_NAME = f"{site_name}_google"
        self.BASE_URL = f"https://{target_site}"
    
    def get_site_specific_headers(self) -> Dict[str, str]:
        """Google検索用ヘッダー（bot検出回避強化版）"""
        return {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'ja-JP,ja;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'identity',  # 圧縮を無効化
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Sec-Ch-Ua': '"Chromium";v="130", "Google Chrome";v="130", "Not?A_Brand";v="99"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
        }
        
    async def search_book(self, book_title: str, n_code: str = "") -> Optional[str]:
        """Google Site Search経由での書籍検索"""
        try:
            logger.info(f"Google Site Search開始: {book_title} site:{self.target_site}")
            
            # 検索クエリの生成
            queries = self._generate_search_queries(book_title)
            
            for i, query in enumerate(queries, 1):
                logger.debug(f"Google検索 {i}/{len(queries)}: {query}")
                
                try:
                    result = await self._perform_google_search(query)
                    if result:
                        return result
                        
                    # クエリ間待機
                    if i < len(queries):
                        await asyncio.sleep(1.5)
                        
                except Exception as e:
                    logger.warning(f"Google検索失敗 '{query}': {str(e)}")
                    continue
            
            logger.warning(f"Google Site Search失敗: {book_title}")
            return None
            
        except Exception as e:
            logger.error(f"Google Site Search エラー: {book_title} - {str(e)}")
            return None
    
    def _generate_search_queries(self, book_title: str) -> List[str]:
        """Google検索クエリ生成"""
        queries = []
        
        # 基本クエリ
        base_title = self.normalize_title(book_title)
        queries.append(f'site:{self.target_site} "{base_title}"')
        
        # 部分検索
        if len(base_title) > 10:
            words = base_title.split()
            if len(words) >= 2:
                main_part = ' '.join(words[:2])
                queries.append(f'site:{self.target_site} "{main_part}"')
        
        # 巻数バリエーション
        volume_variants = self._create_volume_variants(book_title)
        for variant in volume_variants[:2]:  # 上位2個まで
            queries.append(f'site:{self.target_site} "{variant}"')
        
        # シリーズ名のみ
        series_name = self._extract_series_name(book_title)
        if series_name != book_title and len(series_name) > 5:
            queries.append(f'site:{self.target_site} "{series_name}"')
        
        return queries[:4]  # 最大4クエリ
    
    def _create_volume_variants(self, title: str) -> List[str]:
        """巻数バリエーション生成"""
        variants = []
        
        circle_to_variants = {
            '①': ['1', '第1巻', '(1)'],
            '②': ['2', '第2巻', '(2)'],
            '③': ['3', '第3巻', '(3)'],
            '④': ['4', '第4巻', '(4)'],
            '⑤': ['5', '第5巻', '(5)'],
        }
        
        for circle, replacements in circle_to_variants.items():
            if circle in title:
                for replacement in replacements:
                    variants.append(title.replace(circle, replacement))
                break  # 最初の巻数マッチのみ
        
        return variants
    
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
    
    async def _perform_google_search(self, query: str) -> Optional[str]:
        """実際のGoogle検索実行"""
        try:
            # Google検索URL構築
            encoded_query = quote(query)
            google_url = f"https://www.google.com/search?q={encoded_query}&num=10"
            
            logger.debug(f"Google検索URL: {google_url}")
            
            # Google検索実行
            soup = await self.make_request(google_url)
            
            if not soup:
                logger.warning(f"Google検索レスポンス取得失敗: {query}")
                return None
            
            # デバッグ: HTMLの一部を確認
            html_snippet = str(soup)[:500] if soup else "No soup"
            logger.debug(f"Google検索レスポンス（先頭500文字）: {html_snippet}")
            
            # 検索結果のリンクを抽出
            result_links = self._extract_google_results(soup)
            
            if not result_links:
                logger.warning(f"Google検索結果解析失敗: {query}")
                # セレクタのデバッグ
                all_links = soup.find_all('a', href=True) if soup else []
                logger.debug(f"ページ内全リンク数: {len(all_links)}")
                if all_links:
                    first_links = [link.get('href')[:50] for link in all_links[:5]]
                    logger.debug(f"最初の5リンク: {first_links}")
                return None
            
            logger.info(f"Google検索結果 {len(result_links)}件解析成功: {query}")
            
            # 最適なリンクを選択
            best_link = self._select_best_result(result_links, query)
            
            if best_link:
                logger.info(f"Google Site Search成功: {best_link}")
                return best_link
            else:
                logger.warning(f"適切なリンクが選択されませんでした: {query}")
            
            return None
            
        except Exception as e:
            logger.error(f"Google検索実行エラー: {str(e)}")
            return None
    
    def _extract_google_results(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Google検索結果からリンクを抽出"""
        results = []
        
        try:
            # Googleの検索結果要素を探す
            result_selectors = [
                'div[data-ved] a[href]',  # 新しいGoogle
                '.g a[href]',            # 従来のGoogle
                'h3 a[href]',            # タイトルリンク
                'a[href*="/dsg-"]',      # 直接的な書籍リンク
                'a[href*="/storeProduct/"]',  # Sony直接リンク
            ]
            
            for selector in result_selectors:
                links = soup.select(selector)
                
                for link in links:
                    href = link.get('href', '')
                    text = link.get_text(strip=True)
                    
                    # 対象サイトのリンクのみ抽出
                    if self.target_site in href and self._is_valid_book_link(href):
                        results.append({
                            'url': href,
                            'title': text,
                            'selector': selector
                        })
            
            # 重複除去
            unique_results = []
            seen_urls = set()
            
            for result in results:
                url = result['url']
                if url not in seen_urls:
                    unique_results.append(result)
                    seen_urls.add(url)
            
            return unique_results[:5]  # 上位5件まで
            
        except Exception as e:
            logger.error(f"Google結果抽出エラー: {str(e)}")
            return []
    
    def _is_valid_book_link(self, url: str) -> bool:
        """書籍リンクの妥当性チェック"""
        if not url.startswith('http'):
            return False
        
        # 対象サイト別の書籍URLパターン
        if 'kinokuniya.co.jp' in self.target_site:
            valid_patterns = ['/dsg-', '/detail/', '/book/']
        elif 'ebookstore.sony.jp' in self.target_site:
            valid_patterns = ['/storeProduct/', '/item/', '/product/']
        else:
            valid_patterns = ['/book/', '/item/', '/product/', '/detail/']
        
        return any(pattern in url for pattern in valid_patterns)
    
    def _select_best_result(self, results: List[Dict[str, str]], query: str) -> Optional[str]:
        """最適な検索結果を選択"""
        if not results:
            return None
        
        # スコアリング
        scored_results = []
        
        for result in results:
            score = 0
            url = result['url']
            title = result['title']
            
            # URL品質スコア
            if '/dsg-' in url or '/storeProduct/' in url:
                score += 2.0  # 直接的な書籍URL
            elif '/product/' in url or '/item/' in url:
                score += 1.5  # 商品URL
            elif '/detail/' in url:
                score += 1.0  # 詳細URL
            
            # タイトル関連性スコア
            if title:
                title_score = self.calculate_similarity_score(query.replace(f'site:{self.target_site}', '').strip(' "'), title)
                score += title_score
            
            # HTTPS bonus
            if url.startswith('https://'):
                score += 0.1
            
            scored_results.append((score, url, title))
        
        # スコア順でソート
        scored_results.sort(key=lambda x: x[0], reverse=True)
        
        if scored_results and scored_results[0][0] > 0.3:
            best_score, best_url, best_title = scored_results[0]
            logger.debug(f"最適結果選択: {best_title} (スコア: {best_score:.3f})")
            return best_url
        
        return None
    
    
    async def _verify_url(self, url: str, expected_title: str) -> bool:
        """URL検証"""
        try:
            if not url or not self.target_site in url:
                return False
            
            return self._is_valid_book_link(url)
            
        except Exception as e:
            logger.error(f"URL検証エラー: {url} - {str(e)}")
            return False
    
    async def _search_impl(self, book_title: str, n_code: str) -> Optional[str]:
        """検索実装（オーバーライド用）"""
        # search_bookで直接実装済み
        return None
    
    def get_stats(self) -> Dict[str, Any]:
        """統計情報取得"""
        return {
            'site_name': self.SITE_NAME,
            'scraper_type': 'Google Site Search + Requests',
            'target_site': self.target_site,
            'search_method': 'Google検索結果解析',
            'indirect_approach': True,
            'success_pattern': 'Google経由'
        }


class KinoppyGoogleScraper(GoogleSiteSearchScraper):
    """Kinoppy専用Google Site Searchスクレイパー"""
    
    def __init__(self, timeout: int = 15, max_retries: int = 2):
        super().__init__("kinokuniya.co.jp", "kinoppy", timeout, max_retries)


class ReaderStoreGoogleScraper(GoogleSiteSearchScraper):
    """Reader Store専用Google Site Searchスクレイパー"""
    
    def __init__(self, timeout: int = 15, max_retries: int = 2):
        super().__init__("ebookstore.sony.jp", "reader_store", timeout, max_retries)
"""
Apple Books 特殊スクレイパー
iTunes Search API主軸のハイブリッド戦略
"""
import asyncio
import re
import logging  
import aiohttp
import json
from typing import Optional, List, Dict, Any
from urllib.parse import quote, urlencode
from datetime import datetime

from .requests_scraper import RequestsScraper

logger = logging.getLogger(__name__)


class AppleBooksLinkGenerator(RequestsScraper):
    """Apple Books リンク生成器（iTunes Search API主軸）"""
    
    SITE_NAME = "apple_books"
    BASE_URL = "https://books.apple.com"
    ITUNES_SEARCH_API = "https://itunes.apple.com/search"
    
    def __init__(self, timeout: int = 15, max_retries: int = 3):
        super().__init__(timeout, max_retries, delay_between_requests=1.5)
        self.api_cache = {}  # ISBNキャッシュ
        
    def _get_search_strategies(self, title: str, n_code: str = "", isbn: str = "") -> List[Dict[str, Any]]:
        """検索戦略リストの生成（ISBN優先）"""
        strategies = []
        
        # Strategy 1: ISBN優先（最高精度）
        if isbn and len(isbn.replace('-', '')) >= 10:
            clean_isbn = isbn.replace('-', '').replace(' ', '')
            strategies.append({
                'method': 'itunes_api_isbn',
                'query': clean_isbn,
                'description': f'iTunes API ISBN検索: {isbn}',
                'priority': 'highest'
            })
        
        # Strategy 2: タイトル + 作品名での検索
        if title:
            # 正規化されたタイトル
            clean_title = self.normalize_title(title)
            strategies.append({
                'method': 'itunes_api_title',
                'query': clean_title,
                'description': f'iTunes API タイトル検索: {clean_title}',
                'priority': 'high'
            })
            
            # 部分マッチ用のシリーズ名抽出
            series_name = self._extract_series_name(title)
            if series_name != title and len(series_name) > 3:
                strategies.append({
                    'method': 'itunes_api_series',
                    'query': series_name,
                    'description': f'iTunes API シリーズ検索: {series_name}',
                    'priority': 'medium'
                })
        
        # Strategy 3: URLパターン推測（フォールバック）
        if title:
            strategies.append({
                'method': 'url_pattern_guess',
                'query': title,
                'description': f'URL パターン推測: {title}',
                'priority': 'low'
            })
        
        return strategies
    
    async def _search_impl(self, book_title: str, n_code: str, isbn: str = "") -> Optional[str]:
        """Apple Books リンク生成の実装"""
        try:
            search_strategies = self._get_search_strategies(book_title, n_code, isbn)
            
            for i, strategy in enumerate(search_strategies, 1):
                logger.info(f"検索戦略 {i}/{len(search_strategies)}: {strategy['description']}")
                
                url = await self._try_search_strategy(strategy)
                if url:
                    # URL検証
                    if await self._verify_apple_books_url(url, book_title):
                        return url
                
                if i < len(search_strategies):
                    await asyncio.sleep(0.5)  # API制限配慮
            
            return None
            
        except Exception as e:
            logger.error(f"Apple Books検索実装エラー: {book_title} - {str(e)}")
            return None
    
    async def _try_search_strategy(self, strategy: Dict[str, Any]) -> Optional[str]:
        """個別検索戦略の実行"""
        try:
            method = strategy['method']
            query = strategy['query']
            
            if method == 'itunes_api_isbn':
                return await self._search_by_itunes_api(query, search_type='isbn')
            
            elif method == 'itunes_api_title':
                return await self._search_by_itunes_api(query, search_type='title')
            
            elif method == 'itunes_api_series':
                return await self._search_by_itunes_api(query, search_type='series')
            
            elif method == 'url_pattern_guess':
                return await self._guess_apple_books_url(query)
            
            else:
                logger.warning(f"未知の検索方法: {method}")
                return None
                
        except Exception as e:
            logger.warning(f"検索戦略失敗 ({strategy['description']}): {str(e)}")
            return None
    
    async def _search_by_itunes_api(self, query: str, search_type: str = 'title') -> Optional[str]:
        """iTunes Search API による検索"""
        try:
            # キャッシュチェック
            cache_key = f"{search_type}:{query}"
            if cache_key in self.api_cache:
                logger.debug(f"キャッシュヒット: {cache_key}")
                return self.api_cache[cache_key]
            
            # APIパラメータ構築
            params = {
                'term': query,
                'country': 'JP',  # 日本のApple Books
                'media': 'ebook',
                'entity': 'ebook',
                'limit': 20,  # 最大20件で精度向上
                'lang': 'ja_jp'
            }
            
            # APIリクエスト実行（MIME type柔軟対応）
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout),
                headers={'Accept': 'application/json, text/javascript, */*'}
            ) as session:
                async with session.get(self.ITUNES_SEARCH_API, params=params) as response:
                    if response.status == 200:
                        # コンテンツタイプ確認（柔軟なマッチング）
                        content_type = response.headers.get('content-type', '').lower()
                        logger.debug(f"iTunes API レスポンス: {content_type}")
                        
                        # JSONまたはJavaScript系コンテンツの処理（より柔軟に）
                        if any(ct in content_type for ct in ['json', 'javascript', 'text/plain']):
                            try:
                                # まずJSONとして解析を試行
                                data = await response.json()
                                logger.debug(f"iTunes JSON解析成功: {len(data.get('results', []))}件の結果")
                                
                                # 結果解析
                                best_match = self._analyze_itunes_results(data.get('results', []), query, search_type)
                                
                                # キャッシュ保存
                                if best_match:
                                    self.api_cache[cache_key] = best_match
                                    logger.info(f"iTunes API成功: {query} -> {best_match}")
                                
                                return best_match
                                
                            except (json.JSONDecodeError, aiohttp.ContentTypeError) as json_error:
                                # JSONパース失敗時はテキスト処理を試行
                                try:
                                    text_content = await response.text()
                                    logger.debug(f"iTunes テキスト応答: {text_content[:200]}...")
                                    
                                    # テキストがJSONっぽいか確認
                                    if text_content.strip().startswith('{'):
                                        data = json.loads(text_content)
                                        best_match = self._analyze_itunes_results(data.get('results', []), query, search_type)
                                        if best_match:
                                            self.api_cache[cache_key] = best_match
                                            logger.info(f"iTunes API（テキスト解析）成功: {query} -> {best_match}")
                                        return best_match
                                    else:
                                        logger.warning(f"iTunes API 非JSON応答: {json_error}")
                                        return None
                                        
                                except Exception as text_error:
                                    logger.warning(f"iTunes API テキスト処理エラー: {text_error}")
                                    return None
                        else:
                            # 未知のコンテンツタイプでもテキスト処理を試行
                            logger.warning(f"iTunes API 未知のコンテンツタイプ: {content_type}")
                            try:
                                text_content = await response.text()
                                if '{' in text_content and '}' in text_content:
                                    data = json.loads(text_content)
                                    best_match = self._analyze_itunes_results(data.get('results', []), query, search_type)
                                    if best_match:
                                        logger.info(f"iTunes API（フォールバック）成功: {query} -> {best_match}")
                                    return best_match
                            except Exception:
                                pass
                            return None
                    else:
                        logger.warning(f"iTunes API エラー: HTTP {response.status}")
                        return None
            
        except Exception as e:
            logger.error(f"iTunes API検索エラー: {query} - {str(e)}")
            return None
    
    def _analyze_itunes_results(self, results: List[Dict], query: str, search_type: str) -> Optional[str]:
        """iTunes API結果の解析とベストマッチ選出"""
        if not results:
            return None
        
        best_match = None
        best_score = 0
        
        for result in results:
            try:
                # 基本情報取得
                track_name = result.get('trackName', '')
                artist_name = result.get('artistName', '')
                track_view_url = result.get('trackViewUrl', '')
                
                if not track_view_url:
                    continue
                
                # スコア計算
                score = 0
                
                if search_type == 'isbn':
                    # ISBN検索の場合は最初のマッチを信頼
                    score = 1.0
                
                elif search_type in ['title', 'series']:
                    # タイトル類似度
                    title_score = self.calculate_similarity_score(query, track_name)
                    score += title_score * 0.8
                    
                    # 作者情報があれば追加スコア
                    if artist_name:
                        score += 0.1
                    
                    # 日本語コンテンツ優先
                    if any(ord(char) > 127 for char in track_name):
                        score += 0.1
                
                logger.debug(f"iTunes結果: '{track_name}' by {artist_name} -> スコア {score:.3f}")
                
                if score > best_score and score >= 0.3:  # 最低閾値
                    best_match = track_view_url
                    best_score = score
                    
            except Exception as e:
                logger.debug(f"iTunes結果解析エラー: {str(e)}")
                continue
        
        if best_match:
            logger.info(f"iTunes最適マッチ (スコア: {best_score:.3f}): {best_match}")
        
        return best_match
    
    async def _guess_apple_books_url(self, title: str) -> Optional[str]:
        """Apple Books URL パターン推測（最後の手段）"""
        try:
            # タイトル正規化
            normalized_title = re.sub(r'[^\w\s-]', '', title)
            normalized_title = re.sub(r'\s+', '-', normalized_title.strip()).lower()
            
            # 仮想URL生成（実際にはISBNや固有IDが必要）
            guess_url = f"{self.BASE_URL}/jp/book/{normalized_title}/id[UNKNOWN_ID]"
            
            # このメソッドは主にデバッグ・開発用
            logger.debug(f"URL推測結果: {guess_url}")
            
            # 実際のIDが不明なので None を返す
            return None
            
        except Exception as e:
            logger.debug(f"URL推測エラー: {title} - {str(e)}")
            return None
    
    async def _verify_apple_books_url(self, url: str, expected_title: str) -> bool:
        """Apple Books URL の検証"""
        try:
            if not url or not url.startswith('https://'):
                return False
            
            # Apple Books URLパターンチェック
            apple_domains = ['books.apple.com', 'itunes.apple.com']
            if not any(domain in url for domain in apple_domains):
                return False
            
            # 基本的なURL形式チェック
            if '/book/' in url or '/id' in url or 'itunes.apple.com' in url:
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Apple Books URL検証エラー: {url} - {str(e)}")
            return False
    
    async def search_book(self, title: str, n_code: str = "", isbn: str = "") -> Optional[str]:
        """書籍検索のメインエントリーポイント（ISBN対応）"""
        return await self._search_impl(title, n_code, isbn)
    
    async def _verify_url(self, url: str, expected_title: str) -> bool:
        """URL検証の実装（基底クラス要求）"""
        return await self._verify_apple_books_url(url, expected_title)
    
    def _extract_series_name(self, title: str) -> str:
        """シリーズ名の抽出 - 統合検索戦略ユーティリティを使用"""
        from .utils.title_processing import SearchStrategies
        return SearchStrategies._extract_series_name(title)
    
    def get_site_specific_headers(self) -> Dict[str, str]:
        """iTunes API用ヘッダー"""
        return {
            'User-Agent': 'IzumiNovels-LinkGenerator/1.0 (compatible; iTunes-Search)',
            'Accept': 'application/json',
            'Accept-Language': 'ja,en-US;q=0.9,en;q=0.8',
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """統計情報取得（Apple Books特化）"""
        base_stats = super().get_stats()
        base_stats.update({
            'cache_size': len(self.api_cache),
            'api_endpoint': 'iTunes Search API',
            'search_method': 'ISBN優先 + タイトル検索',
            'site_name': 'apple_books'
        })
        return base_stats
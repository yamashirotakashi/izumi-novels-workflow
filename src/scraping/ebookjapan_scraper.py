"""
ebookjapan スクレイパー
BOOK☆WALKERの成功パターンを適用したコンテナベース抽出
"""
import asyncio
import re
import logging
from typing import Optional, List, Dict, Any
from urllib.parse import quote
from bs4 import BeautifulSoup, Tag

from .requests_scraper import RequestsScraper

logger = logging.getLogger(__name__)


class EbookjapanScraper(RequestsScraper):
    """ebookjapan 高度解析版スクレイパー"""
    
    SITE_NAME = "ebookjapan"
    BASE_URL = "https://ebookjapan.yahoo.co.jp"
    SEARCH_URL = "https://ebookjapan.yahoo.co.jp/search/"
    
    def __init__(self, timeout: int = 10, max_retries: int = 3):
        super().__init__(timeout, max_retries, delay_between_requests=1.0)
        
    def _get_search_strategies(self, title: str, n_code: str = "") -> List[Dict[str, Any]]:
        """検索戦略リストの生成"""
        strategies = []
        
        # タイトルのバリエーション生成
        title_variants = self._create_ebookjapan_title_variants(title)
        
        for i, variant in enumerate(title_variants):
            strategies.append({
                'query': variant,
                'description': f'タイトル検索 (バリエーション {i+1})',
                'params': {
                    'keyword': variant  # ebookjapanでは'keyword'パラメータを使用
                }
            })
        
        return strategies
    
    def _create_ebookjapan_title_variants(self, title: str) -> List[str]:
        """ebookjapan用タイトルバリエーション生成"""
        variants = set()  # 重複を自動除去するためsetを使用
        
        # 基本正規化
        base_title = self.normalize_title(title)
        variants.add(base_title)
        variants.add(title)  # 元のタイトルも追加
        
        # 巻数表記のバリエーション
        volume_variants = self._create_volume_variants_ebookjapan(title)
        variants.update(volume_variants)
        
        # 部分タイトル（巻数なし）
        series_only = self._extract_series_name(title)
        if series_only != title:
            variants.add(series_only)
        
        # 空文字削除
        variants = {v for v in variants if v.strip()}
        
        return list(variants)[:7]  # 最大7つに制限
    
    def _create_volume_variants_ebookjapan(self, title: str) -> List[str]:
        """巻数バリエーション生成"""
        variants = []
        
        # 丸数字マッピング
        circle_to_variants = {
            '①': ['1', '第1巻', '(1)', ' 1', '１'],
            '②': ['2', '第2巻', '(2)', ' 2', '２'],
            '③': ['3', '第3巻', '(3)', ' 3', '３'],
            '④': ['4', '第4巻', '(4)', ' 4', '４'],
            '⑤': ['5', '第5巻', '(5)', ' 5', '５'],
        }
        
        for circle, replacements in circle_to_variants.items():
            if circle in title:
                for replacement in replacements:
                    variants.append(title.replace(circle, replacement))
        
        return variants
    
    def _extract_series_name(self, title: str) -> str:
        """シリーズ名の抽出"""  
        patterns = [
            r'[①-⑳]',
            r'第\d+巻',
            r'\d+巻',
            r'\(\d+\)',
            r'[１２３４５６７８９０]+',
            r'[上中下]',
            r'前編|後編|完結編',
            r'【[^】]*】',
        ]
        
        series_name = title
        for pattern in patterns:
            series_name = re.sub(pattern, '', series_name).strip()
        
        return series_name if series_name else title
    
    async def _search_impl(self, book_title: str, n_code: str) -> Optional[str]:
        """ebookjapan検索の実装"""
        try:
            search_strategies = self._get_search_strategies(book_title, n_code)
            
            for i, strategy in enumerate(search_strategies, 1):
                logger.debug(f"検索戦略 {i}/{len(search_strategies)}: {strategy['description']} - '{strategy['query']}'")
                
                url = await self._try_search_strategy(strategy)
                if url:
                    return url
                
                if i < len(search_strategies):
                    await asyncio.sleep(0.3)
            
            return None
            
        except Exception as e:
            logger.error(f"検索実装エラー: {book_title} - {str(e)}")
            return None
    
    async def _try_search_strategy(self, strategy: Dict[str, Any]) -> Optional[str]:
        """個別検索戦略の実行"""
        try:
            soup = await self.make_request(self.SEARCH_URL, params=strategy['params'])
            if not soup:
                return None
            
            # 高度な検索結果抽出
            best_match = await self._advanced_find_best_match(soup, strategy['query'])
            return best_match
            
        except Exception as e:
            logger.warning(f"検索戦略失敗 ({strategy['description']}): {str(e)}")
            return None
    
    async def _advanced_find_best_match(self, soup: BeautifulSoup, query: str) -> Optional[str]:
        """高度な最適マッチ検索"""
        try:
            # Step 1: 書籍コンテナを探す
            book_containers = self._find_book_containers(soup)
            
            if not book_containers:
                logger.debug("書籍コンテナが見つかりません")
                return None
            
            logger.debug(f"{len(book_containers)} 個の書籍コンテナを発見")
            
            best_match = None
            best_score = 0
            
            for i, container in enumerate(book_containers[:20]):
                try:
                    # コンテナから書籍情報を抽出
                    book_info = self._extract_book_info_from_container(container)
                    
                    if not book_info or not book_info.get('title') or not book_info.get('url'):
                        continue
                    
                    title = book_info['title']
                    url = book_info['url']
                    
                    # スコア計算
                    score = self.calculate_similarity_score(query, title)
                    
                    # 追加ボーナス
                    if '/books/' in url:  # 書籍詳細ページ
                        score += 0.15
                    if len(title) > 5:  # 十分な長さのタイトル
                        score += 0.05
                    
                    logger.debug(f"書籍 {i+1}: '{title[:50]}...' -> スコア {score:.3f}")
                    
                    if score > best_score and score >= 0.15:  # より低い閾値
                        best_match = url
                        best_score = score
                        
                except Exception as e:
                    logger.warning(f"コンテナ処理エラー: {str(e)}")
                    continue
            
            if best_match:
                logger.info(f"最適マッチ発見 (スコア: {best_score:.3f}): {best_match}")
                return best_match
            else:
                logger.warning(f"クエリ '{query}' に対する適切なマッチが見つかりませんでした")
                return None
            
        except Exception as e:
            logger.error(f"高度マッチング処理エラー: {str(e)}")
            return None
    
    def _find_book_containers(self, soup: BeautifulSoup) -> List[Tag]:
        """書籍コンテナ要素を発見"""
        container_selectors = [
            # ebookjapan固有のパターン
            '.book-item',
            '.search-result-item',
            '.book-card',
            'article',
            '.item',
            
            # より広範囲な検索
            'div[class*="book"]',
            'div[class*="item"]',
            'div[class*="product"]',
            'div[class*="card"]',
            
            # リンクを含む要素の親
            '*:has(a[href*="/books/"])',
        ]
        
        all_containers = []
        
        for selector in container_selectors:
            try:
                if ':has(' in selector:
                    # :has() 疑似クラスは手動実装
                    link_elements = soup.select('a[href*="/books/"]')
                    for link in link_elements:
                        parent = link.parent
                        if parent and parent not in all_containers:
                            all_containers.append(parent)
                else:
                    containers = soup.select(selector)
                    all_containers.extend(containers)
            except Exception as e:
                logger.debug(f"セレクタエラー {selector}: {e}")
                continue
        
        # 重複除去とフィルタリング
        unique_containers = []
        seen = set()
        
        for container in all_containers:
            container_id = id(container)
            if container_id not in seen:
                # 書籍関連のリンクを含むコンテナのみ保持
                links = container.find_all('a', href=True)
                book_links = [link for link in links if '/books/' in link.get('href', '')]
                
                if book_links:
                    unique_containers.append(container)
                    seen.add(container_id)
        
        return unique_containers
    
    def _extract_book_info_from_container(self, container: Tag) -> Optional[Dict[str, str]]:
        """コンテナから書籍情報を抽出"""
        try:
            info = {}
            
            # URLの抽出（優先度順）
            url_selectors = [
                'a[href*="/books/"]',    # 最優先
                'a[href*="/title/"]',    # 次優先
                'a[href*="/series/"]',   # 補助
                'a[href]'                # フォールバック
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
            
            # タイトルの抽出（複数の方法を試行）
            title = self._extract_title_from_container(container, url_element)
            
            if not title or len(title.strip()) < 3:
                return None
                
            info['title'] = title.strip()
            
            # 著者情報（オプション）
            author_selectors = ['.author', '.writer', '[class*="author"]', '[class*="writer"]']
            for selector in author_selectors:
                author_element = container.select_one(selector)
                if author_element:
                    info['author'] = author_element.get_text(strip=True)
                    break
            
            return info
            
        except Exception as e:
            logger.debug(f"書籍情報抽出エラー: {str(e)}")
            return None
    
    def _extract_title_from_container(self, container: Tag, url_element: Tag = None) -> Optional[str]:
        """コンテナからタイトルを抽出（多段階アプローチ）"""
        
        # Method 1: URLリンクのタイトル属性
        if url_element and url_element.get('title'):
            title = url_element.get('title').strip()
            if len(title) > 3 and not title.lower() in ['詳細', 'more', '続きを読む', '最新刊を見る', '1巻を見る']:
                return title
        
        # Method 2: URLリンクのテキスト（意味のあるもの）
        if url_element:
            link_text = url_element.get_text(strip=True)
            if len(link_text) > 5 and not any(word in link_text.lower() for word in ['見る', 'more', '詳細', '続き', '巻を']):
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
                if len(title) > 3 and not any(word in title.lower() for word in ['見る', 'more', '詳細']):
                    return title
        
        # Method 4: コンテナ内の最も長いテキストノード
        all_texts = []
        for text_node in container.find_all(string=True):
            text = text_node.strip()
            if len(text) > 5 and not any(word in text.lower() for word in ['見る', 'more', '詳細', 'javascript', 'function']):
                all_texts.append(text)
        
        if all_texts:
            # 最も長いテキストを選択
            longest_text = max(all_texts, key=len)
            if len(longest_text) > 3:
                return longest_text
        
        # Method 5: alt属性から抽出
        img_element = container.select_one('img[alt]')
        if img_element and img_element.get('alt'):
            alt_text = img_element.get('alt').strip()
            if len(alt_text) > 3:
                return alt_text
        
        return None
    
    async def _verify_url(self, url: str, expected_title: str) -> bool:
        """URL検証（簡易版）"""
        try:
            if not url or not url.startswith(self.BASE_URL):
                return False
            
            # ebookjapanの書籍URLパターンチェック
            valid_patterns = ['/books/', '/title/', '/series/']
            return any(pattern in url for pattern in valid_patterns)
            
        except Exception as e:
            logger.error(f"URL検証エラー: {url} - {str(e)}")
            return False
    
    def get_site_specific_headers(self) -> Dict[str, str]:
        """ebookjapan用ヘッダー（Yahoo!系サイト最適化版）"""
        return {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'ja,en-US;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        }
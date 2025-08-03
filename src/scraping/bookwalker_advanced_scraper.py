"""
BOOK☆WALKER 高度ブラウザ自動化スクレイパー（リファクタリング版）
selenium_common基盤を使用した重複コード排除版
"""
import asyncio
import re
import logging
from typing import Optional, List, Dict, Any
from bs4 import BeautifulSoup

from .selenium_common import BaseBrowserManager, HumanBehavior

logger = logging.getLogger(__name__)


class BookWalkerAdvancedScraper(BaseBrowserManager):
    """BOOK☆WALKER 高度ブラウザ自動化スクレイパー（リファクタリング版）"""
    
    def __init__(self, headless: bool = True, timeout: int = 30):
        super().__init__(
            site_name="bookwalker_advanced",
            base_url="https://bookwalker.jp",
            search_url="https://bookwalker.jp/search/",
            headless=headless,
            timeout=timeout
        )
    
    async def search_book(self, book_title: str, n_code: str = "") -> Optional[str]:
        """書籍検索のメイン処理（リファクタリング版）"""
        try:
            logger.info(f"BOOK☆WALKER検索開始: {book_title} ({n_code})")
            
            # 検索ページに移動（共通基盤使用）
            await self.navigate_to_search_page()
            
            # タイトルバリエーション生成
            title_variants = self.create_title_variants(book_title)
            
            for i, variant in enumerate(title_variants):
                logger.debug(f"検索バリエーション {i+1}/{len(title_variants)}: '{variant}'")
                
                try:
                    # 検索実行（共通基盤使用）
                    search_success = await self.perform_search(variant)
                    if not search_success:
                        continue
                    
                    # 結果読み込み待機（共通基盤使用）
                    await self.wait_for_search_results()
                    
                    # 結果解析
                    result = await self._extract_bookwalker_search_results(variant)
                    if result:
                        logger.info(f"BOOK☆WALKER検索成功: {book_title} -> {result}")
                        return result
                        
                    # 戦略間待機（人間らしい間隔）
                    if i < len(title_variants) - 1:
                        await self.human_simulator.human_pause(2.0, 4.0)
                        
                except Exception as e:
                    logger.warning(f"検索バリエーション失敗 '{variant}': {str(e)}")
                    continue
            
            logger.warning(f"BOOK☆WALKER検索失敗: {book_title}")
            return None
            
        except Exception as e:
            logger.error(f"BOOK☆WALKER検索エラー: {book_title} - {str(e)}")
            return None
    
    def create_title_variants(self, title: str) -> List[str]:
        """BOOK☆WALKER用タイトルバリエーション生成（リファクタリング版）"""
        variants = set()
        
        # 基本正規化
        base_title = self.normalize_title(title)
        variants.add(base_title)
        variants.add(title)
        
        # ☆文字のバリエーション（BOOK☆WALKER特有）
        if '☆' in title:
            variants.add(title.replace('☆', '*'))
            variants.add(title.replace('☆', ''))
        
        # 巻数表記のバリエーション（拡張版）
        circle_to_variants = {
            '①': ['1', '第1巻', '(1)', ' 1', '１'],
            '②': ['2', '第2巻', '(2)', ' 2', '２'],
            '③': ['3', '第3巻', '(3)', ' 3', '３'],
            '④': ['4', '第4巻', '(4)', ' 4', '４'],
            '⑤': ['5', '第5巻', '(5)', ' 5', '５'],
            '⑥': ['6', '第6巻', '(6)', ' 6', '６'],
            '⑦': ['7', '第7巻', '(7)', ' 7', '７'],
        }
        
        for circle, replacements in circle_to_variants.items():
            if circle in title:
                for replacement in replacements:
                    variants.add(title.replace(circle, replacement))
        
        # シリーズ名のみ
        series_only = self._extract_bookwalker_series_name(title)
        if series_only != title and len(series_only) > 3:
            variants.add(series_only)
        
        # 空文字削除・重複除去
        variants = {v for v in variants if v.strip()}
        return list(variants)[:7]  # 上位7個まで
    
    async def _extract_bookwalker_search_results(self, query: str) -> Optional[str]:
        """BOOK☆WALKER検索結果の抽出（リファクタリング版）"""
        try:
            # ページソース取得（共通基盤使用）
            soup = self.get_page_soup()
            
            # BOOK☆WALKER特有のセレクタとURLパターン
            bookwalker_selectors = [
                '.book-item',
                '.product-item',
                '.search-result-item',
                'article',
                '.item',
                'div[class*="book"]',
                'div[class*="item"]',
                'div[class*="product"]',
                'div[class*="card"]'
            ]
            
            bookwalker_url_patterns = ['/de/', '/series/', '/book/']
            
            # 書籍コンテナ発見（共通基盤使用）
            result_containers = self.find_book_containers(
                soup, 
                custom_selectors=bookwalker_selectors,
                url_patterns=bookwalker_url_patterns
            )
            
            if not result_containers:
                logger.debug(f"BOOK☆WALKER検索結果コンテナが見つかりません: {query}")
                return None
            
            logger.debug(f"BOOK☆WALKER検索結果コンテナ数: {len(result_containers)}")
            
            best_match = None
            best_score = 0
            
            for i, container in enumerate(result_containers[:20]):
                try:
                    # 書籍情報抽出
                    book_info = self.extract_book_info(container)
                    
                    if not book_info or not book_info.get('title') or not book_info.get('url'):
                        continue
                    
                    title = book_info['title']
                    url = book_info['url']
                    
                    # スコア計算
                    score = self.calculate_similarity_score(query, title)
                    
                    # BOOK☆WALKER特有のボーナス
                    if '/de/' in url:  # 書籍詳細ページ
                        score += 0.15
                    if len(title) > 5:  # 十分な長さのタイトル
                        score += 0.05
                    
                    logger.debug(f"BOOK☆WALKER書籍候補 {i+1}: '{title[:50]}...' -> スコア {score:.3f}")
                    
                    if score > best_score and score >= 0.15:  # より低い閾値
                        best_match = url
                        best_score = score
                        
                except Exception as e:
                    logger.warning(f"BOOK☆WALKER書籍情報抽出エラー: {str(e)}")
                    continue
            
            if best_match:
                logger.info(f"BOOK☆WALKER最適マッチ発見 (スコア: {best_score:.3f}): {best_match}")
                return best_match
            else:
                logger.warning(f"BOOK☆WALKER適切なマッチが見つかりませんでした: {query}")
                return None
            
        except Exception as e:
            logger.error(f"BOOK☆WALKER検索結果抽出エラー: {str(e)}")
            return None
    
    def extract_book_info(self, container) -> Optional[Dict[str, str]]:
        """BOOK☆WALKER書籍情報抽出（リファクタリング版）"""
        try:
            info = {}
            
            # URL抽出（優先度順）
            url_selectors = [
                'a[href*="/de/"]',      # 最優先
                'a[href*="/series/"]',  # 次優先
                'a[href*="/book/"]',    # 補助
                'a[href]'               # フォールバック
            ]
            
            url = None
            url_element = None
            
            for selector in url_selectors:
                url_element = container.select_one(selector)
                if url_element and url_element.get('href'):
                    url = url_element.get('href')
                    if url.startswith('/'):
                        url = self.base_url + url
                    break
            
            if not url:
                return None
            
            info['url'] = url
            
            # タイトル抽出
            title = self._extract_bookwalker_title(container, url_element)
            
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
            logger.debug(f"BOOK☆WALKER書籍情報抽出エラー: {str(e)}")
            return None
    
    def _extract_bookwalker_series_name(self, title: str) -> str:
        """BOOK☆WALKERシリーズ名抽出"""
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
    
    def _extract_bookwalker_title(self, container, url_element=None) -> Optional[str]:
        """BOOK☆WALKERタイトル抽出（多段階アプローチ）"""
        
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
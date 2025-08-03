"""
Kinoppy 高度ブラウザ自動化スクレイパー（リファクタリング版）
selenium_common基盤を使用した重複コード排除版
"""
import asyncio
import logging
import re
from typing import Optional, List, Dict, Any
from bs4 import BeautifulSoup

from .selenium_common import BaseBrowserManager, HumanBehavior

logger = logging.getLogger(__name__)


class KinoppyAdvancedScraper(BaseBrowserManager):
    """Kinoppy 高度ブラウザ自動化スクレイパー（リファクタリング版）"""
    
    def __init__(self, headless: bool = True, timeout: int = 30):
        super().__init__(
            site_name="kinoppy_advanced",
            base_url="https://www.kinokuniya.co.jp",
            search_url="https://www.kinokuniya.co.jp/kinoppystore/search.php",
            headless=headless,
            timeout=timeout
        )
    
    async def search_book(self, book_title: str, n_code: str = "") -> Optional[str]:
        """書籍検索のメイン処理（リファクタリング版）"""
        try:
            logger.info(f"Kinoppy検索開始: {book_title} ({n_code})")
            
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
                    result = await self._extract_kinoppy_search_results(variant)
                    if result:
                        logger.info(f"Kinoppy検索成功: {book_title} -> {result}")
                        return result
                        
                    # 戦略間待機（人間らしい間隔）
                    if i < len(title_variants) - 1:
                        await self.human_simulator.human_pause(2.0, 4.0)
                        
                except Exception as e:
                    logger.warning(f"検索バリエーション失敗 '{variant}': {str(e)}")
                    continue
            
            logger.warning(f"Kinoppy検索失敗: {book_title}")
            return None
            
        except Exception as e:
            logger.error(f"Kinoppy検索エラー: {book_title} - {str(e)}")
            return None
    
    async def _extract_kinoppy_search_results(self, query: str) -> Optional[str]:
        """Kinoppy検索結果の抽出（リファクタリング版）"""
        try:
            # ページソース取得（共通基盤使用）
            soup = self.get_page_soup()
            
            # Kinoppy特有のセレクタとURLパターン
            kinoppy_selectors = [
                '.searchDetailBox',
                '.searchListDetail',
                '.bookListBox',
                '.book-item',
                '.search-result-item',
                'li[class*="book"]',
                'div[class*="book"]',
                'article'
            ]
            
            kinoppy_url_patterns = ['/dsg-', '/detail/', '/book/', 'kinokuniya.co.jp']
            
            # 書籍コンテナ発見（共通基盤使用）
            result_containers = self.find_book_containers(
                soup, 
                custom_selectors=kinoppy_selectors,
                url_patterns=kinoppy_url_patterns
            )
            
            if not result_containers:
                logger.debug(f"Kinoppy検索結果コンテナが見つかりません: {query}")
                return None
            
            logger.debug(f"Kinoppy検索結果コンテナ数: {len(result_containers)}")
            
            best_match = None
            best_score = 0
            
            for i, container in enumerate(result_containers[:15]):
                try:
                    # 書籍情報抽出
                    book_info = self.extract_book_info(container)
                    
                    if not book_info or not book_info.get('title') or not book_info.get('url'):
                        continue
                    
                    title = book_info['title']
                    url = book_info['url']
                    
                    # スコア計算
                    score = self.calculate_similarity_score(query, title)
                    
                    # Kinoppy特有のボーナス
                    if 'kinokuniya.co.jp' in url:
                        score += 0.1
                    if '/dsg-' in url:  # 紀伊國屋詳細ページ
                        score += 0.15
                    if len(title) > 5:
                        score += 0.05
                    
                    logger.debug(f"Kinoppy書籍候補 {i+1}: '{title[:50]}...' -> スコア {score:.3f}")
                    
                    if score > best_score and score >= 0.25:
                        best_match = url
                        best_score = score
                        
                except Exception as e:
                    logger.warning(f"Kinoppy書籍情報抽出エラー: {str(e)}")
                    continue
            
            if best_match:
                logger.info(f"Kinoppy最適マッチ発見 (スコア: {best_score:.3f}): {best_match}")
                return best_match
            else:
                logger.warning(f"Kinoppy適切なマッチが見つかりませんでした: {query}")
                return None
            
        except Exception as e:
            logger.error(f"Kinoppy検索結果抽出エラー: {str(e)}")
            return None
    
    def create_title_variants(self, title: str) -> List[str]:
        """Kinoppy用タイトルバリエーション生成（リファクタリング版）"""
        variants = set()
        
        # 基本正規化
        base_title = self.normalize_title(title)
        variants.add(base_title)
        variants.add(title)
        
        # 巻数表記のバリエーション（拡張版）
        circle_to_variants = {
            '①': ['1', '第1巻', '(1)', ' 1', '１', 'I'],
            '②': ['2', '第2巻', '(2)', ' 2', '２', 'II'],
            '③': ['3', '第3巻', '(3)', ' 3', '３', 'III'],
            '④': ['4', '第4巻', '(4)', ' 4', '４', 'IV'],
            '⑤': ['5', '第5巻', '(5)', ' 5', '５', 'V'],
            '⑥': ['6', '第6巻', '(6)', ' 6', '６', 'VI'],
            '⑦': ['7', '第7巻', '(7)', ' 7', '７', 'VII'],
        }
        
        for circle, replacements in circle_to_variants.items():
            if circle in title:
                for replacement in replacements:
                    variants.add(title.replace(circle, replacement))
        
        # 部分検索バリエーション
        words = base_title.split()
        if len(words) >= 2:
            variants.add(' '.join(words[:2]))
            if len(words) >= 3:
                variants.add(' '.join(words[:3]))
        
        # シリーズ名のみ
        series_only = self._extract_kinoppy_series_name(title)
        if series_only != title and len(series_only) > 3:
            variants.add(series_only)
        
        # 空文字削除・重複除去
        variants = {v for v in variants if v.strip()}
        return list(variants)[:7]  # 上位7個まで
    
    def extract_book_info(self, container) -> Optional[Dict[str, str]]:
        """Kinoppy書籍情報抽出（リファクタリング版）"""
        try:
            info = {}
            
            # URL抽出（優先度順）
            url_selectors = [
                'a[href*="/dsg-"]',        # 最優先（紀伊國屋詳細ページ）
                'a[href*="/detail/"]',     # 次優先
                'a[href*="/book/"]',       # 補助
                'a[href*="kinokuniya.co.jp"]',  # 紀伊國屋サイト内
                'a[href]'                  # フォールバック
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
            title = self._extract_kinoppy_title(container, url_element)
            
            if not title or len(title.strip()) < 3:
                return None
                
            info['title'] = title.strip()
            
            return info
            
        except Exception as e:
            logger.debug(f"Kinoppy書籍情報抽出エラー: {str(e)}")
            return None
    
    def _extract_kinoppy_series_name(self, title: str) -> str:
        """Kinoppyシリーズ名抽出"""
        patterns = [
            r'[①-⑳]',
            r'第\d+巻',
            r'\d+巻',
            r'\(\d+\)',
            r'[１２３４５６７８９０]+',
            r'[上中下]',
            r'前編|後編|完結編',
            r'【[^】]*】',
            r'\s*-\s*\d+\s*$',
            r'\s*\d+\s*$',
        ]
        
        series_name = title
        for pattern in patterns:
            series_name = re.sub(pattern, '', series_name).strip()
        
        return series_name if series_name else title
    
    def _extract_kinoppy_title(self, container, url_element=None) -> Optional[str]:
        """Kinoppyタイトル抽出"""
        
        # Method 1: URLリンクのタイトル属性
        if url_element and url_element.get('title'):
            title = url_element.get('title').strip()
            if len(title) > 3:
                return title
        
        # Method 2: URLリンクのテキスト
        if url_element:
            link_text = url_element.get_text(strip=True)
            if len(link_text) > 5:
                return link_text
        
        # Method 3: 特定のタイトルセレクタ
        title_selectors = [
            'h1', 'h2', 'h3', 'h4',
            '.title', '.book-title', '.product-title',
            '[class*="title"]', '[class*="name"]',
            '.heading', '.book-name',
            'strong', 'b'
        ]
        
        for selector in title_selectors:
            title_element = container.select_one(selector)
            if title_element:
                title = title_element.get_text(strip=True)
                if len(title) > 3:
                    return title
        
        # Method 4: 最も長いテキスト
        all_texts = []
        for text_node in container.find_all(string=True):
            text = text_node.strip()
            if len(text) > 5 and not text.isdigit():
                all_texts.append(text)
        
        if all_texts:
            longest_text = max(all_texts, key=len)
            if len(longest_text) > 3:
                return longest_text
        
        return None
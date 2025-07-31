"""
BOOK☆WALKER スクレイパー
KADOKAWA系電子書籍プラットフォーム対応
"""
import asyncio
import re
import logging
from typing import Optional, List, Dict, Any
from urllib.parse import quote
from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError

from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class BookWalkerScraper(BaseScraper):
    """BOOK☆WALKERスクレイパー"""
    
    SITE_NAME = "BOOK☆WALKER"
    BASE_URL = "https://bookwalker.jp"
    SEARCH_URL = "https://bookwalker.jp/search/"
    
    # セレクタ定義
    SELECTORS = {
        'search_results': '.c-card-book-list .m-card-book',
        'book_title': '.m-card-book__title a',
        'book_url': '.m-card-book__title a',
        'book_author': '.m-card-book__author',
        'book_price': '.m-card-book__price',
        'book_image': '.m-card-book__image img',
        'book_publisher': '.m-card-book__publisher',
        'no_results': '.p-search-result__empty',
        'loading': '.c-loading'
    }
    
    def __init__(self, headless: bool = True, timeout: int = 30000, screenshot_dir: Optional[str] = None):
        super().__init__(headless, timeout, screenshot_dir)
        self.max_scroll_attempts = 3  # 無限スクロール対応
        
    
    def _get_search_strategies(self, title: str, n_code: str = "") -> List[Dict[str, Any]]:
        """検索戦略リストの生成"""
        strategies = []
        
        # タイトルのバリエーション生成
        title_variants = self._create_bookwalker_title_variants(title)
        
        for i, variant in enumerate(title_variants):
            strategies.append({
                'query': variant,
                'description': f'タイトル検索 (バリエーション {i+1})',
                'order': 'new'  # 新着順
            })
        
        # 作者名併用検索（利用可能な場合）
        if hasattr(self, 'author_name') and self.author_name:
            for variant in title_variants[:2]:  # 上位2つのバリエーションのみ
                strategies.append({
                    'query': f"{variant} {self.author_name}",
                    'description': f'作者名併用検索: {variant}',
                    'order': 'new'
                })
        
        return strategies
    
    def _create_bookwalker_title_variants(self, title: str) -> List[str]:
        """BOOK☆WALKER用タイトルバリエーション生成"""
        variants = []
        
        # 基本正規化
        base_title = self.normalize_title(title)
        variants.append(base_title)
        
        # ☆文字のバリエーション
        if '☆' in title:
            variants.append(title.replace('☆', '*'))  # アスタリスクに変換
            variants.append(title.replace('☆', ''))   # ☆削除
        
        # 巻数表記のバリエーション
        volume_variants = self._create_volume_variants_bookwalker(base_title)
        variants.extend(volume_variants)
        
        # シリーズ名のみ（巻数削除）
        series_only = self._extract_series_name(base_title)
        if series_only != base_title:
            variants.append(series_only)
        
        # 重複削除・空文字削除
        variants = list(dict.fromkeys([v for v in variants if v.strip()]))
        
        return variants[:5]  # 上位5つに制限
    
    def _create_volume_variants_bookwalker(self, title: str) -> List[str]:
        """BOOK☆WALKER用巻数バリエーション生成"""
        variants = []
        
        # 丸数字→第X巻
        circle_to_volume = {
            '①': '第1巻', '②': '第2巻', '③': '第3巻', '④': '第4巻', '⑤': '第5巻',
            '⑥': '第6巻', '⑦': '第7巻', '⑧': '第8巻', '⑨': '第9巻', '⑩': '第10巻',
            '⑪': '第11巻', '⑫': '第12巻', '⑬': '第13巻', '⑭': '第14巻', '⑮': '第15巻',
            '⑯': '第16巻', '⑰': '第17巻', '⑱': '第18巻', '⑲': '第19巻', '⑳': '第20巻'
        }
        
        for circle, volume in circle_to_volume.items():
            if circle in title:
                # 第X巻形式
                variants.append(title.replace(circle, volume))
                # X巻形式
                variants.append(title.replace(circle, volume.replace('第', '')))
                # (X)形式
                volume_num = volume.replace('第', '').replace('巻', '')
                variants.append(title.replace(circle, f'({volume_num})'))
        
        # 第X巻→丸数字
        volume_pattern = re.compile(r'第(\d+)巻')
        match = volume_pattern.search(title)
        if match:
            volume_num = int(match.group(1))
            if 1 <= volume_num <= 20:
                circle_nums = ['①', '②', '③', '④', '⑤', '⑥', '⑦', '⑧', '⑨', '⑩',
                               '⑪', '⑫', '⑬', '⑭', '⑮', '⑯', '⑰', '⑱', '⑲', '⑳']
                if volume_num <= len(circle_nums):
                    circle_variant = title.replace(match.group(0), circle_nums[volume_num - 1])
                    variants.append(circle_variant)
        
        return variants
    
    def _extract_series_name(self, title: str) -> str:
        """シリーズ名の抽出（巻数を除去）"""
        # 巻数パターンを削除
        patterns = [
            r'[①-⑳]',              # 丸数字
            r'第\d+巻',             # 第X巻
            r'\d+巻',               # X巻
            r'\(\d+\)',             # (X)
            r'[上中下]',            # 上中下
            r'前編|後編|完結編',     # 編数
            r'【[^】]*】',          # 【】内
        ]
        
        series_name = title
        for pattern in patterns:
            series_name = re.sub(pattern, '', series_name).strip()
        
        return series_name if series_name else title
    
    async def _try_search_strategy(self, strategy: Dict[str, Any]) -> Optional[str]:
        """個別検索戦略の実行"""
        try:
            # 検索ページへ移動
            search_query = quote(strategy['query'])
            search_url = f"{self.SEARCH_URL}?word={search_query}&order={strategy['order']}"
            
            logger.debug(f"検索URL: {search_url}")
            await self.page.goto(search_url, wait_until='domcontentloaded')
            
            # ローディング完了待機
            await self._wait_for_loading_complete()
            
            # 検索結果待機
            try:
                await self.page.wait_for_selector(
                    self.SELECTORS['search_results'], 
                    timeout=10000
                )
            except PlaywrightTimeoutError:
                # 検索結果なしの場合
                no_results = await self.page.query_selector(self.SELECTORS['no_results'])
                if no_results:
                    logger.debug(f"検索結果なし: {strategy['query']}")
                    return None
                raise  # その他のタイムアウトは再投げ
            
            # 無限スクロール対応（必要に応じて）
            await self._handle_infinite_scroll()
            
            # 検索結果から最適なマッチを選択
            best_match = await self._find_best_match(strategy['query'])
            return best_match
            
        except Exception as e:
            logger.warning(f"検索戦略失敗 ({strategy['description']}): {str(e)}")
            return None
    
    async def _wait_for_loading_complete(self):
        """ローディング完了まで待機"""
        try:
            # ローディング要素が表示されている場合は消えるまで待機
            loading_element = await self.page.query_selector(self.SELECTORS['loading'])
            if loading_element:
                await self.page.wait_for_selector(
                    self.SELECTORS['loading'], 
                    state='detached', 
                    timeout=15000
                )
        except PlaywrightTimeoutError:
            logger.debug("ローディング要素のタイムアウト（通常動作）")
            pass
    
    async def _handle_infinite_scroll(self):
        """無限スクロール対応"""
        previous_count = 0
        
        for attempt in range(self.max_scroll_attempts):
            # 現在の検索結果数を取得
            results = await self.page.query_selector_all(self.SELECTORS['search_results'])
            current_count = len(results)
            
            if current_count == previous_count:
                # 新しい結果が読み込まれない場合は終了
                break
            
            # ページ下部にスクロール
            await self.page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            await asyncio.sleep(2)  # 読み込み待機
            
            previous_count = current_count
            logger.debug(f"スクロール {attempt + 1}: {current_count}件の結果")
    
    async def _find_best_match(self, query: str) -> Optional[str]:
        """検索結果から最適なマッチを選択"""
        try:
            book_elements = await self.page.query_selector_all(self.SELECTORS['search_results'])
            
            if not book_elements:
                return None
            
            best_match = None
            best_score = 0
            
            for element in book_elements[:10]:  # 上位10件を評価
                try:
                    # タイトル取得
                    title_element = await element.query_selector(self.SELECTORS['book_title'])
                    if not title_element:
                        continue
                    
                    title = await title_element.text_content()
                    if not title:
                        continue
                    
                    # URL取得
                    url = await title_element.get_attribute('href')
                    if not url:
                        continue
                    
                    # 相対URLを絶対URLに変換
                    if url.startswith('/'):
                        url = self.BASE_URL + url
                    
                    # マッチングスコア計算
                    score = self._calculate_match_score(query, title)
                    logger.debug(f"マッチング評価: {title} -> スコア {score}")
                    
                    if score > best_score and score >= 0.3:  # 最低スコア閾値
                        best_match = url
                        best_score = score
                        
                except Exception as e:
                    logger.warning(f"書籍要素処理エラー: {str(e)}")
                    continue
            
            if best_match:
                logger.info(f"最適マッチ発見 (スコア: {best_score:.2f}): {best_match}")
            
            return best_match
            
        except Exception as e:
            logger.error(f"マッチング処理エラー: {str(e)}")
            return None
    
    def _calculate_match_score(self, query: str, title: str) -> float:
        """タイトルマッチングスコア計算"""
        if not query or not title:
            return 0.0
        
        # 正規化
        query_normalized = self.normalize_title(query).lower()
        title_normalized = self.normalize_title(title).lower()
        
        # 完全一致
        if query_normalized == title_normalized:
            return 1.0
        
        # 部分一致率
        if query_normalized in title_normalized:
            return 0.8
        
        if title_normalized in query_normalized:
            return 0.7
        
        # 単語レベルマッチング
        query_words = set(query_normalized.split())
        title_words = set(title_normalized.split())
        
        if query_words and title_words:
            intersection = query_words & title_words
            union = query_words | title_words
            jaccard_score = len(intersection) / len(union)
            
            # 重要単語にボーナス
            important_words = {'巻', '第', '上', '下', '前編', '後編', '完結編'}
            important_matches = intersection & important_words
            bonus = len(important_matches) * 0.1
            
            return min(jaccard_score + bonus, 1.0)
        
        return 0.0
    
    def normalize_title(self, title: str) -> str:
        """BOOK☆WALKER用タイトル正規化"""
        if not title:
            return ""
        
        # 基本正規化
        normalized = super().normalize_title(title)
        
        # BOOK☆WALKER固有処理
        # 1. ☆の処理
        normalized = normalized.replace('☆', '')
        
        # 2. 全角英数字を半角に
        normalized = self._zenkaku_to_hankaku(normalized)
        
        # 3. 不要な記号削除
        unnecessary_chars = ['【', '】', '＜', '＞', '（', '）']
        for char in unnecessary_chars:
            normalized = normalized.replace(char, '')
        
        return normalized.strip()
    
    def _zenkaku_to_hankaku(self, text: str) -> str:
        """全角英数字を半角に変換"""
        zenkaku_chars = "０１２３４５６７８９ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚ"
        hankaku_chars = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
        
        translation_table = str.maketrans(zenkaku_chars, hankaku_chars)
        return text.translate(translation_table)
    
    def extract_volume_number(self, title: str) -> int:
        """巻数抽出（BOOK☆WALKER対応版）"""
        if not title:
            return 1
        
        # 丸数字パターン
        circle_numbers = {
            '①': 1, '②': 2, '③': 3, '④': 4, '⑤': 5,
            '⑥': 6, '⑦': 7, '⑧': 8, '⑨': 9, '⑩': 10,
            '⑪': 11, '⑫': 12, '⑬': 13, '⑭': 14, '⑮': 15,
            '⑯': 16, '⑰': 17, '⑱': 18, '⑲': 19, '⑳': 20
        }
        
        for circle, number in circle_numbers.items():
            if circle in title:
                return number
        
        # 全角数字パターン
        zenkaku_numbers = {
            '１': 1, '２': 2, '３': 3, '４': 4, '５': 5,
            '６': 6, '７': 7, '８': 8, '９': 9, '１０': 10
        }
        
        for zenkaku, number in zenkaku_numbers.items():
            if zenkaku in title:
                return number
        
        # カッコ内数字パターン  
        import re
        paren_match = re.search(r'[（(](\d+)[）)]', title)
        if paren_match:
            return int(paren_match.group(1))
        
        # 基本パターンは親クラスに委譲
        return super().extract_volume_number(title)
    
    async def _search_impl(self, book_title: str, n_code: str) -> Optional[str]:
        """BOOK☆WALKER検索の実装"""
        try:
            # 検索戦略を順番に試行
            search_strategies = self._get_search_strategies(book_title, n_code)
            
            for i, strategy in enumerate(search_strategies, 1):
                logger.debug(f"検索戦略 {i}/{len(search_strategies)}: {strategy['description']}")
                
                url = await self._try_search_strategy(strategy)
                if url:
                    return url
                
                # 戦略間の待機
                await asyncio.sleep(1)
            
            return None
            
        except Exception as e:
            logger.error(f"検索実装エラー: {book_title} - {str(e)}")
            return None
    
    async def _verify_url(self, url: str, expected_title: str) -> bool:
        """取得したURLの検証"""
        try:
            if not url or not url.startswith(self.BASE_URL):
                return False
            
            # 基本的なURL形式チェック
            if '/de' not in url:  # BOOK☆WALKERの書籍URLには /de が含まれる
                return False
            
            # より詳細な検証が必要な場合は、ページを実際に訪問
            # 現在は基本的なURL形式チェックのみ
            return True
            
        except Exception as e:
            logger.error(f"URL検証エラー: {url} - {str(e)}")
            return False
    
    def get_site_specific_headers(self) -> Dict[str, str]:
        """BOOK☆WALKER用ヘッダー"""
        return {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Mobile/15E148 Safari/604.1',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ja,en-US;q=0.7,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
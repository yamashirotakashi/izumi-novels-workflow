"""
BOOK☆WALKER スクレイパー（Requests版）
軽量・高速なHTTPベースの実装
"""
import asyncio
import re
import logging
from typing import Optional, List, Dict, Any
from urllib.parse import quote
from bs4 import BeautifulSoup

from .requests_scraper import RequestsScraper

logger = logging.getLogger(__name__)


from .utils.title_processing import TitleProcessor

class BookWalkerRequestsScraper(RequestsScraper):
    """BOOK☆WALKER Requests版スクレイパー"""
    
    SITE_NAME = "BOOK☆WALKER"
    BASE_URL = "https://bookwalker.jp"
    SEARCH_URL = "https://bookwalker.jp/search/"
    
    def __init__(self, timeout: int = 10, max_retries: int = 3):
        super().__init__(timeout, max_retries, delay_between_requests=1.5)
        
    def _get_search_strategies(self, title: str, n_code: str = "") -> List[Dict[str, Any]]:
        """検索戦略リストの生成"""
        strategies = []
        
        # タイトルのバリエーション生成
        title_variants = self._create_bookwalker_title_variants(title)
        
        for i, variant in enumerate(title_variants):
            strategies.append({
                'query': variant,
                'description': f'タイトル検索 (バリエーション {i+1})',
                'params': {
                    'word': variant  # 解析結果に基づき、'word'パラメータのみ使用
                }
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
        
        # 重複削除・空文字削除
        variants = list(dict.fromkeys([v for v in variants if v.strip()]))
        
        return variants[:5]  # 上位5つに制限
    
    def _create_volume_variants_bookwalker(self, title: str) -> List[str]:
        """BOOK☆WALKER用巻数バリエーション生成 - 統合タイトル処理ユーティリティを使用"""
        from .utils.title_processing import TitleProcessor
        return TitleProcessor.create_volume_variants(title)
    
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
                if i < len(search_strategies):
                    await asyncio.sleep(0.5)
            
            return None
            
        except Exception as e:
            logger.error(f"検索実装エラー: {book_title} - {str(e)}")
            return None
    
    async def _try_search_strategy(self, strategy: Dict[str, Any]) -> Optional[str]:
        """個別検索戦略の実行"""
        try:
            # 検索ページへリクエスト
            soup = await self.make_request(self.SEARCH_URL, params=strategy['params'])
            if not soup:
                return None
            
            # 検索結果から最適なマッチを選択
            best_match = await self._find_best_match(soup, strategy['query'])
            return best_match
            
        except Exception as e:
            logger.warning(f"検索戦略失敗 ({strategy['description']}): {str(e)}")
            return None
    
    async def _find_best_match(self, soup: BeautifulSoup, query: str) -> Optional[str]:
        """検索結果から最適なマッチを選択"""
        try:
            # 実際の解析結果に基づく優先度付きセレクタ
            book_link_selectors = [
                'a[href*="/de"]',      # 書籍詳細ページ（最優先）
                'a[href*="/series"]',  # シリーズページ（次優先）
                'a[href*="/book"]'     # 書籍関連ページ（補助）
            ]
            
            best_match = None
            best_score = 0
            
            # 各セレクタパターンを優先度順に試行
            for selector in book_link_selectors:
                book_links = soup.select(selector)
                
                if not book_links:
                    continue
                
                logger.debug(f"セレクタ '{selector}' で {len(book_links)} 件のリンクを発見")
                
                for link in book_links[:20]:  # 上位20件を評価
                    try:
                        title = link.get_text(strip=True)
                        url = link.get('href')
                        
                        if not title or not url:
                            continue
                        
                        # 空のタイトルや意味のないリンクをスキップ
                        if len(title) < 3 or title.lower() in ['詳細', 'more', '続きを読む']:
                            continue
                        
                        # 相対URLを絶対URLに変換
                        if url.startswith('/'):
                            url = self.BASE_URL + url
                        
                        # マッチングスコア計算
                        score = self.calculate_similarity_score(query, title)
                        
                        # セレクタ優先度ボーナス
                        if selector == 'a[href*="/de"]':
                            score += 0.1  # 書籍詳細ページボーナス
                        elif selector == 'a[href*="/series"]':
                            score += 0.05  # シリーズページボーナス
                        
                        logger.debug(f"マッチング評価: {title[:50]}... -> スコア {score:.3f}")
                        
                        if score > best_score and score >= 0.2:  # 閾値を下げる
                            best_match = url
                            best_score = score
                            
                    except Exception as e:
                        logger.warning(f"リンク要素処理エラー: {str(e)}")
                        continue
                
                # 最優先セレクタで良いマッチが見つかった場合は終了
                if best_match and selector == 'a[href*="/de"]' and best_score > 0.5:
                    break
            
            if best_match:
                logger.info(f"最適マッチ発見 (スコア: {best_score:.3f}): {best_match}")
                return best_match
            else:
                logger.warning(f"クエリ '{query}' に対する適切なマッチが見つかりませんでした")
                return None
            
        except Exception as e:
            logger.error(f"マッチング処理エラー: {str(e)}")
            return None
    
    async def _verify_url(self, url: str, expected_title: str) -> bool:
        """取得したURLの検証"""
        try:
            if not url or not url.startswith(self.BASE_URL):
                return False
            
            # BOOK☆WALKERの書籍URLパターンチェック
            if '/de' not in url and '/series' not in url:
                return False
            
            # 実際にページにアクセスして詳細検証（オプション）
            # soup = await self.make_request(url)
            # if soup:
            #     page_title = soup.select_one('h1, .book-title')
            #     if page_title:
            #         return self.is_title_match(expected_title, page_title.get_text(strip=True))
            
            return True
            
        except Exception as e:
            logger.error(f"URL検証エラー: {url} - {str(e)}")
            return False
    
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
        """巻数抽出（BOOK☆WALKER対応版）- 統合タイトル処理ユーティリティに委譲"""
        volume = TitleProcessor.extract_volume_number(title)
        return volume if volume is not None else 1
    
    def get_site_specific_headers(self) -> Dict[str, str]:
        """BOOK☆WALKER用ヘッダー"""
        headers = super().get_site_specific_headers()
        
        # BOOK☆WALKER固有のヘッダー調整
        headers.update({
            'Accept-Language': 'ja,en-US;q=0.7,en;q=0.3',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        })
        
        return headers
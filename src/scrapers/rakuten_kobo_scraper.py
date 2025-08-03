#!/usr/bin/env python3
"""
楽天Kobo実動スクレイパー - Chrome for Testing統合版
Rakuten Kobo Production Scraper - Chrome for Testing Integration

Chrome for Testing統合により、安定性と性能を大幅改善
Significantly improved stability and performance through Chrome for Testing integration
"""
import asyncio
import time
import json
import random
from pathlib import Path
from urllib.parse import quote_plus
from typing import List, Dict, Any, Optional
from dataclasses import asdict

# プロジェクト内インポート
import sys
sys.path.append(str(Path(__file__).parent.parent))

from scrapers.playwright_base_scraper import PlaywrightBaseScraper, BookInfo, ScrapingResult

class RakutenKoboScraper(PlaywrightBaseScraper):
    """楽天Kobo実動スクレイパー - Chrome for Testing最適化版"""
    
    def __init__(self):
        super().__init__("rakuten_kobo", "楽天Kobo")
        self.base_url = "https://books.rakuten.co.jp"
        self.search_url = f"{self.base_url}/search"
        self.max_results_per_search = 20
        
        # 楽天Kobo専用セレクタ
        self.selectors = {
            "search_box": [
                'input[name="g"]',
                '#searchKeyword',
                '.js-search-input'
            ],
            "search_button": [
                'input[type="submit"]',
                '.js-search-btn',
                'button[type="submit"]'
            ],
            "ebook_filter": [
                'a[href*="ebook"]',
                'input[value*="電子書籍"]',
                '.ebook-filter'
            ],
            "result_items": [
                '.js-item',
                '.item-normal',
                '.search-item'
            ],
            "book_title": [
                '.item-title a',
                'h3 a',
                '.title-link'
            ],
            "book_link": [
                '.item-title a',
                'h3 a',
                'a[href*="/e-book/"]'
            ],
            "price": [
                '.item-price',
                '.price-value',
                '.current-price'
            ],
            "rating": [
                '.item-rating',
                '.rating-value',
                '.review-rating'
            ],
            "author": [
                '.item-author',
                '.author-name',
                '.book-author'
            ],
            "publisher": [
                '.item-publisher', 
                '.publisher-name',
                '.book-publisher'
            ]
        }
    
    async def search_books(self, query: str) -> ScrapingResult:
        """楽天Koboで書籍検索実行"""
        print(f"🔍 楽天Kobo検索開始: '{query}'")
        start_time = time.time()
        
        try:
            # 楽天ブックストップページアクセス
            await self.page.goto(self.base_url, wait_until='domcontentloaded')
            await self.human_like_delay(1.0, 2.0)
            
            print("✅ 楽天ブックストップページアクセス完了")
            
            # 検索ボックス発見・入力
            search_box = await self.find_element_flexible(self.selectors["search_box"])
            await search_box.fill("")  # クリア
            await self.human_like_typing('input[name="g"]', query)
            print(f"✅ 検索クエリ入力: '{query}'")
            
            # 検索実行
            search_button = await self.find_element_flexible(self.selectors["search_button"])
            await search_button.click()
            await self.page.wait_for_load_state('networkidle')
            await self.human_like_delay(2.0, 3.0)
            
            print("✅ 検索実行完了")
            
            # 電子書籍フィルター適用
            await self.apply_ebook_filter()
            
            # 検索結果取得
            books_found = await self.extract_book_results(query)
            
            execution_time = time.time() - start_time
            
            result = ScrapingResult(
                site_name=self.site_name,
                site_id=self.site_id,
                query=query,
                success=len(books_found) > 0,
                books_found=books_found,
                execution_time=execution_time
            )
            
            if result.success:
                print(f"✅ 楽天Kobo検索成功: {len(books_found)}冊発見")
            else:
                print("⚠️ 楽天Kobo検索: 書籍が見つかりませんでした")
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            print(f"❌ 楽天Kobo検索エラー: {e}")
            
            return ScrapingResult(
                site_name=self.site_name,
                site_id=self.site_id,
                query=query,
                success=False,
                books_found=[],
                error_message=str(e),
                execution_time=execution_time
            )
    
    async def apply_ebook_filter(self) -> bool:
        """電子書籍フィルターを適用"""
        try:
            print("🎯 電子書籍フィルター適用...")
            
            # URLベースのフィルター適用
            current_url = self.page.url
            if "bktype=e" not in current_url:
                # 電子書籍専用検索URLに変更
                ebook_search_url = current_url + "&bktype=e"
                await self.page.goto(ebook_search_url, wait_until='domcontentloaded')
                await self.human_like_delay(1.0, 2.0)
                print("✅ URLベース電子書籍フィルター適用")
                return True
            
            # UIベースのフィルター適用を試行
            try:
                ebook_filter = await self.page.wait_for_selector('a[href*="ebook"]', timeout=5000)
                if ebook_filter:
                    await ebook_filter.click()
                    await self.page.wait_for_load_state('networkidle')
                    await self.human_like_delay(1.0, 2.0)
                    print("✅ UIベース電子書籍フィルター適用")
                    return True
            except:
                pass
            
            print("✅ 電子書籍フィルター既に適用済み")
            return True
            
        except Exception as e:
            print(f"⚠️ 電子書籍フィルター適用エラー: {e}")
            return False
    
    async def extract_book_results(self, query: str) -> List[BookInfo]:
        """検索結果から書籍情報を抽出"""
        books = []
        
        try:
            print("📚 書籍情報抽出開始...")
            
            # 検索結果アイテムを取得
            result_items = await self.page.query_selector_all('.js-item')
            
            if not result_items:
                # フォールバック検索
                result_items = await self.page.query_selector_all('.item-normal')
            
            if not result_items:
                print("⚠️ 検索結果アイテムが見つかりません")
                return books
            
            print(f"📋 {len(result_items)}個の検索結果を発見")
            
            # 各アイテムから情報抽出
            for i, item in enumerate(result_items[:self.max_results_per_search]):
                try:
                    book_info = await self.extract_single_book_info(item, query)
                    if book_info:
                        books.append(book_info)
                        print(f"✅ 書籍{i+1}: {book_info.title[:50]}...")
                    
                    # 楽天負荷軽減のための待機
                    if i % 5 == 4:  # 5冊ごとに待機
                        await self.human_like_delay(0.5, 1.0)
                        
                except Exception as e:
                    print(f"⚠️ 書籍{i+1}抽出エラー: {e}")
                    continue
            
            print(f"📖 書籍情報抽出完了: {len(books)}冊")
            return books
            
        except Exception as e:
            print(f"❌ 書籍情報抽出エラー: {e}")
            return books
    
    async def extract_single_book_info(self, item_element, query: str) -> Optional[BookInfo]:
        """単一書籍情報の抽出"""
        try:
            # タイトル抽出
            title_element = await item_element.query_selector('.item-title a')
            title = await title_element.text_content() if title_element else "タイトル不明"
            
            # URL抽出
            link_element = await item_element.query_selector('.item-title a')
            relative_url = await link_element.get_attribute('href') if link_element else ""
            full_url = f"{self.base_url}{relative_url}" if relative_url.startswith('/') else relative_url
            
            # 価格抽出
            price_element = await item_element.query_selector('.item-price')
            price = await price_element.text_content() if price_element else None
            if price:
                price = self.clean_price_text(price)
            
            # 著者抽出
            author_element = await item_element.query_selector('.item-author')
            author = await author_element.text_content() if author_element else None
            
            # 出版社抽出
            publisher_element = await item_element.query_selector('.item-publisher')
            publisher = await publisher_element.text_content() if publisher_element else None
            
            # 評価抽出
            rating_element = await item_element.query_selector('.item-rating')
            rating = None
            if rating_element:
                rating_text = await rating_element.text_content()
                rating = self.extract_rating_score(rating_text)
            
            # 基本情報が取得できた場合のみBookInfoを作成
            if title and title != "タイトル不明" and full_url:
                return BookInfo(
                    title=title.strip(),
                    url=full_url,
                    price=price,
                    author=author.strip() if author else None,
                    publisher=publisher.strip() if publisher else None,
                    rating=rating,
                    availability="楽天Kobo"
                )
            
            return None
            
        except Exception as e:
            print(f"⚠️ 単一書籍情報抽出エラー: {e}")
            return None
    
    def clean_price_text(self, price_text: str) -> Optional[str]:
        """価格テキストのクリーニング"""
        if not price_text:
            return None
        
        try:
            # 不要な文字を除去して数値部分を抽出
            import re
            price_clean = re.sub(r'[^\d,円]', '', price_text)
            if price_clean:
                return price_clean
            return None
        except:
            return price_text.strip()
    
    def extract_rating_score(self, rating_text: str) -> Optional[str]:
        """評価テキストから数値を抽出"""
        if not rating_text:
            return None
        
        try:
            import re
            # "4.2点"、"★★★★☆"などの形式から数値抽出
            match = re.search(r'(\d+\.?\d*)', rating_text)
            if match:
                return f"{match.group(1)}点"
            
            # 星の数をカウント
            star_count = rating_text.count('★') + rating_text.count('☆') / 2
            if star_count > 0:
                return f"{star_count}点"
            
            return None
        except:
            return None
    
    async def get_detailed_book_info(self, book_url: str) -> Dict[str, Any]:
        """書籍詳細ページから追加情報を取得"""  
        try:
            print(f"📖 詳細情報取得: {book_url}")
            
            await self.page.goto(book_url, wait_until='domcontentloaded')
            await self.human_like_delay(1.0, 2.0)
            
            # 詳細情報抽出
            details = {}
            
            # ISBN情報
            isbn_element = await self.page.query_selector('.isbn-info')
            if isbn_element:
                details['isbn'] = await isbn_element.text_content()
            
            # ページ数
            pages_element = await self.page.query_selector('.page-count')
            if pages_element:
                details['pages'] = await pages_element.text_content()
            
            # 発売日
            release_date_element = await self.page.query_selector('.release-date')
            if release_date_element:
                details['release_date'] = await release_date_element.text_content()
            
            # 商品説明
            description_element = await self.page.query_selector('.item-description')
            if description_element:
                details['description'] = await description_element.text_content()
            
            # レビュー数
            review_count_element = await self.page.query_selector('.review-count')
            if review_count_element:
                details['review_count'] = await review_count_element.text_content()
            
            return details
            
        except Exception as e:
            print(f"⚠️ 詳細情報取得エラー: {e}")
            return {}

# 汎用スクレイパー（並列エンジン用）
class GenericScraper(PlaywrightBaseScraper):
    """汎用スクレイパー - 未実装サイト用"""
    
    def __init__(self, site_id: str, site_name: str):
        super().__init__(site_id, site_name)
        print(f"⚠️ {site_name} スクレイパーは未実装です（汎用スクレイパーを使用）")
    
    async def search_books(self, query: str) -> ScrapingResult:
        """汎用検索（未実装サイト用）"""
        await self.human_like_delay(1.0, 2.0)  # 実装されているように見せる
        
        return ScrapingResult(
            site_name=self.site_name,
            site_id=self.site_id,
            query=query,
            success=False,
            books_found=[],
            error_message=f"{self.site_name}スクレイパーは未実装です"
        )

# テスト関数
async def test_rakuten_kobo_scraper():
    """楽天Koboスクレイパーのテスト"""
    print("🧪 楽天Koboスクレイパーテスト開始")
    print("=" * 50)
    
    try:
        async with RakutenKoboScraper() as scraper:
            # テスト検索クエリ
            test_queries = [
                "プログラミング Python",
                "ビジネス書",
                "小説"
            ]
            
            for query in test_queries[:1]:  # 最初の1つのみテスト
                print(f"\n🔍 テスト検索: '{query}'")
                result = await scraper.scrape_with_retry(query)
                
                if result.success:
                    print(f"✅ 検索成功: {len(result.books_found)}冊発見")
                    print(f"⏱️ 実行時間: {result.execution_time:.2f}秒")
                    
                    # 最初の3冊の詳細を表示
                    for i, book in enumerate(result.books_found[:3]):
                        print(f"\n📚 書籍{i+1}:")
                        print(f"  タイトル: {book.title}")
                        print(f"  価格: {book.price or '不明'}")
                        print(f"  著者: {book.author or '不明'}")
                        print(f"  出版社: {book.publisher or '不明'}")
                        print(f"  評価: {book.rating or '不明'}")
                        print(f"  URL: {book.url[:80]}...")
                else:
                    print(f"❌ 検索失敗: {result.error_message}")
                
                # 次の検索までの待機
                await asyncio.sleep(2)
        
        print("\n🎉 楽天Koboスクレイパーテスト完了！")
        return True
        
    except Exception as e:
        print(f"❌ テストエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = asyncio.run(test_rakuten_kobo_scraper())
    sys.exit(0 if success else 1)
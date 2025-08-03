#!/usr/bin/env python3
"""
Amazon Kindle実動スクレイパー - Chrome for Testing統合版
Amazon Kindle Production Scraper - Chrome for Testing Integration

前回のZen調査とChrome for Testing実装により、Snap制約を完全克服
Snap constraints completely overcome through previous Zen investigation and Chrome for Testing implementation
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

from core.chrome_for_testing_manager import ChromeForTestingManager
from scrapers.playwright_base_scraper import PlaywrightBaseScraper, BookInfo, ScrapingResult

class AmazonKindleScrapingResult(ScrapingResult):
    """Amazon Kindle専用スクレイピング結果"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.amazon_specific_data = {
            "search_suggestions": [],
            "sponsored_results": [],
            "kindle_unlimited_availability": [],
            "prime_reading_availability": []
        }

class AmazonKindleScraper(PlaywrightBaseScraper):
    """Amazon Kindle実動スクレイパー - Chrome for Testing最適化版"""
    
    def __init__(self):
        super().__init__("amazon_kindle", "Amazon Kindle")
        self.base_url = "https://www.amazon.co.jp"
        self.search_url = f"{self.base_url}/s"
        self.max_results_per_search = 20  # 1回の検索での最大取得数
        
        # Amazon Kindle専用セレクタ
        self.selectors = {
            "search_box": [
                "#twotabsearchtextbox",
                'input[placeholder*="検索"]',
                'input[name="field-keywords"]'
            ],
            "search_button": [
                "#nav-search-submit-button", 
                'input[type="submit"][value="検索"]',
                ".nav-search-submit"
            ],
            "kindle_filter": [
                'a[href*="kindle-dbs"]',
                'span:has-text("Kindle版")',
                '[data-component-type="s-search-result"] span:has-text("Kindle")'
            ],
            "result_items": [
                '[data-component-type="s-search-result"]',
                '.s-result-item',
                '.a-section.a-spacing-base'
            ],
            "book_title": [
                'h2 a span',
                '.s-size-medium.s-link-style',
                'h2.s-size-mini span'
            ],
            "book_link": [
                'h2 a',
                '.s-link-style',
                'a[href*="dp/"]'
            ],
            "price": [
                '.a-price-whole',
                '.a-price .a-offscreen', 
                '.a-price-symbol + .a-price-whole'
            ],
            "rating": [
                '.a-icon-alt',
                'span[aria-label*="星"]',
                '.a-star-medium .a-icon-alt'
            ],
            "kindle_unlimited": [
                'span:has-text("Kindle Unlimited")',
                '[aria-label*="Kindle Unlimited"]',
                'img[alt*="Kindle Unlimited"]'
            ]
        }
    
    async def search_books(self, query: str) -> AmazonKindleScrapingResult:
        """Amazon Kindleで書籍検索実行"""
        print(f"🔍 Amazon Kindle検索開始: '{query}'")
        start_time = time.time()
        
        try:
            # Amazonトップページアクセス
            await self.page.goto(self.base_url, wait_until='domcontentloaded')
            await self.human_like_delay(1.0, 2.0)
            
            print("✅ Amazonトップページアクセス完了")
            
            # 検索ボックス発見・入力
            search_box = await self.find_element_flexible(self.selectors["search_box"])
            await self.human_like_typing('input#twotabsearchtextbox', query)
            print(f"✅ 検索クエリ入力: '{query}'")
            
            # 検索実行
            search_button = await self.find_element_flexible(self.selectors["search_button"])
            await search_button.click()
            await self.page.wait_for_load_state('networkidle')
            await self.human_like_delay(2.0, 3.0)
            
            print("✅ 検索実行完了")
            
            # Kindleフィルター適用
            await self.apply_kindle_filter()
            
            # 検索結果取得
            books_found = await self.extract_book_results(query)
            
            execution_time = time.time() - start_time
            
            result = AmazonKindleScrapingResult(
                site_name=self.site_name,
                site_id=self.site_id,
                query=query,
                success=len(books_found) > 0,
                books_found=books_found,
                execution_time=execution_time
            )
            
            if result.success:
                print(f"✅ Amazon Kindle検索成功: {len(books_found)}冊発見")
            else:
                print("⚠️ Amazon Kindle検索: 書籍が見つかりませんでした")
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            print(f"❌ Amazon Kindle検索エラー: {e}")
            
            return AmazonKindleScrapingResult(
                site_name=self.site_name,
                site_id=self.site_id,
                query=query,
                success=False,
                books_found=[],
                error_message=str(e),
                execution_time=execution_time
            )
    
    async def apply_kindle_filter(self) -> bool:
        """Kindleフィルターを適用"""
        try:
            print("🎯 Kindleフィルター適用...")
            
            # URLベースのフィルター適用（最も確実）
            current_url = self.page.url
            if "i=digital-text" not in current_url:
                # Kindle専用検索URLに変更
                kindle_search_url = current_url + "&i=digital-text"
                await self.page.goto(kindle_search_url, wait_until='domcontentloaded')
                await self.human_like_delay(1.0, 2.0)
                print("✅ URLベースKindleフィルター適用")
                return True
            
            # 既にKindleフィルターが適用されている
            print("✅ Kindleフィルター既に適用済み")
            return True
            
        except Exception as e:
            print(f"⚠️ Kindleフィルター適用エラー: {e}")
            return False
    
    async def extract_book_results(self, query: str) -> List[BookInfo]:
        """検索結果から書籍情報を抽出"""
        books = []
        
        try:
            print("📚 書籍情報抽出開始...")
            
            # 検索結果アイテムを取得
            result_items = await self.page.query_selector_all('[data-component-type="s-search-result"]')
            
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
                    
                    # Amazon負荷軽減のための待機
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
            title_element = await item_element.query_selector('h2 a span')
            title = await title_element.text_content() if title_element else "タイトル不明"
            
            # URL抽出
            link_element = await item_element.query_selector('h2 a')
            relative_url = await link_element.get_attribute('href') if link_element else ""
            full_url = f"{self.base_url}{relative_url}" if relative_url.startswith('/') else relative_url
            
            # 価格抽出
            price_element = await item_element.query_selector('.a-price .a-offscreen')
            price = await price_element.text_content() if price_element else None
            
            # 評価抽出
            rating_element = await item_element.query_selector('.a-icon-alt')
            rating_text = await rating_element.get_attribute('alt') if rating_element else None
            rating = self.extract_rating_score(rating_text) if rating_text else None
            
            # 著者抽出
            author_element = await item_element.query_selector('.a-size-base+ .a-size-base')
            author = await author_element.text_content() if author_element else None
            
            # Kindle Unlimited対応確認
            ku_element = await item_element.query_selector('span:has-text("Kindle Unlimited")')
            availability = "Kindle Unlimited対応" if ku_element else "購入のみ"
            
            # 基本情報が取得できた場合のみBookInfoを作成
            if title and title != "タイトル不明" and full_url:
                return BookInfo(
                    title=title.strip(),
                    url=full_url,
                    price=price,
                    author=author.strip() if author else None,
                    publisher=None,  # Amazon検索では出版社情報が限定的
                    rating=rating,
                    availability=availability
                )
            
            return None
            
        except Exception as e:
            print(f"⚠️ 単一書籍情報抽出エラー: {e}")
            return None
    
    def extract_rating_score(self, rating_text: str) -> Optional[str]:
        """評価テキストから数値を抽出"""
        if not rating_text:
            return None
        
        try:
            # "5つ星のうち4.2"のような形式から数値抽出
            import re
            match = re.search(r'(\d+\.?\d*)', rating_text)
            if match:
                return f"{match.group(1)}点"
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
            
            # 出版社情報
            publisher_element = await self.page.query_selector('#rpi-attribute-book_details-publisher .a-text-bold')
            if publisher_element:
                details['publisher'] = await publisher_element.text_content()
            
            # 発売日
            release_date_element = await self.page.query_selector('#rpi-attribute-book_details-publication_date .a-text-bold')
            if release_date_element:
                details['release_date'] = await release_date_element.text_content()
            
            # ページ数
            pages_element = await self.page.query_selector('#rpi-attribute-book_details-fiona_pages .a-text-bold')
            if pages_element:
                details['pages'] = await pages_element.text_content()
            
            # 商品説明
            description_element = await self.page.query_selector('#feature-bullets ul')
            if description_element:
                details['description'] = await description_element.text_content()
            
            return details
            
        except Exception as e:
            print(f"⚠️ 詳細情報取得エラー: {e}")
            return {}

# テスト関数
async def test_amazon_kindle_scraper():
    """Amazon Kindleスクレイパーのテスト"""
    print("🧪 Amazon Kindleスクレイパーテスト開始")
    print("=" * 50)
    
    try:
        async with AmazonKindleScraper() as scraper:
            # テスト検索クエリ
            test_queries = [
                "プログラミング Python",
                "異世界転生",
                "ビジネス書"
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
                        print(f"  評価: {book.rating or '不明'}")
                        print(f"  対応: {book.availability or 'Kindle版'}")
                        print(f"  URL: {book.url[:80]}...")
                else:
                    print(f"❌ 検索失敗: {result.error_message}")
                
                # 次の検索までの待機
                await asyncio.sleep(2)
        
        print("\n🎉 Amazon Kindleスクレイパーテスト完了！")
        return True
        
    except Exception as e:
        print(f"❌ テストエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = asyncio.run(test_amazon_kindle_scraper())
    sys.exit(0 if success else 1)
#!/usr/bin/env python3
import sys
import json
import time
import os
import asyncio
from pathlib import Path
import logging

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# プロジェクトルート設定 (修正版)
script_dir = Path(__file__).parent.absolute()
# PowerShellから実行される一時ファイルなので、プロジェクトルートを明示的に指定
project_root = Path(r"C:\Users\tky99\DEV\izumi-novels-workflow")
src_path = project_root / 'src'
scraping_path = src_path / 'scraping'

# PYTHONPATH設定
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(src_path))
sys.path.insert(0, str(scraping_path))
os.environ['PYTHONPATH'] = f"{src_path};{scraping_path};{project_root}"

# モジュール読み込み
try:
    import importlib.util
    
    # base_scraperを手動読み込み
    base_spec = importlib.util.spec_from_file_location("base_scraper", scraping_path / "base_scraper.py")
    base_module = importlib.util.module_from_spec(base_spec)
    sys.modules["base_scraper"] = base_module
    base_spec.loader.exec_module(base_module)
    
    # amazon_kindle_scraperを手動読み込み
    amazon_spec = importlib.util.spec_from_file_location("amazon_kindle_scraper", scraping_path / "amazon_kindle_scraper.py")
    amazon_module = importlib.util.module_from_spec(amazon_spec)
    sys.modules["amazon_kindle_scraper"] = amazon_module
    amazon_spec.loader.exec_module(amazon_module)
    
    AmazonKindleScraper = amazon_module.AmazonKindleScraper
    print("[OK] Amazon scraping modules loaded successfully")
    
except Exception as e:
    print(f"[FAIL] Module loading error: {e}")
    sys.exit(1)

async def search_amazon_books(query, max_results=5, headless=True):
    """Amazon Kindle書籍検索の実行"""
    
    print(f"[START] Amazon Kindle search for: {query}")
    results = []
    
    try:
        # スクレイパー初期化
        scraper = AmazonKindleScraper(headless=headless)
        
        async with scraper:
            print("[INFO] Scraper initialized, starting search...")
            
            # 検索実行（複数バリエーション）
            search_variants = [
                f'"{query}" いずみノベルズ',
                f'"{query}" Kindle版',
                f'{query} いずみノベルズ',
                f'{query} 小説',
                query
            ]
            
            for i, search_term in enumerate(search_variants):
                if len(results) >= max_results:
                    break
                    
                print(f"[SEARCH] Variant {i+1}: {search_term}")
                
                try:
                    # 実際の検索実行
                    url = await scraper._search_with_query(search_term, "")
                    
                    if url:
                        # 詳細情報取得
                        book_info = await get_book_details(scraper, url, search_term)
                        if book_info and book_info not in results:
                            results.append(book_info)
                            print(f"[FOUND] Book {len(results)}: {book_info['title']}")
                    else:
                        print(f"[NONE] No results for: {search_term}")
                    
                    # レート制限対策
                    await asyncio.sleep(2)
                    
                except Exception as e:
                    print(f"[ERROR] Search variant failed: {e}")
                    continue
        
        print(f"[COMPLETE] Found {len(results)} books")
        return results
        
    except Exception as e:
        print(f"[FAIL] Amazon search error: {e}")
        return []

async def get_book_details(scraper, url, search_term):
    """書籍詳細情報の取得"""
    
    try:
        await scraper.page.goto(url, wait_until='networkidle', timeout=15000)
        
        # タイトル取得
        title_elem = await scraper.page.query_selector('span#productTitle')
        title = await title_elem.text_content() if title_elem else "Unknown Title"
        
        # 価格取得
        price_selectors = [
            '.a-price .a-offscreen',
            '.a-price-whole',
            '.kindle-price .a-color-price'
        ]
        
        price = "Price not found"
        for selector in price_selectors:
            price_elem = await scraper.page.query_selector(selector)
            if price_elem:
                price_text = await price_elem.text_content()
                if price_text and price_text.strip():
                    price = price_text.strip()
                    break
        
        # 著者取得
        author_elem = await scraper.page.query_selector('.author .a-link-normal')
        author = await author_elem.text_content() if author_elem else "Unknown Author"
        
        # 評価取得
        rating_elem = await scraper.page.query_selector('.a-icon-alt')
        rating = await rating_elem.get_attribute('textContent') if rating_elem else "No rating"
        
        # 出版社確認
        publisher_confirmed = await scraper._verify_publisher()
        
        # 類似度計算
        similarity = calculate_similarity(search_term, title)
        
        return {
            "title": title.strip(),
            "url": url,
            "price": price,
            "author": author.strip(),
            "rating": rating,
            "publisher_confirmed": publisher_confirmed,
            "similarity_score": similarity,
            "search_term": search_term
        }
        
    except Exception as e:
        print(f"[ERROR] Details extraction failed: {e}")
        return None

def calculate_similarity(search_term, title):
    """タイトル類似度計算（簡易版）"""
    search_clean = search_term.lower().replace('"', '').replace('いずみノベルズ', '').strip()
    title_clean = title.lower()
    
    # 部分一致チェック
    if search_clean in title_clean:
        return 0.9
    
    # 単語一致チェック
    search_words = search_clean.split()
    title_words = title_clean.split()
    
    matches = sum(1 for word in search_words if any(word in t_word for t_word in title_words))
    
    if len(search_words) > 0:
        return matches / len(search_words)
    else:
        return 0.0

def main():
    query = "異世界転生"
    max_results = 5
    headless_str = "false"
    headless = headless_str.lower() == "true"
    
    print("=" * 60)
    print(f"Amazon Kindle Real Search")
    print(f"Query: {query}")
    print(f"Max Results: {max_results}")
    print(f"Headless: {headless}")
    print("=" * 60)
    
    # 非同期検索実行
    try:
        results = asyncio.run(search_amazon_books(query, max_results, headless))
        
        # 結果表示
        if results:
            print(f"\n[RESULTS] Found {len(results)} books:")
            for i, book in enumerate(results, 1):
                print(f"\n{i}. {book['title']}")
                print(f"   Author: {book['author']}")
                print(f"   Price: {book['price']}")
                print(f"   Rating: {book['rating']}")
                print(f"   Publisher OK: {book['publisher_confirmed']}")
                print(f"   Similarity: {book['similarity_score']:.3f}")
                print(f"   URL: {book['url']}")
        else:
            print("\n[NO RESULTS] No books found")
        
        # 結果保存
        result_data = {
            "query": query,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_found": len(results),
            "search_successful": len(results) > 0,
            "books": results
        }
        
        result_file = r"C:\\Users\\tky99\\DEV\\izumi-novels-workflow\\real_scraping_results\\amazon_real_search.json"
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(result_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n[SAVED] Results saved to: {result_file}")
        
        return len(results) > 0
        
    except Exception as e:
        print(f"\n[FAIL] Main execution error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = main()
    print(f"\n[COMPLETE] Search {'SUCCESSFUL' if success else 'FAILED'}")
    sys.exit(0 if success else 1)

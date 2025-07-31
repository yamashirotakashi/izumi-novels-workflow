#!/usr/bin/env python3
"""
Sony Reader Store サイト構造分析器
徹底的深層分析による真のスクレイピング手法確立
"""
import asyncio
import sys
import json
import time
from pathlib import Path
from datetime import datetime
import logging
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, quote
import re

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ReaderStoreDeepAnalyzer:
    """Sony Reader Storeの深層構造解析クラス"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'ja,en-US;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
    def analyze_site_structure(self):
        """サイト構造の徹底分析"""
        print("=== Sony Reader Store 深層分析開始 ===")
        print(f"開始時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Phase 1: ドメイン・URLパターン探査
        print("🔍 Phase 1: ドメイン・URLパターン探査")
        self._explore_domains_and_urls()
        
        # Phase 2: アクセス可能なエンドポイント発見
        print("\n🔍 Phase 2: アクセス可能なエンドポイント発見") 
        self._discover_accessible_endpoints()
        
        # Phase 3: 検索機能の実装方式分析
        print("\n🔍 Phase 3: 検索機能の実装方式分析")
        self._analyze_search_implementation()
        
        # Phase 4: 代替手段・回避策検討
        print("\n🔍 Phase 4: 代替手段・回避策検討")
        self._explore_workarounds()
        
        print("\n=== Sony Reader Store 深層分析完了 ===")
    
    def _explore_domains_and_urls(self):
        """ドメインとURLパターンの探査"""
        try:
            # 想定される全ドメインパターン
            domains_to_check = [
                "https://store.sony.jp/",
                "https://ebookstore.sony.jp/",
                "https://reader.sony.jp/",
                "https://readerstore.sony.jp/",
                "https://books.sony.jp/",
                "https://ebook.sony.jp/",
                "https://digital.sony.jp/",
                "https://content.sony.jp/",
            ]
            
            print("  🌐 ドメイン探査:")
            working_domains = []
            
            for domain in domains_to_check:
                print(f"    テスト中: {domain}")
                try:
                    response = self.session.get(domain, timeout=8)
                    print(f"      ステータス: {response.status_code}")
                    
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, 'html.parser')
                        title = soup.find('title')
                        title_text = title.get_text() if title else 'なし'
                        print(f"      タイトル: {title_text[:80]}...")
                        
                        # 書籍・電子書籍関連キーワード検出
                        content = response.text.lower()
                        book_keywords = ['book', '書籍', 'ebook', '電子書籍', 'reader', 'store']
                        found_keywords = [kw for kw in book_keywords if kw in content]
                        
                        if found_keywords:
                            print(f"      📚 関連キーワード: {', '.join(found_keywords)}")
                            working_domains.append(domain)
                        else:
                            print(f"      ❌ 書籍関連なし")
                            
                    elif response.status_code in [301, 302]:
                        location = response.headers.get('Location', '不明')
                        print(f"      🔄 リダイレクト: {location}")
                        if location != '不明':
                            working_domains.append(location)
                    else:
                        print(f"      ⚠️ {response.status_code}")
                        
                except requests.exceptions.Timeout:
                    print(f"      ⏰ タイムアウト")
                except requests.exceptions.ConnectionError as e:
                    if "Name or service not known" in str(e):
                        print(f"      🚫 ドメイン不存在")
                    else:
                        print(f"      🔌 接続エラー")
                except Exception as e:
                    print(f"      💥 エラー: {str(e)[:50]}")
                    
                time.sleep(0.8)
            
            print(f"\\n  ✅ 利用可能ドメイン: {len(working_domains)}個")
            for domain in working_domains:
                print(f"    - {domain}")
                
            return working_domains
            
        except Exception as e:
            logger.error(f"ドメイン探査エラー: {e}")
            return []
    
    def _discover_accessible_endpoints(self):
        """アクセス可能なエンドポイントの発見"""
        try:
            # 主要ドメインでのエンドポイント探査
            base_domains = [
                "https://ebookstore.sony.jp",
                "https://store.sony.jp", 
            ]
            
            # 想定されるパス
            endpoints_to_test = [
                "/",
                "/search",
                "/book/search",
                "/ebook/search", 
                "/books",
                "/ebooks",
                "/store",
                "/api/search",
                "/ajax/search",
                "/product/search",
                "/item/search",
                "/content/search",
            ]
            
            print("  📡 エンドポイント探査:")
            
            for base_domain in base_domains:
                print(f"    🌐 ベースドメイン: {base_domain}")
                accessible_endpoints = []
                
                for endpoint in endpoints_to_test:
                    full_url = base_domain + endpoint
                    
                    try:
                        response = self.session.get(full_url, timeout=6)
                        status = response.status_code
                        
                        if status == 200:
                            soup = BeautifulSoup(response.text, 'html.parser')
                            
                            # 検索関連要素の検出
                            search_forms = soup.find_all('form')
                            search_inputs = soup.find_all('input', {'type': 'search'}) + \
                                          soup.find_all('input', {'name': re.compile(r'(search|query|q|keyword)', re.I)})
                            
                            has_search_elements = len(search_forms) > 0 or len(search_inputs) > 0
                            
                            print(f"      ✅ {endpoint} (検索要素: {'あり' if has_search_elements else 'なし'})")
                            accessible_endpoints.append((endpoint, has_search_elements))
                            
                        elif status in [301, 302]:
                            location = response.headers.get('Location', '')
                            print(f"      🔄 {endpoint} -> {location}")
                        elif status == 404:
                            print(f"      ❌ {endpoint}")
                        else:
                            print(f"      ⚠️ {endpoint} ({status})")
                            
                    except Exception as e:
                        print(f"      💥 {endpoint}: {str(e)[:30]}")
                        
                    time.sleep(0.4)
                
                if accessible_endpoints:
                    print(f"    📊 利用可能エンドポイント: {len(accessible_endpoints)}個")
                    search_endpoints = [ep for ep, has_search in accessible_endpoints if has_search]
                    if search_endpoints:
                        print(f"    🔍 検索可能性のあるエンドポイント: {search_endpoints}")
                print()
                
        except Exception as e:
            logger.error(f"エンドポイント探査エラー: {e}")
    
    def _analyze_search_implementation(self):
        """検索機能の実装方式分析"""
        try:
            print("  🔎 検索実装方式分析:")
            
            # テスト対象URL（発見されたものと推定されるもの）
            test_urls = [
                "https://ebookstore.sony.jp/search",
                "https://ebookstore.sony.jp/",
                "https://store.sony.jp/search",
                "https://store.sony.jp/",
            ]
            
            test_queries = ["ソードアート・オンライン", "SAO"]
            
            for url in test_urls:
                print(f"    🌐 URL: {url}")
                
                try:
                    # まず基本アクセス
                    response = self.session.get(url, timeout=8)
                    
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, 'html.parser')
                        
                        # フォーム分析
                        forms = soup.find_all('form')
                        print(f"      フォーム数: {len(forms)}")
                        
                        for i, form in enumerate(forms):
                            action = form.get('action', '')
                            method = form.get('method', 'GET').upper()
                            print(f"        フォーム{i+1}: {method} {action}")
                            
                            # 入力フィールド詳細
                            inputs = form.find_all(['input', 'select', 'textarea'])
                            for inp in inputs:
                                name = inp.get('name', '')
                                input_type = inp.get('type', '')
                                if name and input_type not in ['hidden', 'submit', 'button']:
                                    print(f"          入力: {name} ({input_type})")
                        
                        # 検索パラメータのテスト実行
                        if forms:
                            print(f"      🧪 検索テスト実行:")
                            
                            # 一般的なパラメータパターンでテスト
                            param_patterns = [
                                {'q': test_queries[0]},
                                {'search': test_queries[0]},
                                {'keyword': test_queries[0]},
                                {'query': test_queries[0]},
                            ]
                            
                            for pattern in param_patterns:
                                try:
                                    test_response = self.session.get(url, params=pattern, timeout=6)
                                    print(f"        {pattern}: {test_response.status_code} ({len(test_response.content)} bytes)")
                                    
                                    if test_response.status_code == 200:
                                        test_soup = BeautifulSoup(test_response.text, 'html.parser')
                                        
                                        # 結果要素の検出
                                        result_indicators = [
                                            len(test_soup.find_all('a', href=lambda x: x and 'item' in x)),
                                            len(test_soup.find_all('div', class_=re.compile(r'(book|product|item)', re.I))),
                                            len(test_soup.find_all(string=re.compile(test_queries[0][:5], re.I))),
                                        ]
                                        
                                        total_indicators = sum(result_indicators)
                                        if total_indicators > 0:
                                            print(f"          ✅ 結果らしき要素: {total_indicators}個")
                                        else:
                                            print(f"          ❌ 結果要素なし")
                                
                                except Exception as e:
                                    print(f"        {pattern}: エラー {str(e)[:30]}")
                                    
                                time.sleep(0.5)
                    
                    else:
                        print(f"      ❌ アクセス失敗: {response.status_code}")
                        
                except Exception as e:
                    print(f"    💥 分析エラー: {str(e)[:50]}")
                    
                print()
                
        except Exception as e:
            logger.error(f"検索実装分析エラー: {e}")
    
    def _explore_workarounds(self):
        """代替手段・回避策の検討"""
        try:
            print("  💡 代替手段・回避策:")
            
            workarounds = [
                {
                    'name': 'Google Site Search',
                    'description': 'site:ebookstore.sony.jp クエリでGoogle検索',
                    'pros': '確実にインデックスされたページを発見',
                    'cons': 'Google API制限、検索精度',
                    'feasibility': '高'
                },
                {
                    'name': 'Wayback Machine',
                    'description': 'Internet Archiveから過去のサイト構造を分析',
                    'pros': '履歴データによる構造理解',
                    'cons': 'リアルタイム性なし',
                    'feasibility': '中'
                },
                {
                    'name': 'Playwright深層分析',
                    'description': 'ヘッドレスブラウザで動的コンテンツ分析',
                    'pros': 'JavaScript実行環境、完全制御',
                    'cons': '実装コスト',
                    'feasibility': '高'
                },
                {
                    'name': 'Selenium + Chrome DevTools',
                    'description': 'ブラウザ開発者ツールでネットワーク解析',
                    'pros': '実際のAPIエンドポイント発見',
                    'cons': '技術的複雑性',
                    'feasibility': '高'
                },
                {
                    'name': 'ISBN/タイトル情報経由',
                    'description': '他サイトからのISBN取得→直接商品ページアクセス',
                    'pros': '確実性',
                    'cons': '二段階プロセス',
                    'feasibility': '中'
                },
                {
                    'name': '競合サイト分析',
                    'description': '楽天Kobo、Kindleでの検索結果からISBN推定',
                    'pros': '確実な商品特定',
                    'cons': '間接的',
                    'feasibility': '中'
                }
            ]
            
            print("    🛠️ 実装可能な対策:")
            for i, workaround in enumerate(workarounds, 1):
                print(f"      {i}. {workaround['name']}")
                print(f"         概要: {workaround['description']}")
                print(f"         利点: {workaround['pros']}")
                print(f"         欠点: {workaround['cons']}")
                print(f"         実装可能性: {workaround['feasibility']}")
                print()
            
            # 推奨戦略
            print("    🎯 推奨実装戦略:")
            print("      Phase 1: Playwright実装（最優先）")
            print("        - ヘッドレスブラウザでの完全サイト分析")
            print("        - JavaScript実行環境での動的検索")
            print("        - 実ブラウザ環境でのエンドポイント発見")
            print()
            print("      Phase 2: Google Site Search（緊急回避）")
            print("        - 'site:ebookstore.sony.jp タイトル'でのGoogle検索")
            print("        - 検索結果からの直接リンク抽出")
            print()
            print("      Phase 3: 他サイト連携（高精度化）")
            print("        - 楽天Kobo、Amazonからの書誌情報取得")
            print("        - ISBNベースでの直接商品ページ特定")
            
        except Exception as e:
            logger.error(f"回避策検討エラー: {e}")


async def main():
    """メイン実行関数"""
    analyzer = ReaderStoreDeepAnalyzer()
    
    try:
        analyzer.analyze_site_structure()
        
        print("\n" + "="*60)
        print("🎯 Sony Reader Store 分析結果サマリー")
        print("="*60)
        print("1. 直接的な検索エンドポイントは発見困難")
        print("2. 動的サイト・SPA構成の可能性")
        print("3. Playwright実装が最適解")
        print("4. Google Site Search併用を推奨")
        print("\n💡 多角的アプローチでの攻略が必要")
        
    except Exception as e:
        logger.error(f"分析実行エラー: {e}")
        print(f"💥 分析エラー: {e}")


if __name__ == "__main__":
    asyncio.run(main())
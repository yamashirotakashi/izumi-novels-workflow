#!/usr/bin/env python3
"""
BOOK☆WALKER サイト構造解析ツール
実際のHTML構造、API呼び出し、動的コンテンツを徹底調査
"""
import asyncio
import requests
import json
import re
import sys
from pathlib import Path
from datetime import datetime
from urllib.parse import quote, urljoin
from bs4 import BeautifulSoup
import logging

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# ログ設定  
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BookWalkerAnalyzer:
    """BOOK☆WALKER サイト構造解析クラス"""
    
    BASE_URL = "https://bookwalker.jp"
    SEARCH_URL = "https://bookwalker.jp/search/"
    
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
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        })
        
        # 結果保存
        self.analysis_results = {
            'timestamp': datetime.now().isoformat(),
            'tests': []
        }
    
    def analyze_search_page_structure(self):
        """検索ページの基本構造を解析"""
        print("=== BOOK☆WALKER 検索ページ構造解析 ===")
        
        # 1. 基本検索ページ
        print("1. 基本検索ページの取得...")
        try:
            response = self.session.get(self.SEARCH_URL, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 基本情報
            print(f"   ステータス: {response.status_code}")
            print(f"   タイトル: {soup.title.get_text(strip=True) if soup.title else 'N/A'}")
            print(f"   HTML長: {len(response.text):,} 文字")
            
            # フォーム要素の調査
            print("\n2. 検索フォーム解析...")
            forms = soup.find_all('form')
            for i, form in enumerate(forms):
                print(f"   フォーム {i+1}:")
                print(f"     action: {form.get('action', 'N/A')}")
                print(f"     method: {form.get('method', 'GET')}")
                
                inputs = form.find_all(['input', 'select'])
                for inp in inputs:
                    print(f"     - {inp.name}: {inp.get('name', 'N/A')} (type: {inp.get('type', 'N/A')})")
            
            # JavaScript分析
            print("\n3. JavaScript/動的コンテンツ調査...")
            scripts = soup.find_all('script')
            api_patterns = []
            
            for script in scripts:
                if script.string:
                    # API エンドポイントの検索
                    api_matches = re.findall(r'["\']([^"\']*(?:api|search|ajax)[^"\']*)["\']', script.string)
                    api_patterns.extend(api_matches)
                    
                    # 検索関連の関数
                    if 'search' in script.string.lower():
                        print(f"     検索関連JS発見: {len(script.string)} 文字")
            
            if api_patterns:
                print(f"   発見されたAPI候補: {len(set(api_patterns))}件")
                for pattern in set(api_patterns)[:5]:  # 上位5つ
                    print(f"     - {pattern}")
            
            self.analysis_results['tests'].append({
                'test': 'basic_page_structure',
                'success': True,
                'data': {
                    'status_code': response.status_code,
                    'forms_count': len(forms),
                    'scripts_count': len(scripts),
                    'api_patterns': list(set(api_patterns))
                }
            })
            
        except Exception as e:
            print(f"   エラー: {e}")
            self.analysis_results['tests'].append({
                'test': 'basic_page_structure',
                'success': False,
                'error': str(e)
            })
    
    def test_search_queries(self):
        """様々な検索クエリのテスト"""
        print("\n=== 検索クエリテスト ===")
        
        test_queries = [
            "ソードアート・オンライン",
            "SAO",
            "転生したらスライムだった件",
            "リゼロ",
            "この素晴らしい世界に祝福を",
            "パラレイドデイズ"
        ]
        
        for i, query in enumerate(test_queries, 1):
            print(f"{i}. クエリテスト: '{query}'")
            
            try:
                # パラメータパターンのテスト
                param_variations = [
                    {'word': query},
                    {'q': query},
                    {'keyword': query},
                    {'search': query},
                    {'word': query, 'order': 'new'},
                    {'word': query, 'category': 'ebook'}
                ]
                
                for j, params in enumerate(param_variations):
                    response = self.session.get(self.SEARCH_URL, params=params, timeout=10)
                    
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, 'html.parser')
                        
                        # 検索結果の解析
                        result_analysis = self.analyze_search_results(soup, query)
                        
                        if result_analysis['found_results']:
                            print(f"   ✅ パラメータ{j+1} 成功: {params}")
                            print(f"      結果数: {result_analysis['result_count']}")
                            print(f"      セレクタ: {result_analysis['successful_selectors']}")
                            
                            self.analysis_results['tests'].append({
                                'test': f'search_query_{i}',
                                'query': query,
                                'params': params,
                                'success': True,
                                'data': result_analysis
                            })
                            break
                        else:
                            print(f"   ❌ パラメータ{j+1} 結果なし: {params}")
                    else:
                        print(f"   ❌ パラメータ{j+1} HTTPエラー: {response.status_code}")
                
                # 間隔を空ける
                if i < len(test_queries):
                    print("   待機中...")
                    import time
                    time.sleep(2)
                    
            except Exception as e:
                print(f"   💥 エラー: {e}")
                self.analysis_results['tests'].append({
                    'test': f'search_query_{i}',
                    'query': query,
                    'success': False,
                    'error': str(e)
                })
    
    def analyze_search_results(self, soup, query):
        """検索結果ページの詳細解析"""
        result_selectors = [
            # 一般的なパターン
            '.search-result-item',
            '.search-item',
            '.book-item',
            '.product-item',
            '.result-item',
            
            # BOOK☆WALKER特有パターン
            '.c-card-book-list .m-card-book',
            '.m-card-book',
            '.c-card-book',
            '.book-card',
            '.product-card',
            
            # より具体的なパターン
            'div[data-book-id]',
            'div[data-product-id]',
            'article',
            '.tile',
            '.grid-item',
            
            # リンクベースのパターン
            'a[href*="/de"]',  # BOOK☆WALKERの書籍URLパターン
            'a[href*="/series"]',
            'a[href*="/book"]'
        ]
        
        analysis = {
            'found_results': False,
            'result_count': 0,
            'successful_selectors': [],
            'all_links': [],
            'title_patterns': []
        }
        
        # 各セレクタをテスト
        for selector in result_selectors:
            try:
                elements = soup.select(selector)
                if elements:
                    analysis['successful_selectors'].append({
                        'selector': selector,
                        'count': len(elements)
                    })
                    
                    analysis['found_results'] = True
                    analysis['result_count'] = max(analysis['result_count'], len(elements))
                    
                    # 各要素から詳細情報を抽出
                    for element in elements[:3]:  # 上位3つを詳細分析
                        link_info = self.extract_element_info(element)
                        if link_info:
                            analysis['all_links'].append(link_info)
                            
            except Exception as e:
                print(f"     セレクタエラー {selector}: {e}")
        
        # タイトルパターンの抽出
        all_text_elements = soup.find_all(text=True)
        for text in all_text_elements:
            if query.lower() in text.lower() and len(text.strip()) > 5:
                analysis['title_patterns'].append(text.strip()[:100])
        
        return analysis
    
    def extract_element_info(self, element):
        """要素から詳細情報を抽出"""
        info = {
            'tag': element.name,
            'classes': element.get('class', []),
            'text': element.get_text(strip=True)[:200],
            'links': []
        }
        
        # リンクの抽出
        links = element.find_all('a', href=True)
        for link in links:
            href = link.get('href')
            if href:
                # 相対URLを絶対URLに変換
                if href.startswith('/'):
                    href = urljoin(self.BASE_URL, href)
                
                info['links'].append({
                    'href': href,
                    'text': link.get_text(strip=True)[:100]
                })
        
        return info if (info['text'] or info['links']) else None
    
    def test_direct_api_calls(self):
        """直接API呼び出しのテスト"""
        print("\n=== 直接API呼び出しテスト ===")
        
        # 推測されるAPIエンドポイント
        api_endpoints = [
            "/api/search",
            "/api/books/search", 
            "/search/api",
            "/ajax/search",
            "/v1/search",
            "/services/search",
        ]
        
        test_params = {
            'q': 'ソードアート・オンライン',
            'word': 'ソードアート・オンライン',
            'keyword': 'ソードアート・オンライン'
        }
        
        for endpoint in api_endpoints:
            print(f"API テスト: {self.BASE_URL}{endpoint}")
            
            try:
                # GET リクエスト
                response = self.session.get(
                    f"{self.BASE_URL}{endpoint}",
                    params=test_params,
                    timeout=10
                )
                
                if response.status_code == 200:
                    content_type = response.headers.get('content-type', '')
                    
                    if 'json' in content_type:
                        try:
                            data = response.json()
                            print(f"   ✅ JSON API発見!")
                            print(f"      キー: {list(data.keys()) if isinstance(data, dict) else 'Not dict'}")
                            
                            self.analysis_results['tests'].append({
                                'test': 'api_discovery',
                                'endpoint': endpoint,
                                'success': True,
                                'content_type': content_type,
                                'data_keys': list(data.keys()) if isinstance(data, dict) else None
                            })
                        except json.JSONDecodeError:
                            print(f"   ❌ JSON解析エラー")
                    else:
                        print(f"   ⚠️  非JSON応答: {content_type}")
                        
                elif response.status_code == 404:
                    print(f"   ❌ 404 Not Found")
                else:
                    print(f"   ❌ HTTPエラー: {response.status_code}")
                    
            except Exception as e:
                print(f"   💥 エラー: {e}")
    
    def save_analysis_results(self):
        """解析結果をファイルに保存"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f"logs/bookwalker_analysis_{timestamp}.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.analysis_results, f, ensure_ascii=False, indent=2)
        
        print(f"\n📄 解析結果を保存: {output_file}")
        return output_file
    
    def run_full_analysis(self):
        """完全解析の実行"""
        print("🔍 BOOK☆WALKER 完全サイト解析開始")
        print(f"開始時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        try:
            # 1. 基本構造解析
            self.analyze_search_page_structure()
            
            # 2. 検索クエリテスト
            self.test_search_queries()
            
            # 3. API発見テスト
            self.test_direct_api_calls()
            
            # 4. 結果保存
            output_file = self.save_analysis_results()
            
            print("=" * 60)
            print("✅ 解析完了")
            
            # サマリー表示
            successful_tests = [t for t in self.analysis_results['tests'] if t.get('success')]
            print(f"成功テスト: {len(successful_tests)}/{len(self.analysis_results['tests'])}")
            
            return output_file
            
        except Exception as e:
            print(f"💥 解析中にエラー: {e}")
            return None


def main():
    """メイン処理"""
    # ログディレクトリ作成
    Path('logs').mkdir(exist_ok=True)
    
    analyzer = BookWalkerAnalyzer()
    result_file = analyzer.run_full_analysis()
    
    if result_file:
        print(f"\n🎯 次のステップ: {result_file} を確認して最適な戦略を決定")


if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
紀伊國屋書店（Kinoppy）サイト構造分析器
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


class KinoppyDeepAnalyzer:
    """紀伊國屋書店の深層構造解析クラス"""
    
    BASE_URL = "https://www.kinokuniya.co.jp"
    
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
        print("=== 紀伊國屋書店（Kinoppy）深層分析開始 ===")
        print(f"開始時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Phase 1: トップページ分析
        print("🔍 Phase 1: トップページ構造分析")
        self._analyze_homepage()
        
        # Phase 2: 検索エンドポイント発見
        print("\n🔍 Phase 2: 検索エンドポイント発見")
        self._discover_search_endpoints()
        
        # Phase 3: 実際の検索実行と応答分析
        print("\n🔍 Phase 3: 実際の検索実行・応答分析")
        self._analyze_search_responses()
        
        # Phase 4: JavaScript/Ajax分析
        print("\n🔍 Phase 4: JavaScript/Ajax分析")
        self._analyze_javascript_ajax()
        
        # Phase 5: 代替アプローチ検討
        print("\n🔍 Phase 5: 代替アプローチ検討")
        self._explore_alternative_approaches()
        
        print("\n=== 紀伊國屋書店深層分析完了 ===")
    
    def _analyze_homepage(self):
        """トップページの構造分析"""
        try:
            # 複数のURLパターンを試行
            urls_to_check = [
                "https://www.kinokuniya.co.jp/",
                "https://www.kinokuniya.co.jp/kinoppystore/",
                "https://www.kinokuniya.co.jp/kinoppystore/search",
                "https://www.kinokuniya.co.jp/f/dsg-08-EK",  # 旧URL
                "https://kinoppy.jp/",  # 別ドメイン
                "https://store.kinoppy.jp/",  # ストア別ドメイン
            ]
            
            for url in urls_to_check:
                print(f"  🌐 アクセス中: {url}")
                try:
                    response = self.session.get(url, timeout=10)
                    print(f"    ステータス: {response.status_code}")
                    
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, 'html.parser')
                        title = soup.find('title')
                        print(f"    タイトル: {title.get_text() if title else 'なし'}")
                        
                        # 検索フォーム検出
                        search_forms = soup.find_all('form')
                        print(f"    検索フォーム数: {len(search_forms)}")
                        
                        for i, form in enumerate(search_forms):
                            action = form.get('action', '')
                            method = form.get('method', 'GET')
                            print(f"      フォーム{i+1}: {method} {action}")
                            
                            # 入力フィールド分析
                            inputs = form.find_all(['input', 'select'])
                            for inp in inputs:
                                name = inp.get('name', '')
                                input_type = inp.get('type', '')
                                if name and input_type not in ['hidden', 'submit']:
                                    print(f"        入力: {name} ({input_type})")
                        
                        # ナビゲーションリンク
                        nav_links = soup.find_all('a', href=True)
                        ebook_links = [link for link in nav_links if 'kinoppy' in link.get('href', '').lower() or 'ebook' in link.get('href', '').lower()]
                        print(f"    電子書籍関連リンク: {len(ebook_links)}")
                        
                        for link in ebook_links[:5]:  # 最初の5個だけ表示
                            href = link.get('href')
                            text = link.get_text(strip=True)
                            print(f"      - {text}: {href}")
                        
                    elif response.status_code == 404:
                        print(f"    ❌ 404 - URLが存在しません")
                    elif response.status_code == 302 or response.status_code == 301:
                        print(f"    🔄 リダイレクト先: {response.headers.get('Location', '不明')}")
                    else:
                        print(f"    ⚠️ 予期しないステータス: {response.status_code}")
                        
                except requests.exceptions.Timeout:
                    print(f"    ⏰ タイムアウト")
                except requests.exceptions.ConnectionError:
                    print(f"    🔌 接続エラー")
                except Exception as e:
                    print(f"    💥 エラー: {str(e)}")
                
                time.sleep(1)  # 負荷軽減
                
        except Exception as e:
            logger.error(f"ホームページ分析エラー: {e}")
    
    def _discover_search_endpoints(self):
        """検索エンドポイントの発見"""
        try:
            # 想定される検索エンドポイント
            search_endpoints = [
                "/kinoppystore/search",
                "/search",
                "/f/dsg-08-EK",
                "/f/dsg-08",
                "/dw/search",
                "/book/search",
                "/ebook/search",
                "/api/search",
                "/ajax/search",
            ]
            
            print("  📡 検索エンドポイント探査:")
            
            for endpoint in search_endpoints:
                full_url = self.BASE_URL + endpoint
                print(f"    テスト中: {endpoint}")
                
                try:
                    # GET リクエスト
                    response = self.session.get(full_url, timeout=5)
                    print(f"      GET {response.status_code}")
                    
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, 'html.parser')
                        
                        # 検索に関連する要素を探す
                        search_indicators = [
                            soup.find_all('input', {'type': 'search'}),
                            soup.find_all('input', {'name': re.compile(r'(search|query|q|keyword)', re.I)}),
                            soup.find_all('form', {'action': re.compile(r'search', re.I)}),
                        ]
                        
                        total_indicators = sum(len(indicators) for indicators in search_indicators)
                        if total_indicators > 0:
                            print(f"      ✅ 検索要素発見: {total_indicators}個")
                            
                            # 詳細分析
                            forms = soup.find_all('form')
                            for form in forms:
                                action = form.get('action', '')
                                if action:
                                    print(f"        フォームアクション: {action}")
                                    
                        else:
                            print(f"      ⚪ 通常ページ（検索要素なし）")
                    
                    elif response.status_code == 404:
                        print(f"      ❌ 404")
                    else:
                        print(f"      ⚠️ {response.status_code}")
                        
                except Exception as e:
                    print(f"      💥 エラー: {str(e)[:50]}")
                    
                time.sleep(0.5)
                
        except Exception as e:
            logger.error(f"エンドポイント探査エラー: {e}")
    
    def _analyze_search_responses(self):
        """実際の検索実行と応答分析"""
        try:
            test_queries = [
                "ソードアート・オンライン",
                "SAO",
                "クソゲー悪役令嬢",
                "9784048671811",  # ISBN
            ]
            
            print("  🔎 実際の検索実行テスト:")
            
            # 想定される検索パラメータパターン
            search_patterns = [
                {"q": "{query}"},
                {"search": "{query}"},
                {"keyword": "{query}"},
                {"query": "{query}"},
                {"searchKeyword": "{query}"},
                {"searchterm": "{query}"},
                {"q": "{query}", "searchtype": "BOOK"},
                {"q": "{query}", "category": "ebook"},
                {"keyword": "{query}", "type": "digital"},
            ]
            
            search_urls = [
                "https://www.kinokuniya.co.jp/kinoppystore/search",
                "https://www.kinokuniya.co.jp/search",
                "https://www.kinokuniya.co.jp/dw/search",
            ]
            
            for url in search_urls:
                print(f"    🌐 URL: {url}")
                
                for query in test_queries[:2]:  # 最初の2クエリのみ
                    print(f"      📚 クエリ: {query}")
                    
                    for pattern in search_patterns[:3]:  # 最初の3パターンのみ
                        try:
                            params = {k: v.format(query=query) for k, v in pattern.items()}
                            print(f"        パラメータ: {params}")
                            
                            response = self.session.get(url, params=params, timeout=8)
                            print(f"        レスポンス: {response.status_code} ({len(response.text)} bytes)")
                            
                            if response.status_code == 200:
                                soup = BeautifulSoup(response.text, 'html.parser')
                                
                                # 検索結果の指標を探す
                                result_indicators = [
                                    len(soup.find_all('a', href=lambda x: x and '/dsg-' in x)),
                                    len(soup.find_all('div', class_=re.compile(r'(book|item|product)', re.I))),
                                    len(soup.find_all(['h2', 'h3', 'h4'], string=re.compile(query[:5], re.I))),
                                ]
                                
                                total_results = sum(result_indicators)
                                print(f"        結果要素: {total_results}個")
                                
                                if total_results > 0:
                                    print(f"        ✅ 検索結果らしきものを発見！")
                                    
                                    # 実際のリンクを探す
                                    book_links = soup.find_all('a', href=re.compile(r'/dsg-'))
                                    if book_links:
                                        for link in book_links[:3]:
                                            href = link.get('href')
                                            text = link.get_text(strip=True)
                                            print(f"          📖 {text[:30]}... -> {href}")
                                
                            time.sleep(1)
                            
                        except Exception as e:
                            print(f"        💥 エラー: {str(e)[:50]}")
                            
                    print()
                    
        except Exception as e:
            logger.error(f"検索応答分析エラー: {e}")
    
    def _analyze_javascript_ajax(self):
        """JavaScript/Ajax分析"""
        try:
            print("  🔧 JavaScript/Ajax分析:")
            
            # トップページのJavaScriptファイル検出
            try:
                response = self.session.get("https://www.kinokuniya.co.jp/kinoppystore/", timeout=10)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Script タグ検出
                    scripts = soup.find_all('script', src=True)
                    print(f"    外部スクリプト数: {len(scripts)}")
                    
                    # Ajax関連のパターンを探す
                    ajax_patterns = [
                        r'ajax',
                        r'xhr',
                        r'fetch',
                        r'search',
                        r'api',
                    ]
                    
                    inline_scripts = soup.find_all('script', src=False)
                    print(f"    インラインスクリプト数: {len(inline_scripts)}")
                    
                    ajax_hints = []
                    for script in inline_scripts:
                        script_content = script.get_text()
                        for pattern in ajax_patterns:
                            if re.search(pattern, script_content, re.I):
                                ajax_hints.append(pattern)
                    
                    if ajax_hints:
                        print(f"    Ajax関連キーワード発見: {', '.join(set(ajax_hints))}")
                    else:
                        print(f"    Ajax関連要素なし（静的サイトの可能性）")
                    
                    # Formのsubmit先分析
                    forms = soup.find_all('form')
                    for form in forms:
                        action = form.get('action', '')
                        if 'search' in action.lower():
                            print(f"    検索フォーム発見: {action}")
                            
                            # フォーム内のJavaScript分析
                            onsubmit = form.get('onsubmit', '')
                            if onsubmit:
                                print(f"      onsubmit: {onsubmit[:100]}...")
            
            except Exception as e:
                print(f"    💥 JavaScript分析エラー: {str(e)}")
                
        except Exception as e:
            logger.error(f"JavaScript/Ajax分析エラー: {e}")
    
    def _explore_alternative_approaches(self):
        """代替アプローチの検討"""
        try:
            print("  💡 代替アプローチ検討:")
            
            approaches = [
                {
                    'name': 'Selenium WebDriver',
                    'pros': 'JavaScript実行、動的コンテンツ対応',
                    'cons': '重い、検出されやすい',
                    'feasibility': '高'
                },
                {
                    'name': 'Playwright',
                    'pros': '高速、最新ブラウザ技術、ステルス性',
                    'cons': '実装コスト',
                    'feasibility': '高'
                },
                {
                    'name': 'API逆解析',
                    'pros': '最高速、確実',
                    'cons': '技術的難易度高、メンテナンス性',
                    'feasibility': '中'
                },
                {
                    'name': 'Chrome DevTools Protocol',
                    'pros': '柔軟性、詳細制御',
                    'cons': '複雑、実装コスト高',
                    'feasibility': '中'
                },
                {
                    'name': 'requests-html',
                    'pros': 'JavaScript対応、シンプル',
                    'cons': 'PyQt4依存、安定性',
                    'feasibility': '中'
                },
            ]
            
            print("    🛠️ 技術選択肢:")
            for approach in approaches:
                print(f"      {approach['name']}:")
                print(f"        利点: {approach['pros']}")
                print(f"        欠点: {approach['cons']}")
                print(f"        実装可能性: {approach['feasibility']}")
                print()
            
            # 推奨戦略
            print("    🎯 推奨戦略:")
            print("      1. Playwright実装（第一選択）")
            print("        - ヘッドレスブラウザでのフル機能テスト")
            print("        - JavaScript実行環境での動的検索")
            print("        - ユーザー操作シミュレーション")
            print()
            print("      2. Selenium WebDriver（フォールバック）")
            print("        - Chromeドライバーでの確実な動作")
            print("        - デバッグ機能充実")
            print()
            print("      3. API探査・リバースエンジニアリング（上級）")
            print("        - ブラウザDevToolsでのネットワーク分析")
            print("        - 実際のAPIエンドポイント発見")
            print("        - 直接APIアクセス実装")
            
        except Exception as e:
            logger.error(f"代替アプローチ検討エラー: {e}")


async def main():
    """メイン実行関数"""
    analyzer = KinoppyDeepAnalyzer()
    
    try:
        analyzer.analyze_site_structure()
        
        print("\n" + "="*60)
        print("🎯 分析結果サマリー")
        print("="*60)
        print("1. 現在のrequests + BeautifulSoupアプローチは限界")
        print("2. JavaScriptベースの動的サイトの可能性が高い")
        print("3. Playwright実装が最適解と判断")
        print("4. 次フェーズ: Playwright版スクレイパー実装")
        print("\n💡 即座にPlaywright版実装に移行することを推奨")
        
    except Exception as e:
        logger.error(f"分析実行エラー: {e}")
        print(f"💥 分析エラー: {e}")


if __name__ == "__main__":
    asyncio.run(main())
#!/usr/bin/env python3
"""
ebookjapan サイト構造解析ツール
BOOK☆WALKERで成功したアプローチを適用
"""
import asyncio
import requests
import json
from datetime import datetime
from pathlib import Path
from bs4 import BeautifulSoup

def analyze_ebookjapan_structure():
    """ebookjapanの基本構造を解析"""
    
    base_url = "https://ebookjapan.yahoo.co.jp"
    search_url = "https://ebookjapan.yahoo.co.jp/search/"
    
    # リクエストヘッダー（Yahoo!系サイト用）
    headers = {
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
    }
    
    # テスト用クエリ
    test_queries = [
        {
            'query': 'ソードアート・オンライン',
            'params': {'keyword': 'ソードアート・オンライン'}
        },
        {
            'query': 'SAO',
            'params': {'keyword': 'SAO'}
        },
        {
            'query': '転生したらスライムだった件',
            'params': {'keyword': '転生したらスライムだった件'}
        },
        {
            'query': 'リゼロ',
            'params': {'keyword': 'リゼロ'}
        },
        {
            'query': 'この素晴らしい世界に祝福を',
            'params': {'keyword': 'この素晴らしい世界に祝福を'}
        },
        {
            'query': 'パラレイドデイズ',
            'params': {'keyword': 'パラレイドデイズ'}
        }
    ]
    
    results = {
        'timestamp': datetime.now().isoformat(),
        'tests': []
    }
    
    session = requests.Session()
    session.headers.update(headers)
    
    print("=== ebookjapan サイト構造解析開始 ===")
    print(f"ベースURL: {base_url}")
    print(f"検索URL: {search_url}")
    print()
    
    # 基本的なページ構造テスト
    try:
        print("1. 基本ページ構造の解析...")
        response = session.get(base_url, timeout=10)
        print(f"   ステータス: {response.status_code}")
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 基本要素の確認
            title = soup.find('title')
            print(f"   ページタイトル: {title.get_text() if title else 'N/A'}")
            
            # 主要なナビゲーション要素
            nav_elements = soup.find_all(['nav', '[class*="nav"]', '[class*="menu"]'])
            print(f"   ナビゲーション要素: {len(nav_elements)}個")
            
            # フォーム要素（検索フォーム）
            form_elements = soup.find_all('form')
            print(f"   フォーム要素: {len(form_elements)}個")
            
            # 検索ボックスの確認
            search_inputs = soup.find_all(['input[type="search"]', 'input[name*="search"]', 'input[name*="keyword"]'])
            print(f"   検索入力欄: {len(search_inputs)}個")
            
            if search_inputs:
                for i, inp in enumerate(search_inputs):
                    print(f"     検索欄{i+1}: name='{inp.get('name')}', placeholder='{inp.get('placeholder', 'N/A')}'")
        
        results['tests'].append({
            'test': 'basic_page_structure',
            'success': True,
            'status_code': response.status_code
        })
        
    except Exception as e:
        print(f"   エラー: {e}")
        results['tests'].append({
            'test': 'basic_page_structure',
            'success': False,
            'error': str(e)
        })
    
    print()
    
    # 検索クエリテスト
    for i, test_query in enumerate(test_queries, 1):
        print(f"{i+1}. 検索クエリテスト: '{test_query['query']}'")
        
        try:
            # 検索リクエスト実行
            response = session.get(search_url, params=test_query['params'], timeout=15)
            print(f"   ステータス: {response.status_code}")
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 検索結果の基本解析
                result_data = {
                    'found_results': False,
                    'result_count': 0,
                    'successful_selectors': [],
                    'all_links': [],
                    'book_patterns': []
                }
                
                # 書籍リンクのパターン検索
                book_link_patterns = [
                    'a[href*="/books/"]',
                    'a[href*="/title/"]',
                    'a[href*="/series/"]',
                    'a[href*="/product/"]',
                    'a[href*="/item/"]',
                    'a[href*="/detail/"]'
                ]
                
                for pattern in book_link_patterns:
                    links = soup.select(pattern)
                    if links:
                        result_data['successful_selectors'].append({
                            'selector': pattern,
                            'count': len(links)
                        })
                        print(f"   セレクタ '{pattern}': {len(links)}件")
                
                # 全リンクの最初の10個を分析
                all_links = soup.find_all('a', href=True)[:10]
                for link in all_links:
                    link_info = {
                        'tag': link.name,
                        'classes': link.get('class', []),
                        'text': link.get_text(strip=True)[:50],
                        'href': link.get('href')[:100]
                    }
                    result_data['all_links'].append(link_info)
                
                # 書籍っぽいパターンの検索
                book_title_patterns = soup.find_all(text=lambda text: 
                    text and (
                        test_query['query'] in text or
                        'ソードアート' in text or
                        'SAO' in text or
                        '転生' in text or
                        'リゼロ' in text or
                        'この素晴らしい' in text or
                        'パラレイド' in text
                    )
                )
                
                for pattern in book_title_patterns[:20]:  # 最初の20個
                    clean_text = pattern.strip()
                    if len(clean_text) > 5:
                        result_data['book_patterns'].append(clean_text)
                
                result_data['found_results'] = len(result_data['successful_selectors']) > 0
                result_data['result_count'] = sum(sel['count'] for sel in result_data['successful_selectors'])
                
                print(f"   検索結果: {result_data['result_count']}件")
                print(f"   書籍パターン: {len(result_data['book_patterns'])}件")
                
                results['tests'].append({
                    'test': f'search_query_{i}',
                    'query': test_query['query'],
                    'params': test_query['params'],
                    'success': True,
                    'data': result_data
                })
                
            else:
                print(f"   検索失敗: HTTP {response.status_code}")
                results['tests'].append({
                    'test': f'search_query_{i}',
                    'query': test_query['query'],
                    'params': test_query['params'],
                    'success': False,
                    'status_code': response.status_code
                })
        
        except Exception as e:
            print(f"   エラー: {e}")
            results['tests'].append({
                'test': f'search_query_{i}',
                'query': test_query['query'],
                'params': test_query['params'],
                'success': False,
                'error': str(e)
            })
        
        print()
    
    # 結果をJSONファイルに保存
    output_file = f"logs/ebookjapan_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    Path('logs').mkdir(exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"📄 解析結果を保存: {output_file}")
    print("=== ebookjapan サイト構造解析完了 ===")
    
    return results

def main():
    """メイン処理"""
    try:
        results = analyze_ebookjapan_structure()
        
        # サマリー表示
        successful_tests = [t for t in results['tests'] if t['success']]
        failed_tests = [t for t in results['tests'] if not t['success']]
        
        print(f"\n📊 解析サマリー:")
        print(f"  成功: {len(successful_tests)}件")
        print(f"  失敗: {len(failed_tests)}件")
        
        if failed_tests:
            print(f"\n❌ 失敗したテスト:")
            for test in failed_tests:
                print(f"  - {test['test']}")
                if 'error' in test:
                    print(f"    エラー: {test['error']}")
        
        # 有効なセレクタの表示
        print(f"\n✅ 発見されたセレクタパターン:")
        for test in successful_tests:
            if 'data' in test and 'successful_selectors' in test['data']:
                for selector in test['data']['successful_selectors']:
                    print(f"  - {selector['selector']}: {selector['count']}件")
    
    except KeyboardInterrupt:
        print("\n⚠️ 解析が中断されました")
    except Exception as e:
        print(f"💥 予期しないエラー: {e}")

if __name__ == "__main__":
    main()
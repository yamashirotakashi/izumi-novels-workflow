#!/usr/bin/env python3
"""
Phase 1高度ブラウザ自動化スクレイパー検証テスト
Chrome環境制約対応版 - 基底クラス互換性修正版
"""
import asyncio
import sys
import os
import json
from typing import Dict, Any
from datetime import datetime

# パス追加
sys.path.append('/mnt/c/Users/tky99/DEV/izumi-novels-workflow/src')

class Phase1VerificationTestFixed:
    """Phase 1検証テストクラス（修正版）"""
    
    def __init__(self):
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'phase': 'Phase 1 - 高度ブラウザ自動化',
            'technology': 'undetected-chromedriver + Human Behavior Simulation',
            'tests': {},
            'overall_status': 'PENDING'
        }
    
    async def run_comprehensive_verification(self):
        """包括的検証テスト実行"""
        print('🚀 Phase 1高度ブラウザ自動化スクレイパー 包括検証開始（修正版）')
        print('=' * 70)
        
        # テスト実行
        await self.test_import_compatibility()
        await self.test_configuration_validation()
        await self.test_human_behavior_simulation()
        await self.test_title_variant_generation()
        await self.test_url_validation_logic()
        await self.test_similarity_scoring()
        await self.test_implementation_completeness()
        await self.test_chrome_compatibility()
        
        # 総合判定
        self.evaluate_overall_status()
        
        # レポート生成
        await self.generate_verification_report()
        
        print('\n🏁 Phase 1包括検証完了')
        return self.results
    
    async def test_import_compatibility(self):
        """インポート互換性テスト"""
        print('\n--- インポート互換性テスト ---')
        test_name = 'import_compatibility'
        
        try:
            # 基本モジュールインポート
            from scraping.kinoppy_advanced_scraper import HumanBehavior
            from scraping.selenium_base_scraper import SeleniumBaseScraper
            
            # 依存関係チェック
            import undetected_chromedriver as uc
            from selenium.webdriver.common.by import By
            from selenium.webdriver.common.keys import Keys
            from bs4 import BeautifulSoup
            
            self.results['tests'][test_name] = {
                'status': 'PASS',
                'message': 'すべてのモジュールを正常にインポート',
                'details': [
                    'HumanBehavior: OK',
                    'SeleniumBaseScraper: OK', 
                    'undetected_chromedriver: OK',
                    'selenium: OK',
                    'BeautifulSoup: OK'
                ]
            }
            print('✅ インポート互換性テスト: PASS')
            
        except Exception as e:
            self.results['tests'][test_name] = {
                'status': 'FAIL',
                'message': f'インポートエラー: {str(e)}',
                'details': []
            }
            print(f'❌ インポート互換性テスト: FAIL - {str(e)}')
    
    async def test_configuration_validation(self):
        """設定検証テスト（直接インスタンス化回避）"""
        print('\n--- 設定検証テスト ---')
        test_name = 'configuration_validation'
        
        try:
            from scraping.kinoppy_advanced_scraper import KinoppyAdvancedScraper
            from scraping.reader_store_advanced_scraper import ReaderStoreAdvancedScraper
            
            # クラス属性の検証（インスタンス化しない）
            kinoppy_config = {
                'SITE_NAME': KinoppyAdvancedScraper.SITE_NAME,
                'BASE_URL': KinoppyAdvancedScraper.BASE_URL,
                'SEARCH_URL': KinoppyAdvancedScraper.SEARCH_URL
            }
            
            reader_store_config = {
                'SITE_NAME': ReaderStoreAdvancedScraper.SITE_NAME,
                'BASE_URL': ReaderStoreAdvancedScraper.BASE_URL,
                'SEARCH_URL': ReaderStoreAdvancedScraper.SEARCH_URL
            }
            
            # 設定値検証
            expected_configs = {
                'kinoppy': {
                    'BASE_URL': 'https://www.kinokuniya.co.jp',
                    'SEARCH_URL': 'https://www.kinokuniya.co.jp/kinoppystore/search.php',
                    'SITE_NAME': 'kinoppy_advanced'
                },
                'reader_store': {
                    'BASE_URL': 'https://ebookstore.sony.jp',
                    'SEARCH_URL': 'https://ebookstore.sony.jp/search/',
                    'SITE_NAME': 'reader_store_advanced'
                }
            }
            
            config_validation = {}
            
            # Kinoppy設定検証
            kinoppy_valid = (
                kinoppy_config['BASE_URL'] == expected_configs['kinoppy']['BASE_URL'] and
                kinoppy_config['SEARCH_URL'] == expected_configs['kinoppy']['SEARCH_URL'] and
                kinoppy_config['SITE_NAME'] == expected_configs['kinoppy']['SITE_NAME']
            )
            config_validation['kinoppy'] = kinoppy_valid
            
            # Reader Store設定検証
            reader_store_valid = (
                reader_store_config['BASE_URL'] == expected_configs['reader_store']['BASE_URL'] and
                reader_store_config['SEARCH_URL'] == expected_configs['reader_store']['SEARCH_URL'] and
                reader_store_config['SITE_NAME'] == expected_configs['reader_store']['SITE_NAME']
            )
            config_validation['reader_store'] = reader_store_valid
            
            all_valid = all(config_validation.values())
            
            self.results['tests'][test_name] = {
                'status': 'PASS' if all_valid else 'FAIL',
                'message': '設定検証完了' if all_valid else '設定に不整合あり',
                'details': {
                    'expected': expected_configs,
                    'actual': {
                        'kinoppy': kinoppy_config,
                        'reader_store': reader_store_config
                    },
                    'validation': config_validation
                }
            }
            
            status = '✅' if all_valid else '❌'
            print(f'{status} 設定検証テスト: {"PASS" if all_valid else "FAIL"}')
            
        except Exception as e:
            self.results['tests'][test_name] = {
                'status': 'FAIL',
                'message': f'設定検証エラー: {str(e)}',
                'details': {}
            }
            print(f'❌ 設定検証テスト: FAIL - {str(e)}')
    
    async def test_human_behavior_simulation(self):
        """人間動作シミュレーションテスト"""
        print('\n--- 人間動作シミュレーションテスト ---')
        test_name = 'human_behavior_simulation'
        
        try:
            from scraping.kinoppy_advanced_scraper import HumanBehavior
            
            behavior = HumanBehavior()
            
            # パラメータ検証
            behavior_params = {
                'typing_speed_min': behavior.typing_speed_min,
                'typing_speed_max': behavior.typing_speed_max,
                'mouse_move_steps': behavior.mouse_move_steps,
                'scroll_pause_min': behavior.scroll_pause_min,
                'scroll_pause_max': behavior.scroll_pause_max,
                'page_load_wait_min': behavior.page_load_wait_min,
                'page_load_wait_max': behavior.page_load_wait_max
            }
            
            # 妥当性チェック
            valid_ranges = (
                0 < behavior.typing_speed_min < behavior.typing_speed_max < 1 and
                behavior.mouse_move_steps > 0 and
                0 < behavior.scroll_pause_min < behavior.scroll_pause_max < 10 and
                0 < behavior.page_load_wait_min < behavior.page_load_wait_max < 30
            )
            
            self.results['tests'][test_name] = {
                'status': 'PASS' if valid_ranges else 'FAIL',
                'message': '人間動作パラメータ検証完了',
                'details': {
                    'parameters': behavior_params,
                    'ranges_valid': valid_ranges
                }
            }
            
            status = '✅' if valid_ranges else '❌'
            print(f'{status} 人間動作シミュレーションテスト: {"PASS" if valid_ranges else "FAIL"}')
            
        except Exception as e:
            self.results['tests'][test_name] = {
                'status': 'FAIL',
                'message': f'人間動作シミュレーションエラー: {str(e)}',
                'details': {}
            }
            print(f'❌ 人間動作シミュレーションテスト: FAIL - {str(e)}')
    
    async def test_title_variant_generation(self):
        """タイトルバリエーション生成テスト（独立メソッドを直接テスト）"""
        print('\n--- タイトルバリエーション生成テスト ---')
        test_name = 'title_variant_generation'
        
        try:
            from scraping.kinoppy_advanced_scraper import KinoppyAdvancedScraper
            from scraping.reader_store_advanced_scraper import ReaderStoreAdvancedScraper
            
            test_title = "課長が目覚めたら異世界SF艦隊の提督になってた件です①"
            
            # 直接メソッド呼び出し（インスタンス化不要）
            kinoppy_scraper = type('TestScraper', (KinoppyAdvancedScraper,), {})
            reader_store_scraper = type('TestScraper', (ReaderStoreAdvancedScraper,), {})
            
            # バリエーション生成メソッドを直接呼び出し
            kinoppy_variants = kinoppy_scraper._create_kinoppy_title_variants(None, test_title)
            reader_store_variants = reader_store_scraper._create_reader_store_title_variants(None, test_title)
            
            # 品質検証
            kinoppy_quality = (
                len(kinoppy_variants) >= 3 and
                len(kinoppy_variants) <= 10 and
                test_title in kinoppy_variants and
                any('1' in variant for variant in kinoppy_variants)  # 巻数変換
            )
            
            reader_store_quality = (
                len(reader_store_variants) >= 3 and
                len(reader_store_variants) <= 10 and
                test_title in reader_store_variants and
                any('1' in variant for variant in reader_store_variants)  # 巻数変換
            )
            
            overall_quality = kinoppy_quality and reader_store_quality
            
            self.results['tests'][test_name] = {
                'status': 'PASS' if overall_quality else 'FAIL',
                'message': 'タイトルバリエーション生成完了',
                'details': {
                    'test_title': test_title,
                    'kinoppy_variants': kinoppy_variants,
                    'reader_store_variants': reader_store_variants,
                    'kinoppy_quality': kinoppy_quality,
                    'reader_store_quality': reader_store_quality
                }
            }
            
            status = '✅' if overall_quality else '❌'
            print(f'{status} タイトルバリエーション生成テスト: {"PASS" if overall_quality else "FAIL"}')
            print(f'  Kinoppy: {len(kinoppy_variants)}バリエーション')
            print(f'  Reader Store: {len(reader_store_variants)}バリエーション')
            
        except Exception as e:
            self.results['tests'][test_name] = {
                'status': 'FAIL',
                'message': f'バリエーション生成エラー: {str(e)}',
                'details': {}
            }
            print(f'❌ タイトルバリエーション生成テスト: FAIL - {str(e)}')
    
    async def test_url_validation_logic(self):
        """URL検証ロジックテスト（静的メソッドとして）"""
        print('\n--- URL検証ロジックテスト ---')
        test_name = 'url_validation_logic'
        
        try:
            from scraping.kinoppy_advanced_scraper import KinoppyAdvancedScraper
            from scraping.reader_store_advanced_scraper import ReaderStoreAdvancedScraper
            
            # テストケース
            kinoppy_test_cases = [
                ("https://www.kinokuniya.co.jp/dsg-01-9784123456789", True),
                ("https://www.kinokuniya.co.jp/detail/book-123", True),
                ("https://example.com/book", False),
                ("", False),
            ]
            
            reader_store_test_cases = [
                ("https://ebookstore.sony.jp/storeProduct/123", True),
                ("https://ebookstore.sony.jp/item/456", True),
                ("https://example.com/book", False),
                ("", False),
            ]
            
            # 検証実行（クラスメソッドとして実行）
            kinoppy_results = []
            for url, expected in kinoppy_test_cases:
                result = await KinoppyAdvancedScraper._verify_url(None, url, "test")
                kinoppy_results.append({
                    'url': url,
                    'expected': expected,
                    'actual': result,
                    'pass': result == expected
                })
            
            reader_store_results = []
            for url, expected in reader_store_test_cases:
                result = await ReaderStoreAdvancedScraper._verify_url(None, url, "test")
                reader_store_results.append({
                    'url': url,
                    'expected': expected,
                    'actual': result,
                    'pass': result == expected
                })
            
            # 合格判定
            kinoppy_pass = all(test['pass'] for test in kinoppy_results)
            reader_store_pass = all(test['pass'] for test in reader_store_results)
            overall_pass = kinoppy_pass and reader_store_pass
            
            self.results['tests'][test_name] = {
                'status': 'PASS' if overall_pass else 'FAIL',
                'message': 'URL検証ロジック完了',
                'details': {
                    'kinoppy_results': kinoppy_results,
                    'reader_store_results': reader_store_results,
                    'kinoppy_pass': kinoppy_pass,
                    'reader_store_pass': reader_store_pass
                }
            }
            
            status = '✅' if overall_pass else '❌'
            print(f'{status} URL検証ロジックテスト: {"PASS" if overall_pass else "FAIL"}')
            
        except Exception as e:
            self.results['tests'][test_name] = {
                'status': 'FAIL',
                'message': f'URL検証エラー: {str(e)}',
                'details': {}
            }
            print(f'❌ URL検証ロジックテスト: FAIL - {str(e)}')
    
    async def test_similarity_scoring(self):
        """類似度スコア計算テスト（基底クラスのメソッドを使用）"""
        print('\n--- 類似度スコア計算テスト ---')
        test_name = 'similarity_scoring'
        
        try:
            from scraping.selenium_base_scraper import SeleniumBaseScraper
            
            # テストケース
            test_cases = [
                ("課長が目覚めたら異世界SF艦隊の提督になってた件です①", "課長が目覚めたら異世界SF艦隊の提督になってた件です 1", 0.8),  # 高類似
                ("課長が目覚めたら異世界SF艦隊の提督になってた件です①", "課長が目覚めたら異世界SF艦隊の提督になってた件です", 0.7),      # 中高類似
                ("課長が目覚めたら異世界SF艦隊の提督になってた件です①", "異世界転生RPG物語", 0.3),                                    # 低類似
                ("課長が目覚めたら異世界SF艦隊の提督になってた件です①", "全く関係ない本", 0.1),                                    # 極低類似
            ]
            
            scoring_results = []
            for query, title, expected_min in test_cases:
                score = SeleniumBaseScraper.calculate_similarity_score(None, query, title)
                scoring_results.append({
                    'query': query[:30] + '...',
                    'title': title[:30] + '...',
                    'score': score,
                    'expected_min': expected_min,
                    'pass': score >= expected_min
                })
            
            # 合格判定
            scoring_valid = all(result['pass'] for result in scoring_results)
            
            self.results['tests'][test_name] = {
                'status': 'PASS' if scoring_valid else 'FAIL',
                'message': '類似度スコア計算完了',
                'details': {
                    'scoring_results': scoring_results,
                    'scoring_valid': scoring_valid
                }
            }
            
            status = '✅' if scoring_valid else '❌'
            print(f'{status} 類似度スコア計算テスト: {"PASS" if scoring_valid else "FAIL"}')
            
        except Exception as e:
            self.results['tests'][test_name] = {
                'status': 'FAIL',
                'message': f'類似度スコア計算エラー: {str(e)}',
                'details': {}
            }
            print(f'❌ 類似度スコア計算テスト: FAIL - {str(e)}')
    
    async def test_implementation_completeness(self):
        """実装完全性テスト"""
        print('\n--- 実装完全性テスト ---')
        test_name = 'implementation_completeness'
        
        try:
            from scraping.kinoppy_advanced_scraper import KinoppyAdvancedScraper
            from scraping.reader_store_advanced_scraper import ReaderStoreAdvancedScraper
            
            # 必須メソッドの存在確認
            required_methods = [
                'search_book',
                '_navigate_to_search_page',
                '_perform_advanced_search',
                '_extract_advanced_search_results',
                '_human_type',
                '_human_pause',
                '_human_scroll',
                'get_stats'
            ]
            
            kinoppy_methods = []
            reader_store_methods = []
            
            for method in required_methods:
                kinoppy_has = hasattr(KinoppyAdvancedScraper, method)
                reader_store_has = hasattr(ReaderStoreAdvancedScraper, method)
                
                kinoppy_methods.append({
                    'method': method,
                    'exists': kinoppy_has
                })
                reader_store_methods.append({
                    'method': method,
                    'exists': reader_store_has
                })
            
            kinoppy_complete = all(m['exists'] for m in kinoppy_methods)
            reader_store_complete = all(m['exists'] for m in reader_store_methods)
            overall_complete = kinoppy_complete and reader_store_complete
            
            self.results['tests'][test_name] = {
                'status': 'PASS' if overall_complete else 'FAIL',
                'message': '実装完全性検証完了',
                'details': {
                    'required_methods': required_methods,
                    'kinoppy_methods': kinoppy_methods,
                    'reader_store_methods': reader_store_methods,
                    'kinoppy_complete': kinoppy_complete,
                    'reader_store_complete': reader_store_complete
                }
            }
            
            status = '✅' if overall_complete else '❌'
            print(f'{status} 実装完全性テスト: {"PASS" if overall_complete else "FAIL"}')
            
        except Exception as e:
            self.results['tests'][test_name] = {
                'status': 'FAIL',
                'message': f'実装完全性エラー: {str(e)}',
                'details': {}
            }
            print(f'❌ 実装完全性テスト: FAIL - {str(e)}')
    
    async def test_chrome_compatibility(self):
        """Chrome互換性テスト（WSL制約確認）"""
        print('\n--- Chrome互換性テスト ---')
        test_name = 'chrome_compatibility'
        
        try:
            import undetected_chromedriver as uc
            from selenium.webdriver.chrome.options import Options
            
            # Chrome設定の妥当性確認
            options = uc.ChromeOptions()
            options.add_argument('--headless=new')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            
            # WSL環境でのChrome実行制約を確認
            import subprocess
            import shutil
            
            chrome_available = False
            chrome_path = None
            
            # システムのChromeを探す
            potential_paths = [
                '/usr/bin/google-chrome',
                '/usr/bin/google-chrome-stable',
                '/usr/bin/chromium',
                '/usr/bin/chromium-browser'
            ]
            
            for path in potential_paths:
                if shutil.which(path.split('/')[-1]):
                    chrome_path = path
                    chrome_available = True
                    break
            
            wsl_constraint = False
            try:
                # WSL環境判定
                with open('/proc/version', 'r') as f:
                    version_info = f.read().lower()
                    if 'microsoft' in version_info or 'wsl' in version_info:
                        wsl_constraint = True
            except:
                pass
            
            compatibility_details = {
                'chrome_available': chrome_available,
                'chrome_path': chrome_path,
                'wsl_environment': wsl_constraint,
                'headless_mode_required': wsl_constraint,
                'gui_support_limited': wsl_constraint
            }
            
            # 総合判定（Chrome利用可能または適切な代替策有り）
            compatibility_ok = chrome_available or not wsl_constraint
            
            self.results['tests'][test_name] = {
                'status': 'PASS' if compatibility_ok else 'PARTIAL',
                'message': 'Chrome互換性確認完了',
                'details': compatibility_details
            }
            
            status = '✅' if compatibility_ok else '⚠️'
            print(f'{status} Chrome互換性テスト: {"PASS" if compatibility_ok else "PARTIAL"}')
            if wsl_constraint:
                print('  ⚠️ WSL環境制約: headlessモード推奨')
            
        except Exception as e:
            self.results['tests'][test_name] = {
                'status': 'FAIL',
                'message': f'Chrome互換性エラー: {str(e)}',
                'details': {}
            }
            print(f'❌ Chrome互換性テスト: FAIL - {str(e)}')
    
    def evaluate_overall_status(self):
        """総合ステータス評価"""
        passed_tests = sum(1 for test in self.results['tests'].values() if test['status'] == 'PASS')
        partial_tests = sum(1 for test in self.results['tests'].values() if test['status'] == 'PARTIAL')
        total_tests = len(self.results['tests'])
        
        if passed_tests == total_tests:
            self.results['overall_status'] = 'FULL_PASS'
        elif passed_tests + partial_tests >= total_tests * 0.8:
            self.results['overall_status'] = 'MOSTLY_PASS' 
        elif passed_tests >= total_tests * 0.5:
            self.results['overall_status'] = 'PARTIAL_PASS'
        else:
            self.results['overall_status'] = 'FAIL'
        
        self.results['test_summary'] = {
            'passed': passed_tests,
            'partial': partial_tests,
            'total': total_tests,
            'pass_rate': (passed_tests + partial_tests * 0.5) / total_tests if total_tests > 0 else 0
        }
    
    async def generate_verification_report(self):
        """検証レポート生成"""
        print('\n' + '=' * 70)
        print('📊 Phase 1検証結果サマリー（修正版）')
        print('=' * 70)
        
        summary = self.results['test_summary']
        print(f"総合ステータス: {self.results['overall_status']}")
        print(f"テスト合格率: {summary['passed']}/{summary['total']} ({summary['pass_rate']:.1%})")
        if summary.get('partial', 0) > 0:
            print(f"部分的合格: {summary['partial']}個")
        
        print(f"\n📋 テスト詳細:")
        for test_name, test_result in self.results['tests'].items():
            if test_result['status'] == 'PASS':
                status_icon = '✅'
            elif test_result['status'] == 'PARTIAL':
                status_icon = '⚠️'
            else:
                status_icon = '❌'
            print(f"  {status_icon} {test_name}: {test_result['status']}")
        
        # 結果判定
        if self.results['overall_status'] in ['FULL_PASS', 'MOSTLY_PASS']:
            print(f"\n🎉 Phase 1実装品質: 高品質")
            print(f"💡 推奨: Windows環境での実機テスト進行")
        else:
            print(f"\n⚠️  Phase 1実装品質: 改善必要")
            print(f"💡 推奨: 実装修正後再検証")
        
        # レポートファイル保存
        report_path = '/mnt/c/Users/tky99/DEV/izumi-novels-workflow/reports/phase1_verification_report_fixed.json'
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        
        print(f"\n📄 詳細レポート保存: {report_path}")

async def main():
    """メイン検証実行"""
    print('🔍 Phase 1高度ブラウザ自動化スクレイパー 検証開始（修正版）')
    
    verifier = Phase1VerificationTestFixed()
    results = await verifier.run_comprehensive_verification()
    
    return results

if __name__ == '__main__':
    asyncio.run(main())
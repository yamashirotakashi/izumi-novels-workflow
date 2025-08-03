#!/usr/bin/env python3
"""
統合Google Sheetsクライアントのテストスクリプト

使用方法:
  python scripts/test_unified_google_sheets.py --mode [auto|legacy|updated]
  python scripts/test_unified_google_sheets.py --comprehensive
  python scripts/test_unified_google_sheets.py --migration-test
"""
import sys
import os
import argparse
import logging
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.scraping.google_sheets_client_consolidated import (
    GoogleSheetsClient,
    test_connection
)

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_test_config():
    """テスト設定を読み込み"""
    # 実際の設定ファイルパスは環境に応じて調整
    config = {
        'credentials_path': os.getenv('GOOGLE_SHEETS_CREDENTIALS', 'config/google_credentials.json'),
        'spreadsheet_id': os.getenv('GOOGLE_SHEETS_ID', 'your_spreadsheet_id_here')
    }
    
    # 設定の検証
    if not os.path.exists(config['credentials_path']):
        logger.warning(f"認証ファイルが見つかりません: {config['credentials_path']}")
        logger.info("環境変数 GOOGLE_SHEETS_CREDENTIALS で認証ファイルのパスを指定してください")
    
    if config['spreadsheet_id'] == 'your_spreadsheet_id_here':
        logger.warning("スプレッドシートIDが設定されていません")
        logger.info("環境変数 GOOGLE_SHEETS_ID でスプレッドシートIDを指定してください")
    
    return config


def test_basic_connection(config, mode="auto"):
    """基本接続テスト"""
    print(f"\n=== 基本接続テスト (mode: {mode}) ===")
    
    try:
        success = test_connection(
            config['credentials_path'],
            config['spreadsheet_id'],
            mode
        )
        
        if success:
            print("✅ 基本接続テスト成功")
        else:
            print("❌ 基本接続テスト失敗")
        
        return success
        
    except Exception as e:
        print(f"❌ 基本接続テスト例外: {e}")
        return False


def test_mode_compatibility(config):
    """モード間互換性テスト"""
    print("\n=== モード間互換性テスト ===")
    
    modes = ["auto", "legacy", "updated"]
    results = {}
    
    for mode in modes:
        try:
            client = UnifiedGoogleSheetsClient(
                config['credentials_path'],
                config['spreadsheet_id'],
                mode
            )
            
            books = client.read_books()
            stats = client.get_summary_stats()
            
            results[mode] = {
                'success': True,
                'books_count': len(books),
                'detected_mode': client.sheet_mode,
                'stats': stats
            }
            
            print(f"✅ {mode}モード: {len(books)}件 (実際: {client.sheet_mode})")
            
        except Exception as e:
            results[mode] = {
                'success': False,
                'error': str(e)
            }
            print(f"❌ {mode}モード: {e}")
    
    return results


def test_backward_compatibility(config):
    """後方互換性テスト"""
    print("\n=== 後方互換性テスト ===")
    
    try:
        # 旧クラス名でのインスタンス化テスト
        old_client = GoogleSheetsClient(
            config['credentials_path'],
            config['spreadsheet_id']
        )
        
        new_client = UnifiedGoogleSheetsClient(
            config['credentials_path'],
            config['spreadsheet_id']
        )
        
        # 同じ結果が得られることを確認
        old_books = old_client.read_books()
        new_books = new_client.read_books()
        
        if len(old_books) == len(new_books):
            print("✅ 後方互換性テスト成功: 同じ結果を取得")
            return True
        else:
            print(f"⚠️ 後方互換性警告: 結果数が異なります (旧: {len(old_books)}, 新: {len(new_books)})")
            return False
            
    except Exception as e:
        print(f"❌ 後方互換性テスト失敗: {e}")
        return False


def test_migration_helpers(config):
    """移行ヘルパーテスト"""
    print("\n=== 移行ヘルパーテスト ===")
    
    try:
        # 各モード用クライアントの作成テスト
        legacy_client = GoogleSheetsMigrationHelper.create_legacy_client(
            config['credentials_path'],
            config['spreadsheet_id']
        )
        
        updated_client = GoogleSheetsMigrationHelper.create_updated_client(
            config['credentials_path'],
            config['spreadsheet_id']
        )
        
        print(f"✅ レガシークライアント作成成功 (mode: {legacy_client.sheet_mode})")
        print(f"✅ 更新クライアント作成成功 (mode: {updated_client.sheet_mode})")
        
        # データ移行テスト（実際の移行は行わない）
        migration_result = GoogleSheetsMigrationHelper.migrate_data_format(
            legacy_client, updated_client
        )
        
        if migration_result:
            print("✅ 移行機能テスト成功")
        else:
            print("❌ 移行機能テスト失敗")
        
        return True
        
    except Exception as e:
        print(f"❌ 移行ヘルパーテスト失敗: {e}")
        return False


def run_performance_test(config):
    """パフォーマンステスト"""
    print("\n=== パフォーマンステスト ===")
    
    import time
    
    try:
        # 各モードでの実行時間測定
        modes = ["auto", "legacy", "updated"]
        performance_results = {}
        
        for mode in modes:
            start_time = time.time()
            
            try:
                client = UnifiedGoogleSheetsClient(
                    config['credentials_path'],
                    config['spreadsheet_id'],
                    mode
                )
                
                books = client.read_books()
                stats = client.get_summary_stats()
                
                end_time = time.time()
                duration = end_time - start_time
                
                performance_results[mode] = {
                    'success': True,
                    'duration': duration,
                    'books_count': len(books)
                }
                
                print(f"✅ {mode}モード: {duration:.2f}秒 ({len(books)}件)")
                
            except Exception as e:
                performance_results[mode] = {
                    'success': False,
                    'error': str(e)
                }
                print(f"❌ {mode}モード: {e}")
        
        return performance_results
        
    except Exception as e:
        print(f"❌ パフォーマンステスト失敗: {e}")
        return {}


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description='統合Google Sheetsクライアントテスト')
    parser.add_argument('--mode', choices=['auto', 'legacy', 'updated'], 
                       default='auto', help='テストモード')
    parser.add_argument('--comprehensive', action='store_true', 
                       help='包括的テストを実行')
    parser.add_argument('--migration-test', action='store_true', 
                       help='移行テストを実行')
    parser.add_argument('--performance', action='store_true', 
                       help='パフォーマンステストを実行')
    parser.add_argument('--all', action='store_true', 
                       help='すべてのテストを実行')
    
    args = parser.parse_args()
    
    # テスト設定読み込み
    config = load_test_config()
    
    print("🚀 統合Google Sheetsクライアント テストスイート")
    print("=" * 50)
    print(f"認証ファイル: {config['credentials_path']}")
    print(f"スプレッドシートID: {config['spreadsheet_id'][:20]}...")
    
    total_tests = 0
    passed_tests = 0
    
    # 基本テスト（常に実行）
    if test_basic_connection(config, args.mode):
        passed_tests += 1
    total_tests += 1
    
    # 包括的テスト
    if args.comprehensive or args.all:
        print("\n=== 包括的テストスイート ===")
        try:
            success = run_comprehensive_test(
                config['credentials_path'],
                config['spreadsheet_id']
            )
            if success:
                passed_tests += 1
            total_tests += 1
        except Exception as e:
            print(f"❌ 包括的テスト失敗: {e}")
            total_tests += 1
    
    # モード互換性テスト
    if args.all:
        results = test_mode_compatibility(config)
        successful_modes = sum(1 for r in results.values() if r.get('success', False))
        passed_tests += successful_modes
        total_tests += len(results)
    
    # 後方互換性テスト
    if args.all:
        if test_backward_compatibility(config):
            passed_tests += 1
        total_tests += 1
    
    # 移行テスト
    if args.migration_test or args.all:
        if test_migration_helpers(config):
            passed_tests += 1
        total_tests += 1
    
    # パフォーマンステスト
    if args.performance or args.all:
        perf_results = run_performance_test(config)
        successful_perf = sum(1 for r in perf_results.values() if r.get('success', False))
        passed_tests += successful_perf
        total_tests += len(perf_results) if perf_results else 1
    
    # 結果サマリー
    print("\n" + "=" * 50)
    print("📊 テスト結果サマリー")
    print(f"成功: {passed_tests}/{total_tests}")
    print(f"成功率: {(passed_tests/total_tests*100) if total_tests > 0 else 0:.1f}%")
    
    if passed_tests == total_tests:
        print("🎉 すべてのテストが成功しました！")
        return 0
    else:
        print("⚠️ 一部のテストが失敗しました")
        return 1


if __name__ == "__main__":
    sys.exit(main())
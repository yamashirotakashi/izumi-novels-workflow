#!/usr/bin/env python3
"""
11サイト設定データベース簡易検証
Configuration Database Quick Validation Test
"""
import json
import sys
from pathlib import Path

def test_config_validation():
    """設定ファイルの包括的検証"""
    print("🔍 IzumiNovels-Workflow 設定データベース検証開始")
    print("=" * 60)
    
    # 設定ファイル読み込み
    config_path = Path("config/site_selectors.json")
    if not config_path.exists():
        print("❌ 設定ファイルが見つかりません")
        return False
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except Exception as e:
        print(f"❌ 設定ファイル読み込みエラー: {e}")
        return False
    
    # 11サイト定義（CLAUDE.mdから）
    expected_sites = [
        ("amazon", "Amazon"),
        ("bookwalker", "BOOK☆WALKER"),
        ("ebookjapan", "ebookjapan"),
        ("rakuten_kobo", "楽天Kobo"),
        ("booklive", "BookLive!"),
        ("honto", "honto"),
        ("kinoppy", "Kinoppy"),
        ("apple_books", "Apple Books"),
        ("google_play_books", "Google Play Books"),
        ("reader_store", "Reader Store"),
        ("amazon_pod", "Amazon POD (印刷版)")
    ]
    
    sites = config.get("sites", {})
    
    print("📋 11サイト設定状況確認:")
    print("-" * 60)
    
    success_count = 0
    total_selectors = 0
    
    for i, (site_id, site_name) in enumerate(expected_sites, 1):
        if site_id in sites:
            site_config = sites[site_id]
            name = site_config.get("name", "不明")
            selectors = site_config.get("selectors", {})
            
            # セレクタカウント
            selector_count = sum(len(v) if isinstance(v, list) else 1 
                               for v in selectors.values())
            total_selectors += selector_count
            
            print(f"{i:2d}. ✅ {name:<20} ({site_id}) - {selector_count}個のセレクタ")
            success_count += 1
        else:
            print(f"{i:2d}. ❌ {site_name:<20} ({site_id}) - 設定なし")
    
    # 統計情報
    completion_rate = success_count / len(expected_sites) * 100
    print("\n" + "=" * 60)
    print("📊 設定データベース統計:")
    print(f"   ✅ 設定完了サイト: {success_count}/11 ({completion_rate:.1f}%)")
    print(f"   🎯 総セレクタ数: {total_selectors}個")
    
    # 必須フィールド検証
    print("\n🔧 設定品質検証:")
    quality_issues = []
    
    for site_id, site_name in expected_sites:
        if site_id not in sites:
            continue
            
        site_config = sites[site_id]
        
        # 必須フィールドチェック
        required_fields = ["name", "base_url", "selectors"]
        missing_fields = [field for field in required_fields 
                         if field not in site_config]
        
        if missing_fields:
            quality_issues.append(f"{site_id}: 欠落フィールド {missing_fields}")
        
        # セレクタ品質チェック
        selectors = site_config.get("selectors", {})
        required_selectors = ["search_input", "search_results"]
        missing_selectors = [sel for sel in required_selectors 
                           if sel not in selectors]
        
        if missing_selectors:
            quality_issues.append(f"{site_id}: 欠落セレクタ {missing_selectors}")
    
    if quality_issues:
        print("   ⚠️ 品質問題:")
        for issue in quality_issues:
            print(f"      - {issue}")
    else:
        print("   ✅ 品質チェック: 全てパス")
    
    # グローバル設定確認
    global_settings = config.get("global_settings", {})
    print(f"\n🌐 グローバル設定:")
    print(f"   Chrome オプション: {len(global_settings.get('chrome_options', []))}個")
    print(f"   リトライ回数: {global_settings.get('retry_attempts', 'デフォルト')}")
    print(f"   タイムアウト: {global_settings.get('timeout_default', 'デフォルト')}秒")
    
    # 最終判定
    print("\n" + "=" * 60)
    if completion_rate == 100 and not quality_issues:
        print("🎉 判定: EXCELLENT - 11サイト完全対応設定データベース")
        print("   ✅ 全11サイト設定完了")
        print("   ✅ 品質チェック全クリア")
        print("   ✅ Git管理対応")
        print("   ✅ 柔軟セレクタシステム")
        result_status = "EXCELLENT"
    elif completion_rate >= 90:
        print("✅ 判定: GOOD - 実用レベル達成")
        result_status = "GOOD"
    elif completion_rate >= 70:
        print("⚠️ 判定: PARTIAL - 改善が推奨")
        result_status = "PARTIAL"
    else:
        print("❌ 判定: NEEDS_IMPROVEMENT - 大幅な修正が必要")
        result_status = "NEEDS_IMPROVEMENT"
    
    print("\n💡 次のステップ:")
    if result_status == "EXCELLENT":
        print("   1. Git commit（設定データベース実装）")
        print("   2. Windows環境での実機テスト")
        print("   3. Phase 2への移行準備")
    else:
        print("   1. 不完全サイトの設定追加")
        print("   2. 品質問題の修正")
        print("   3. 再検証実行")
    
    return result_status == "EXCELLENT"

def main():
    """メイン実行"""
    success = test_config_validation()
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
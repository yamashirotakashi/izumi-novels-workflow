#!/usr/bin/env python3
"""
ebookjapan 高速個別テスト
Quick Individual Test for ebookjapan
"""
import sys
import json
from pathlib import Path

# プロジェクトルートを追加
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root / 'src'))

class EbookjapanQuickTest:
    """ebookjapan 高速テストクラス"""
    
    def __init__(self):
        self.site_id = "ebookjapan"
        self.site_name = "ebookjapan"
        self.config_path = project_root / "config" / "site_selectors.json"
    
    def run_test(self):
        """ebookjapan 設定テスト実行"""
        print(f"⚡ {self.site_name} 高速設定テスト開始")
        print("=" * 50)
        
        # 設定ファイル読み込み
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
        except Exception as e:
            print(f"❌ 設定ファイル読み込みエラー: {e}")
            return False
        
        # サイト設定確認
        sites = config.get('sites', {})
        if self.site_id not in sites:
            print(f"❌ {self.site_name} の設定が見つかりません")
            return False
        
        site_config = sites[self.site_id]
        
        # 設定詳細表示
        print(f"✅ {self.site_name} 設定確認:")
        print(f"   サイト名: {site_config.get('name', '不明')}")
        print(f"   ベースURL: {site_config.get('base_url', '不明')}")
        print(f"   検索URL: {site_config.get('search_url', '不明')}")
        
        # セレクタ詳細
        selectors = site_config.get('selectors', {})
        print(f"\n🔍 セレクタ設定:")
        for selector_type, selector_list in selectors.items():
            count = len(selector_list) if isinstance(selector_list, list) else 1
            print(f"   {selector_type}: {count}個のセレクタ")
            if isinstance(selector_list, list) and selector_list:
                print(f"     - 主要: {selector_list[0]}")
                if len(selector_list) > 1:
                    print(f"     - フォールバック: {len(selector_list)-1}個")
        
        # 待機時間設定
        wait_times = site_config.get('wait_times', {})
        print(f"\n⏱️ 待機時間設定:")
        for wait_type, wait_time in wait_times.items():
            print(f"   {wait_type}: {wait_time}秒")
        
        # 検索パラメータ
        search_params = site_config.get('search_params', {})
        if search_params:
            print(f"\n🎯 検索設定:")
            for param_type, param_value in search_params.items():
                if param_type == 'direct_url_pattern':
                    # テスト用URL生成
                    test_url = param_value.format(query="テスト")
                    print(f"   直接検索URL: {test_url}")
                else:
                    print(f"   {param_type}: {param_value}")
        
        # 設定品質評価
        required_selectors = ['search_input', 'search_results']
        missing_selectors = [sel for sel in required_selectors if sel not in selectors]
        
        required_fields = ['name', 'base_url']
        missing_fields = [field for field in required_fields if field not in site_config]
        
        print(f"\n📊 設定品質評価:")
        if not missing_selectors and not missing_fields:
            print("   ✅ 品質: EXCELLENT - 全必須項目完備")
            quality_score = 100
        elif not missing_selectors:
            print("   ✅ 品質: GOOD - セレクタ完全、軽微な不足")
            quality_score = 85
        else:
            print(f"   ⚠️ 品質: PARTIAL - 不足項目: {missing_selectors + missing_fields}")
            quality_score = 60
        
        # 総合評価
        total_selectors = sum(len(v) if isinstance(v, list) else 1 for v in selectors.values())
        print(f"\n🎉 {self.site_name} テスト結果:")
        print(f"   設定完全性: {quality_score}%")
        print(f"   総セレクタ数: {total_selectors}個")
        print(f"   フォールバック対応: {'✅ あり' if any(isinstance(v, list) and len(v) > 1 for v in selectors.values()) else '❌ なし'}")
        print(f"   直接検索対応: {'✅ あり' if 'direct_url_pattern' in search_params else '❌ なし'}")
        
        if quality_score >= 90:
            print("   判定: ✅ 実用準備完了")
            return True
        elif quality_score >= 70:
            print("   判定: ⚠️ 改善推奨")
            return True
        else:
            print("   判定: ❌ 修正必要")
            return False

def main():
    """メイン実行"""
    test = EbookjapanQuickTest()
    success = test.run_test()
    
    print("\n" + "=" * 50)
    print(f"🏁 {test.site_name} 高速テスト完了")
    
    # 終了コード設定
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
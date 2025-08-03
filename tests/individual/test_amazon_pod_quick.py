#!/usr/bin/env python3
"""
Amazon POD 高速 items別test
Quick Individual Test for Amazon POD (Print On Demand)
"""
import sys
import json
from pathlib import Path

# プロジェクトルートを追加
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root / 'src'))

class AmazonPodQuickTest:
    """Amazon POD 高速testクラス"""
    
    def __init__(self):
        self.site_id = "amazon_pod"
        self.site_name = "Amazon POD (印刷版)"
        self.config_path = project_root / "config" / "site_selectors.json"
    
    def run_test(self):
        """Amazon POD 設定test実行"""
        print(f"[QUICK] {self.site_name} Quick Setup Test Started")
        print("=" * 50)
        
        # 設定ファイル読み込み
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
        except Exception as e:
            print(f"[FAIL] Config file load error: {e}")
            return False
        
        # サイトConfig Check
        sites = config.get('sites', {})
        if self.site_id not in sites:
            print(f"[FAIL] {self.site_name} config not found")
            return False
        
        site_config = sites[self.site_id]
        
        # 設定詳細表示
        print(f"[OK] {self.site_name} Config Check:")
        print(f"   Site Name: {site_config.get('name', 'Unknown')}")
        print(f"   Base URL: {site_config.get('base_url', 'Unknown')}")
        print(f"   Search URL: {site_config.get('search_url', 'Unknown')}")
        
        # セレクタ詳細
        selectors = site_config.get('selectors', {})
        print(f"\n[CHECK] Selector Config:")
        for selector_type, selector_list in selectors.items():
            count = len(selector_list) if isinstance(selector_list, list) else 1
            print(f"   {selector_type}: {count} selectors")
            if isinstance(selector_list, list) and selector_list:
                print(f"     - Primary: {selector_list[0]}")
                if len(selector_list) > 1:
                    print(f"     - Fallback: {len(selector_list)-1} items")
        
        # Wait Time Settings
        wait_times = site_config.get('wait_times', {})
        print(f"\n[TIME] Wait Time Settings:")
        for wait_type, wait_time in wait_times.items():
            print(f"   {wait_type}: {wait_time}sec")
        
        # 検索パラメータ
        search_params = site_config.get('search_params', {})
        if search_params:
            print(f"\n[TARGET] Search Config:")
            for param_type, param_value in search_params.items():
                if param_type == 'direct_url_pattern':
                    # test用URL生成
                    test_url = param_value.format(query="test")
                    print(f"   直接Search URL: {test_url}")
                else:
                    print(f"   {param_type}: {param_value}")
        
        # Config Quality Assessment
        required_selectors = ['search_input', 'search_results']
        missing_selectors = [sel for sel in required_selectors if sel not in selectors]
        
        required_fields = ['name', 'base_url']
        missing_fields = [field for field in required_fields if field not in site_config]
        
        print(f"\n[STATS] Config Quality Assessment:")
        if not missing_selectors and not missing_fields:
            print("   [OK] Quality: EXCELLENT - All required items complete")
            quality_score = 100
        elif not missing_selectors:
            print("   [OK] Quality: GOOD - Selectors complete, minor issues")
            quality_score = 85
        else:
            print(f"   [WARN] Quality: PARTIAL - Missing items: {missing_selectors + missing_fields}")
            quality_score = 60
        
        # 総合評価
        total_selectors = sum(len(v) if isinstance(v, list) else 1 for v in selectors.values())
        print(f"\n[RESULT] {self.site_name} Test Results:")
        print(f"   Config Completeness: {quality_score}%")
        print(f"   Total Selectors: {total_selectors} items")
        print(f"   Fallback Support: {'[OK] Available' if any(isinstance(v, list) and len(v) > 1 for v in selectors.values()) else '[FAIL] None'}")
        print(f"   Direct Search Support: {'[OK] Available' if 'direct_url_pattern' in search_params else '[FAIL] None'}")
        
        if quality_score >= 90:
            print("   Result: [OK] Ready for Production")
            return True
        elif quality_score >= 70:
            print("   Result: [WARN] Improvement Recommended")
            return True
        else:
            print("   Result: [FAIL] Fix Required")
            return False

def main():
    """Main Execution"""
    test = AmazonPodQuickTest()
    success = test.run_test()
    
    print("\n" + "=" * 50)
    print(f"[FINISH] {test.site_name} Quick Test Completed")
    
    # Set exit code
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
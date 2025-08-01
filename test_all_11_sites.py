#!/usr/bin/env python3
"""
11サイト完全対応テスト
IzumiNovels-Workflow 全サイトスクレイピング検証
"""
import sys
import asyncio
from pathlib import Path

# プロジェクトルートを追加
project_root = Path(__file__).parent
sys.path.append(str(project_root / 'src'))

from core.flexible_scraper import FlexibleScraper

class ElevenSitesTest:
    """11サイト完全テスト"""
    
    def __init__(self):
        self.scraper = FlexibleScraper()
        self.test_query = "課長が目覚めたら異世界SF艦隊の提督になってた件です"
        
        # 11サイトの定義（CLAUDE.mdに記載された順序）
        self.target_sites = [
            # 電子書籍版（10サイト）
            "amazon",           # 1. Amazon Kindle
            "bookwalker",       # 2. BOOK☆WALKER  
            "ebookjapan",       # 3. ebookjapan
            "rakuten_kobo",     # 4. 楽天Kobo
            "booklive",         # 5. BookLive
            "honto",            # 6. honto
            "kinoppy",          # 7. 紀伊國屋書店（Kinoppy）
            "apple_books",      # 8. Apple Books
            "google_play_books", # 9. Google Play Books
            "reader_store",     # 10. Reader Store（Sony）
            
            # 印刷版（1サイト）
            "amazon_pod"        # 11. Amazon POD
        ]
    
    def show_site_status(self):
        """サイト設定状況表示"""
        print("📋 11サイト設定状況確認")
        print("=" * 60)
        
        available_sites = self.scraper.get_available_sites()
        
        for i, site in enumerate(self.target_sites, 1):
            status = "✅" if site in available_sites else "❌"
            site_name = self.scraper.config["sites"].get(site, {}).get("name", "未設定")
            print(f"{i:2d}. {status} {site_name:<20} ({site})")
        
        configured_count = sum(1 for site in self.target_sites if site in available_sites)
        print(f"\n📊 設定完了: {configured_count}/11 サイト ({configured_count/11*100:.1f}%)")
        
        return configured_count == 11
    
    async def run_comprehensive_test(self):
        """包括的テスト実行"""
        print("🚀 IzumiNovels-Workflow 11サイト完全テスト開始")
        print("=" * 70)
        
        # サイト設定確認
        all_configured = self.show_site_status()
        if not all_configured:
            print("\n⚠️ 一部サイトの設定が不完全です")
            print("設定されているサイトのみでテストを続行します...\n")
        
        # WebDriverセットアップ
        print("\n🔧 Chrome WebDriverセットアップ中...")
        self.scraper.setup_driver()
        
        try:
            # 実行可能サイトのフィルタリング
            available_sites = self.scraper.get_available_sites()
            test_sites = [site for site in self.target_sites if site in available_sites]
            
            print(f"\n🎯 テスト対象: {len(test_sites)}サイト")
            print(f"検索クエリ: '{self.test_query}'")
            print("\n" + "=" * 70)
            
            # 各サイトでテスト実行
            results = []
            for i, site in enumerate(test_sites, 1):
                print(f"\n[{i}/{len(test_sites)}] {site} テスト実行中...")
                
                try:
                    result = self.scraper.search_site(site, self.test_query)
                    results.append(result)
                    
                    # 結果の簡易表示
                    status_icon = "✅" if result.status == "SUCCESS" else ("⚠️" if result.status == "NO_RESULTS" else "❌")
                    print(f"    {status_icon} {result.site}: {result.results_count}件")
                    
                except Exception as e:
                    print(f"    ❌ {site}: エラー - {e}")
                    results.append({
                        'site': site,
                        'status': 'ERROR',
                        'error_message': str(e)
                    })
            
            # 最終結果表示
            self.show_final_results(results)
            return results
            
        finally:
            self.scraper.cleanup()
    
    def show_final_results(self, results):
        """最終結果表示"""
        print("\n" + "=" * 80)
        print("📊 11サイト完全テスト最終結果")
        print("=" * 80)
        
        # カテゴリ別結果
        success_sites = []
        partial_sites = []
        failed_sites = []
        
        for result in results:
            if hasattr(result, 'status'):
                if result.status == "SUCCESS":
                    success_sites.append((result.site, result.results_count))
                elif result.status == "NO_RESULTS":
                    partial_sites.append((result.site, "検索実行したが結果なし"))
                else:
                    failed_sites.append((result.site, result.error_message if hasattr(result, 'error_message') else "エラー"))
            else:
                failed_sites.append((result['site'], result.get('error_message', 'Unknown error')))
        
        # 成功サイト
        if success_sites:
            print(f"\n✅ 成功サイト ({len(success_sites)}個):")
            for site, count in success_sites:
                print(f"   🎯 {site}: {count}件の検索結果")
        
        # 部分成功サイト
        if partial_sites:
            print(f"\n⚠️ 部分成功サイト ({len(partial_sites)}個):")
            for site, message in partial_sites:
                print(f"   🔍 {site}: {message}")
        
        # 失敗サイト
        if failed_sites:
            print(f"\n❌ 失敗サイト ({len(failed_sites)}個):")
            for site, error in failed_sites:
                print(f"   ⚡ {site}: {error}")
        
        # 統計
        total_sites = len(results)
        success_rate = len(success_sites) / total_sites * 100 if total_sites > 0 else 0
        operational_rate = (len(success_sites) + len(partial_sites)) / total_sites * 100 if total_sites > 0 else 0
        
        print(f"\n📈 最終統計:")
        print(f"   🎯 完全成功率: {len(success_sites)}/{total_sites} ({success_rate:.1f}%)")
        print(f"   🔄 動作成功率: {len(success_sites) + len(partial_sites)}/{total_sites} ({operational_rate:.1f}%)")
        print(f"   ❌ 失敗率: {len(failed_sites)}/{total_sites} ({len(failed_sites)/total_sites*100:.1f}%)")
        
        # 判定
        if success_rate >= 70:
            print("\n🎉 判定: EXCELLENT - 本格運用可能")
        elif operational_rate >= 70:
            print("\n✅ 判定: GOOD - 実用レベル達成")
        elif operational_rate >= 50:
            print("\n⚠️ 判定: PARTIAL - 改善が推奨")
        else:
            print("\n❌ 判定: NEEDS_IMPROVEMENT - 大幅な修正が必要")
        
        print("\n💡 推奨次ステップ:")
        if failed_sites:
            print("   1. 失敗サイトのセレクタ調整")
        if partial_sites:
            print("   2. 部分成功サイトの検索結果抽出改善")
        if success_rate >= 70:
            print("   3. Phase 2への移行準備")
        
        return {
            'success_rate': success_rate,
            'operational_rate': operational_rate,
            'success_sites': len(success_sites),
            'total_sites': total_sites
        }

async def main():
    """メイン実行関数"""
    test = ElevenSitesTest()
    
    try:
        results = await test.run_comprehensive_test()
        return results
    except KeyboardInterrupt:
        print("\n⚠️ ユーザーによるテスト中断")
    except Exception as e:
        print(f"\n❌ 予期しないエラー: {e}")
    finally:
        print("\n🏁 11サイト完全テスト終了")

if __name__ == '__main__':
    asyncio.run(main())
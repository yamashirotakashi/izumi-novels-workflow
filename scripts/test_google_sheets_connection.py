#!/usr/bin/env python3
"""
Google Sheets接続テストスクリプト
実際のスプレッドシートとの接続を確認
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import logging

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.scraping.google_sheets_client_consolidated import (
    GoogleSheetsClient, 
    SalesChannel,
    test_connection
)

# ロガー設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """メイン処理"""
    # 環境変数の読み込み
    load_dotenv()
    
    # 設定値の取得
    credentials_path = os.getenv('GOOGLE_SHEETS_CREDENTIALS_PATH', 'config/credentials/google-sheets-key.json')
    spreadsheet_id = os.getenv('GOOGLE_SHEETS_SPREADSHEET_ID')
    if not spreadsheet_id:
        print("❌ GOOGLE_SHEETS_SPREADSHEET_IDが設定されていません")
        print("環境変数を設定するか.envファイルを作成してください")
        return
    
    print(f"=== Google Sheets接続テスト ===")
    print(f"認証ファイル: {credentials_path}")
    print(f"スプレッドシートID: {spreadsheet_id}")
    print()
    
    # 認証ファイルの存在確認
    if not os.path.exists(credentials_path):
        print(f"❌ 認証ファイルが見つかりません: {credentials_path}")
        print("Google Cloud Consoleから認証JSONファイルをダウンロードして配置してください。")
        return
    
    try:
        # クライアント初期化
        print("📊 Google Sheetsに接続中...")
        client = GoogleSheetsClient(credentials_path, spreadsheet_id)
        print("✅ 接続成功!")
        print()
        
        # 書籍データ読み取りテスト
        print("📖 書籍データを読み取り中...")
        books = client.read_all_books()
        print(f"✅ {len(books)}件の書籍データを取得しました")
        print()
        
        # サンプルデータの表示
        if books:
            print("--- サンプルデータ（最初の3件） ---")
            for i, book in enumerate(books[:3]):
                print(f"\n書籍 {i+1}:")
                print(f"  行番号: {book.row_number}")
                print(f"  Nコード: {book.n_code}")
                print(f"  タイトル: {book.title}")
                print(f"  登録済みリンク数: {len(book.sales_links)}")
                if book.sales_links:
                    print(f"  登録済みサイト: {', '.join(book.sales_links.keys())}")
        print()
        
        # リンク未設定の書籍を確認
        print("🔍 リンク未設定の書籍を検索中...")
        books_without_links = client.get_books_without_links()
        print(f"📌 {len(books_without_links)}件の書籍でリンクが不足しています")
        
        if books_without_links:
            print("\n--- リンク不足の書籍（最初の3件） ---")
            for book in books_without_links[:3]:
                missing_channels = [
                    ch.display_name for ch in SalesChannel 
                    if ch.display_name not in book.sales_links
                ]
                print(f"\n{book.n_code} - {book.title}")
                print(f"  不足: {', '.join(missing_channels[:5])}{'...' if len(missing_channels) > 5 else ''}")
        print()
        
        # 統計情報の表示
        print("📊 収集統計:")
        stats = client.get_summary_stats()
        print(f"  総書籍数: {stats['total_books']}")
        print(f"  期待リンク数: {stats['total_links_expected']}")
        print(f"  収集済みリンク数: {stats['total_links_collected']}")
        print(f"  収集率: {stats['collection_rate']:.1f}%")
        print()
        
        print("📈 チャンネル別収集率:")
        for channel_name, channel_stats in stats['channel_stats'].items():
            print(f"  {channel_name}: {channel_stats['collected']}/{channel_stats['total']} "
                  f"({channel_stats['percentage']:.1f}%)")
        
        print("\n✅ すべてのテストが正常に完了しました！")
        
    except Exception as e:
        print(f"\n❌ エラーが発生しました: {e}")
        logger.exception("詳細なエラー情報:")
        
        # トラブルシューティングのヒント
        print("\n💡 トラブルシューティング:")
        print("1. サービスアカウントのメールアドレスをスプレッドシートに共有していますか？")
        print("2. 編集権限を付与していますか？")
        print("3. Google Sheets APIが有効になっていますか？")
        print("4. スプレッドシートIDが正しいですか？")


if __name__ == "__main__":
    main()
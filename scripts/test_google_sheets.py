#!/usr/bin/env python3
"""
Google Sheets API接続テストスクリプト
環境変数から設定を読み込み、基本的な操作をテストします
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime
import logging

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.scraping.google_sheets_client import (
    GoogleSheetsClient, 
    BookMaster, 
    SalesLinkRecord,
    test_connection
)

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """メイン処理"""
    # 環境変数の読み込み
    load_dotenv()
    
    credentials_path = os.getenv('GOOGLE_SHEETS_CREDENTIALS_PATH')
    spreadsheet_id = os.getenv('GOOGLE_SHEETS_SPREADSHEET_ID')
    
    # 環境変数チェック
    if not credentials_path:
        logger.error("環境変数 GOOGLE_SHEETS_CREDENTIALS_PATH が設定されていません")
        logger.info("以下の手順で設定してください:")
        logger.info("1. .env.example を .env にコピー")
        logger.info("2. GOOGLE_SHEETS_CREDENTIALS_PATH にJSONファイルのパスを設定")
        return
    
    if not spreadsheet_id:
        logger.error("環境変数 GOOGLE_SHEETS_SPREADSHEET_ID が設定されていません")
        logger.info("Google SheetsのURLから SPREADSHEET_ID をコピーして設定してください")
        logger.info("例: https://docs.google.com/spreadsheets/d/[SPREADSHEET_ID]/edit")
        return
    
    # ファイル存在チェック
    if not os.path.exists(credentials_path):
        logger.error(f"認証ファイルが見つかりません: {credentials_path}")
        logger.info("Google Cloud Consoleからサービスアカウントキーをダウンロードしてください")
        return
    
    print("=" * 60)
    print("Google Sheets API 接続テスト")
    print("=" * 60)
    
    # 1. 接続テスト
    print("\n1. 接続テスト...")
    if not test_connection(credentials_path, spreadsheet_id):
        logger.error("接続テストに失敗しました")
        return
    print("✅ 接続成功")
    
    # クライアント初期化
    client = GoogleSheetsClient(credentials_path, spreadsheet_id)
    
    # 2. 必要なシートの作成
    print("\n2. 必要なシートの確認・作成...")
    try:
        client.create_required_sheets()
        print("✅ シート準備完了")
    except Exception as e:
        logger.error(f"シート作成エラー: {e}")
        return
    
    # 3. マスターデータの読み取り
    print("\n3. マスターデータの読み取り...")
    try:
        books = client.read_master_books()
        if books:
            print(f"✅ {len(books)}件の書籍データを取得")
            for book in books[:3]:  # 最初の3件のみ表示
                print(f"  - {book.n_code}: {book.title} 第{book.volume}巻 ({book.status})")
            if len(books) > 3:
                print(f"  ... 他 {len(books) - 3}件")
        else:
            print("📝 マスターデータが空です。サンプルデータを追加しますか？ (y/n): ", end="")
            if input().lower() == 'y':
                add_sample_data(client)
    except Exception as e:
        logger.error(f"データ読み取りエラー: {e}")
        return
    
    # 4. 未収集書籍の確認
    print("\n4. 未収集書籍の確認...")
    try:
        pending_books = client.get_pending_books()
        print(f"✅ {len(pending_books)}件の未収集書籍があります")
        for book in pending_books[:3]:
            print(f"  - {book.n_code}: {book.title}")
    except Exception as e:
        logger.error(f"未収集書籍確認エラー: {e}")
    
    # 5. 販売リンクのテスト追加
    print("\n5. 販売リンクのテスト追加...")
    if books and len(books) > 0:
        test_book = books[0]
        print(f"テスト書籍: {test_book.title}")
        
        # サンプルリンクデータ
        sample_links = [
            SalesLinkRecord(
                link_id=f"test_{test_book.n_code}_amazon_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                n_code=test_book.n_code,
                site_name="Amazon Kindle",
                url="https://www.amazon.co.jp/dp/B0XXXXXXX",
                price=1320,
                scraped_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                is_valid=True
            ),
            SalesLinkRecord(
                link_id=f"test_{test_book.n_code}_rakuten_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                n_code=test_book.n_code,
                site_name="楽天Kobo",
                url="https://books.rakuten.co.jp/rk/xxxxx",
                price=1320,
                scraped_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                is_valid=True
            )
        ]
        
        try:
            if client.append_sales_links(sample_links):
                print("✅ テストリンクを追加しました")
            else:
                print("❌ リンク追加に失敗しました")
        except Exception as e:
            logger.error(f"リンク追加エラー: {e}")
    
    # 6. ステータス更新テスト
    print("\n6. ステータス更新テスト...")
    if books and len(books) > 0:
        test_book = books[0]
        try:
            if client.update_book_status(test_book.n_code, "収集中"):
                print(f"✅ {test_book.n_code} のステータスを「収集中」に更新")
                
                # 元に戻す
                if client.update_book_status(test_book.n_code, test_book.status):
                    print(f"✅ ステータスを元に戻しました: {test_book.status}")
        except Exception as e:
            logger.error(f"ステータス更新エラー: {e}")
    
    # 7. 実行ログ記録
    print("\n7. 実行ログ記録...")
    try:
        client.log_execution(
            process_type="接続テスト",
            target_count=len(books) if books else 0,
            success_count=len(books) if books else 0,
            failure_count=0,
            duration_seconds=5,
            details="Google Sheets API接続テスト実行"
        )
        print("✅ 実行ログを記録しました")
    except Exception as e:
        logger.error(f"ログ記録エラー: {e}")
    
    print("\n" + "=" * 60)
    print("✨ すべてのテストが完了しました！")
    print("=" * 60)


def add_sample_data(client: GoogleSheetsClient):
    """サンプルデータを追加"""
    sample_books = [
        ['n1234567', '異世界転生した件', '1', '2025/02/15', '未収集', '', 'サンプル書籍1'],
        ['n2345678', '魔法使いになりたくて', '3', '2025/02/20', '未収集', '', 'サンプル書籍2'],
        ['n3456789', '勇者のその後', '5', '2025/03/01', '未収集', '', 'サンプル書籍3']
    ]
    
    try:
        body = {'values': sample_books}
        result = client.sheet.values().append(
            spreadsheetId=client.spreadsheet_id,
            range=f'{client.MASTER_SHEET}!A2',
            valueInputOption='USER_ENTERED',
            body=body
        ).execute()
        
        print(f"✅ {len(sample_books)}件のサンプルデータを追加しました")
    except Exception as e:
        logger.error(f"サンプルデータ追加エラー: {e}")


if __name__ == "__main__":
    main()
"""
Google Sheets APIクライアント
いずみノベルズの書籍情報と販売リンクを管理
"""
import os
from typing import List, Dict, Optional, Any
from datetime import datetime
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import logging
from dataclasses import dataclass

# ロガー設定
logger = logging.getLogger(__name__)


@dataclass
class BookMaster:
    """書籍マスターデータ"""
    n_code: str
    title: str
    volume: int
    release_date: str
    status: str
    last_updated: Optional[str] = None
    notes: Optional[str] = None


@dataclass
class SalesLinkRecord:
    """販売リンクレコード"""
    link_id: str
    n_code: str
    site_name: str
    url: str
    price: Optional[int] = None
    scraped_at: str = None
    is_valid: bool = True
    error: Optional[str] = None


class GoogleSheetsClient:
    """Google Sheets APIクライアント"""
    
    # シート名の定義
    MASTER_SHEET = "マスター"
    SALES_LINKS_SHEET = "販売リンク"
    LOG_SHEET = "実行ログ"
    
    def __init__(self, credentials_path: str, spreadsheet_id: str):
        """
        Args:
            credentials_path: サービスアカウントJSONファイルのパス
            spreadsheet_id: スプレッドシートID
        """
        self.spreadsheet_id = spreadsheet_id
        
        # 認証情報の読み込み
        if not os.path.exists(credentials_path):
            raise FileNotFoundError(f"認証ファイルが見つかりません: {credentials_path}")
            
        self.creds = Credentials.from_service_account_file(
            credentials_path,
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        )
        
        # APIクライアントの構築
        self.service = build('sheets', 'v4', credentials=self.creds)
        self.sheet = self.service.spreadsheets()
        
        logger.info(f"Google Sheetsクライアントを初期化しました: {spreadsheet_id}")
    
    def read_master_books(self) -> List[BookMaster]:
        """マスターシートから書籍データを読み取る"""
        try:
            result = self.sheet.values().get(
                spreadsheetId=self.spreadsheet_id,
                range=f'{self.MASTER_SHEET}!A2:G'  # ヘッダーを除く全行
            ).execute()
            
            values = result.get('values', [])
            books = []
            
            for row in values:
                # 行データを正規化（不足分は空文字で埋める）
                row_data = row + [''] * (7 - len(row))
                
                book = BookMaster(
                    n_code=row_data[0],
                    title=row_data[1],
                    volume=int(row_data[2]) if row_data[2].isdigit() else 0,
                    release_date=row_data[3],
                    status=row_data[4],
                    last_updated=row_data[5] if row_data[5] else None,
                    notes=row_data[6] if row_data[6] else None
                )
                books.append(book)
            
            logger.info(f"{len(books)}件の書籍データを読み取りました")
            return books
            
        except HttpError as e:
            logger.error(f"マスターシート読み取りエラー: {e}")
            raise
    
    def get_pending_books(self) -> List[BookMaster]:
        """未収集ステータスの書籍のみ取得"""
        all_books = self.read_master_books()
        pending_books = [book for book in all_books if book.status in ['未収集', 'エラー']]
        logger.info(f"{len(pending_books)}件の未収集書籍があります")
        return pending_books
    
    def update_book_status(self, n_code: str, status: str, timestamp: str = None):
        """書籍のステータスを更新"""
        try:
            # まず該当行を検索
            all_books = self.read_master_books()
            row_index = None
            
            for i, book in enumerate(all_books):
                if book.n_code == n_code:
                    row_index = i + 2  # ヘッダー行を考慮
                    break
            
            if row_index is None:
                logger.warning(f"N番号 {n_code} が見つかりません")
                return False
            
            # 更新データ
            if timestamp is None:
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            values = [[status, timestamp]]
            
            # 更新実行
            result = self.sheet.values().update(
                spreadsheetId=self.spreadsheet_id,
                range=f'{self.MASTER_SHEET}!E{row_index}:F{row_index}',
                valueInputOption='USER_ENTERED',
                body={'values': values}
            ).execute()
            
            logger.info(f"書籍ステータスを更新: {n_code} -> {status}")
            return True
            
        except HttpError as e:
            logger.error(f"ステータス更新エラー: {e}")
            return False
    
    def append_sales_links(self, links: List[SalesLinkRecord]) -> bool:
        """販売リンクをシートに追加"""
        try:
            # リンクデータを配列形式に変換
            values = []
            for link in links:
                values.append([
                    link.link_id,
                    link.n_code,
                    link.site_name,
                    link.url,
                    str(link.price) if link.price else '',
                    link.scraped_at,
                    'TRUE' if link.is_valid else 'FALSE',
                    link.error if link.error else ''
                ])
            
            # 一括追加
            body = {'values': values}
            result = self.sheet.values().append(
                spreadsheetId=self.spreadsheet_id,
                range=f'{self.SALES_LINKS_SHEET}!A2',
                valueInputOption='USER_ENTERED',
                insertDataOption='INSERT_ROWS',
                body=body
            ).execute()
            
            updated_cells = result.get('updates', {}).get('updatedCells', 0)
            logger.info(f"{len(links)}件の販売リンクを追加しました（{updated_cells}セル更新）")
            return updated_cells > 0
            
        except HttpError as e:
            logger.error(f"販売リンク追加エラー: {e}")
            return False
    
    def clear_sales_links_for_book(self, n_code: str) -> bool:
        """特定書籍の既存販売リンクをクリア"""
        try:
            # まず既存のリンクを検索
            result = self.sheet.values().get(
                spreadsheetId=self.spreadsheet_id,
                range=f'{self.SALES_LINKS_SHEET}!A2:H'
            ).execute()
            
            values = result.get('values', [])
            rows_to_delete = []
            
            # 削除対象の行を特定（逆順で処理）
            for i in range(len(values) - 1, -1, -1):
                if len(values[i]) > 1 and values[i][1] == n_code:
                    rows_to_delete.append(i + 2)  # シートの行番号
            
            # 行を削除（バッチリクエスト）
            if rows_to_delete:
                requests = []
                for row in sorted(rows_to_delete, reverse=True):
                    requests.append({
                        'deleteDimension': {
                            'range': {
                                'sheetId': self._get_sheet_id(self.SALES_LINKS_SHEET),
                                'dimension': 'ROWS',
                                'startIndex': row - 1,
                                'endIndex': row
                            }
                        }
                    })
                
                body = {'requests': requests}
                self.sheet.batchUpdate(
                    spreadsheetId=self.spreadsheet_id,
                    body=body
                ).execute()
                
                logger.info(f"{n_code}の{len(rows_to_delete)}件の既存リンクをクリアしました")
            
            return True
            
        except HttpError as e:
            logger.error(f"販売リンククリアエラー: {e}")
            return False
    
    def log_execution(self, 
                      process_type: str,
                      target_count: int,
                      success_count: int,
                      failure_count: int,
                      duration_seconds: int,
                      details: str = ""):
        """実行ログを記録"""
        try:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            values = [[
                timestamp,
                process_type,
                target_count,
                success_count,
                failure_count,
                duration_seconds,
                details
            ]]
            
            result = self.sheet.values().append(
                spreadsheetId=self.spreadsheet_id,
                range=f'{self.LOG_SHEET}!A2',
                valueInputOption='USER_ENTERED',
                insertDataOption='INSERT_ROWS',
                body={'values': values}
            ).execute()
            
            logger.info(f"実行ログを記録: {process_type}")
            
        except HttpError as e:
            logger.error(f"ログ記録エラー: {e}")
    
    def _get_sheet_id(self, sheet_name: str) -> int:
        """シート名からシートIDを取得"""
        try:
            sheet_metadata = self.sheet.get(
                spreadsheetId=self.spreadsheet_id
            ).execute()
            
            for sheet in sheet_metadata.get('sheets', []):
                if sheet['properties']['title'] == sheet_name:
                    return sheet['properties']['sheetId']
            
            raise ValueError(f"シート '{sheet_name}' が見つかりません")
            
        except HttpError as e:
            logger.error(f"シートID取得エラー: {e}")
            raise
    
    def create_required_sheets(self):
        """必要なシートが存在しない場合は作成"""
        try:
            # 既存のシートを確認
            sheet_metadata = self.sheet.get(
                spreadsheetId=self.spreadsheet_id
            ).execute()
            
            existing_sheets = [
                sheet['properties']['title'] 
                for sheet in sheet_metadata.get('sheets', [])
            ]
            
            required_sheets = [
                self.MASTER_SHEET,
                self.SALES_LINKS_SHEET,
                self.LOG_SHEET
            ]
            
            requests = []
            
            # 不足しているシートを作成
            for sheet_name in required_sheets:
                if sheet_name not in existing_sheets:
                    requests.append({
                        'addSheet': {
                            'properties': {
                                'title': sheet_name
                            }
                        }
                    })
            
            if requests:
                body = {'requests': requests}
                self.sheet.batchUpdate(
                    spreadsheetId=self.spreadsheet_id,
                    body=body
                ).execute()
                logger.info(f"{len(requests)}個のシートを作成しました")
            
            # ヘッダー行を設定
            self._setup_headers()
            
        except HttpError as e:
            logger.error(f"シート作成エラー: {e}")
            raise
    
    def _setup_headers(self):
        """各シートのヘッダー行を設定"""
        headers = {
            self.MASTER_SHEET: [
                ['N番号', '書籍タイトル', '巻数', '発売日', 'ステータス', '最終更新', '備考']
            ],
            self.SALES_LINKS_SHEET: [
                ['ID', 'N番号', 'サイト名', 'URL', '価格', '取得日時', '有効性', 'エラー']
            ],
            self.LOG_SHEET: [
                ['タイムスタンプ', '処理種別', '対象数', '成功数', '失敗数', '処理時間(秒)', '詳細']
            ]
        }
        
        for sheet_name, header_values in headers.items():
            try:
                # 現在の1行目を確認
                result = self.sheet.values().get(
                    spreadsheetId=self.spreadsheet_id,
                    range=f'{sheet_name}!A1:H1'
                ).execute()
                
                # ヘッダーが存在しない場合のみ設定
                if not result.get('values'):
                    self.sheet.values().update(
                        spreadsheetId=self.spreadsheet_id,
                        range=f'{sheet_name}!A1',
                        valueInputOption='USER_ENTERED',
                        body={'values': header_values}
                    ).execute()
                    logger.info(f"{sheet_name}のヘッダーを設定しました")
                    
            except HttpError as e:
                logger.error(f"ヘッダー設定エラー ({sheet_name}): {e}")


# テスト用関数
def test_connection(credentials_path: str, spreadsheet_id: str) -> bool:
    """接続テスト"""
    try:
        client = GoogleSheetsClient(credentials_path, spreadsheet_id)
        client.create_required_sheets()
        books = client.read_master_books()
        logger.info(f"接続テスト成功: {len(books)}件の書籍データを確認")
        return True
    except Exception as e:
        logger.error(f"接続テスト失敗: {e}")
        return False
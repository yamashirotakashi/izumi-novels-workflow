"""
Google Sheets APIクライアント統合版
複数バージョンの機能を統合し、シンプルで保守性の高い設計を実現

統合機能:
- BookRecord統一データモデル
- 柔軟なシート構造対応 (legacy/updated)
- 簡潔なAPI設計
- 全ての既存機能を後方互換性付きで統合
"""
import os
from typing import List, Dict, Optional, Any, Tuple, Union
from datetime import datetime
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import logging
from dataclasses import dataclass
from enum import Enum

# ロガー設定
logger = logging.getLogger(__name__)


# ==========================================
# 統一データモデル
# ==========================================

class SalesChannel(Enum):
    """販売チャンネルの列定義"""
    KINDLE = ('AA', 'Kindle')
    AMAZON_POD = ('AB', 'Amazon POD')
    BOOKWALKER = ('AC', 'BookWalker')
    KOBO = ('AD', 'Kobo')
    GOOGLE = ('AE', 'Google')
    APPLE = ('AF', 'Apple')
    KINOPPY = ('AG', 'Kinoppy')
    HONTO = ('AH', 'honto')
    READER_STORE = ('AI', 'ReaderStore')
    BOOKLIVE = ('AJ', 'BookLive')
    EBOOKJAPAN = ('AK', 'ebookjapan')
    
    def __init__(self, column: str, display_name: str):
        self.column = column
        self.display_name = display_name
    
    @classmethod
    def get_column_range(cls) -> Tuple[str, str]:
        """販売リンク列の範囲を取得"""
        return ('AA', 'AK')


@dataclass
class BookRecord:
    """統一書籍レコード (BookMaster + BookInfo の統合)"""
    n_code: str
    title: str
    # Legacy BookMaster fields
    volume: int = 0
    release_date: str = ""
    status: str = "未収集"
    last_updated: Optional[str] = None
    notes: Optional[str] = None
    # Updated BookInfo fields
    row_number: int = 0
    sales_links: Dict[str, str] = None
    
    def __post_init__(self):
        if self.sales_links is None:
            self.sales_links = {}


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


@dataclass
class SalesLinkUpdate:
    """販売リンク更新データ"""
    n_code: str
    channel: SalesChannel
    url: str
    scraped_at: Optional[str] = None


# ==========================================
# 統合Google Sheetsクライアント
# ==========================================

class GoogleSheetsClient:
    """統合Google Sheetsクライアント
    
    旧版とupdated版の全機能を統合し、後方互換性を維持
    """
    
    # シート名の定義
    MASTER_SHEET = "マスター"           # Legacy mode
    SALES_LINKS_SHEET = "販売リンク"    # Legacy mode  
    WORK_SHEET = "作業管理"             # Updated mode
    LOG_SHEET = "実行ログ"              # Both modes
    
    # 列定義
    COL_N_CODE = 'D'
    COL_TITLE = 'E'
    
    def __init__(self, credentials_path: str, spreadsheet_id: str, 
                 sheet_mode: str = "auto"):
        """
        Args:
            credentials_path: サービスアカウントJSONファイルのパス
            spreadsheet_id: スプレッドシートID
            sheet_mode: シートモード ("legacy", "updated", "auto")
        """
        self.spreadsheet_id = spreadsheet_id
        self.sheet_mode = sheet_mode
        
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
        
        # シートモードの自動判定
        if sheet_mode == "auto":
            self._detect_sheet_mode()
        
        logger.info(f"Google Sheetsクライアントを初期化: {spreadsheet_id} (mode: {self.sheet_mode})")
    
    def _detect_sheet_mode(self):
        """既存シートに基づいてモードを自動判定"""
        try:
            sheet_metadata = self.sheet.get(
                spreadsheetId=self.spreadsheet_id
            ).execute()
            
            existing_sheets = [
                sheet['properties']['title'] 
                for sheet in sheet_metadata.get('sheets', [])
            ]
            
            if self.WORK_SHEET in existing_sheets:
                self.sheet_mode = "updated"
            elif self.MASTER_SHEET in existing_sheets:
                self.sheet_mode = "legacy"
            else:
                self.sheet_mode = "updated"  # デフォルト
                
            logger.info(f"シートモードを自動判定: {self.sheet_mode}")
            
        except HttpError as e:
            logger.warning(f"シートモード判定エラー、updatedモードを使用: {e}")
            self.sheet_mode = "updated"
    
    # ==========================================
    # 統合API - 書籍データ読み取り
    # ==========================================
    
    def read_books(self) -> List[BookRecord]:
        """書籍データを読み取り (統一インターフェース)"""
        if self.sheet_mode == "legacy":
            return self._read_legacy_books()
        else:
            return self._read_updated_books()
    
    def _read_legacy_books(self) -> List[BookRecord]:
        """Legacyモード: マスターシートから読み取り"""
        try:
            result = self.sheet.values().get(
                spreadsheetId=self.spreadsheet_id,
                range=f'{self.MASTER_SHEET}!A2:G'
            ).execute()
            
            values = result.get('values', [])
            books = []
            
            for i, row in enumerate(values):
                row_data = row + [''] * (7 - len(row))
                
                book = BookRecord(
                    n_code=row_data[0],
                    title=row_data[1],
                    volume=int(row_data[2]) if row_data[2].isdigit() else 0,
                    release_date=row_data[3],
                    status=row_data[4],
                    last_updated=row_data[5] if row_data[5] else None,
                    notes=row_data[6] if row_data[6] else None,
                    row_number=i + 2  # スプレッドシート行番号
                )
                books.append(book)
            
            logger.info(f"{len(books)}件の書籍データを読み取りました (legacy mode)")
            return books
            
        except HttpError as e:
            logger.error(f"Legacy書籍データ読み取りエラー: {e}")
            raise
    
    def _read_updated_books(self) -> List[BookRecord]:
        """Updatedモード: 作業管理シートから読み取り"""
        try:
            # D列(Nコード)、E列(書籍名)、AA-AK列(販売リンク)を取得
            result = self.sheet.values().batchGet(
                spreadsheetId=self.spreadsheet_id,
                ranges=[
                    f'{self.WORK_SHEET}!D:E',   # Nコードと書籍名
                    f'{self.WORK_SHEET}!AA:AK'  # 販売リンク
                ]
            ).execute()
            
            value_ranges = result.get('valueRanges', [])
            if len(value_ranges) < 2:
                logger.warning("データが正しく取得できませんでした")
                return []
            
            basic_info = value_ranges[0].get('values', [])
            link_info = value_ranges[1].get('values', [])
            
            books = []
            for i in range(1, len(basic_info)):  # ヘッダー行をスキップ
                if i >= len(basic_info) or not basic_info[i]:
                    continue
                
                row_data = basic_info[i] + [''] * (2 - len(basic_info[i]))
                n_code = row_data[0].strip()
                title = row_data[1].strip()
                
                if not n_code:
                    continue
                
                # 販売リンクを取得
                sales_links = {}
                if i < len(link_info) and link_info[i]:
                    link_row = link_info[i] + [''] * (11 - len(link_info[i]))
                    for j, channel in enumerate(SalesChannel):
                        url = link_row[j].strip()
                        if url:
                            sales_links[channel.display_name] = url
                
                book = BookRecord(
                    n_code=n_code,
                    title=title,
                    row_number=i + 1,
                    sales_links=sales_links
                )
                books.append(book)
            
            logger.info(f"{len(books)}件の書籍データを読み取りました (updated mode)")
            return books
            
        except HttpError as e:
            logger.error(f"Updated書籍データ読み取りエラー: {e}")
            raise
    
    # ==========================================
    # Legacy API互換メソッド
    # ==========================================
    
    def read_master_books(self) -> List[BookRecord]:
        """Legacy API: マスターシートから書籍データを読み取る"""
        if self.sheet_mode != "legacy":
            logger.warning("Legacy APIが非legacyモードで呼び出されました")
        return self._read_legacy_books()
    
    def get_pending_books(self) -> List[BookRecord]:
        """Legacy API: 未収集ステータスの書籍のみ取得"""
        all_books = self.read_books()
        pending_books = [book for book in all_books if book.status in ['未収集', 'エラー']]
        logger.info(f"{len(pending_books)}件の未収集書籍があります")
        return pending_books
    
    def update_book_status(self, n_code: str, status: str, timestamp: str = None) -> bool:
        """Legacy API: 書籍のステータスを更新"""
        try:
            books = self.read_books()
            target_book = next((book for book in books if book.n_code == n_code), None)
            
            if target_book is None:
                logger.warning(f"N番号 {n_code} が見つかりません")
                return False
            
            if timestamp is None:
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            values = [[status, timestamp]]
            result = self.sheet.values().update(
                spreadsheetId=self.spreadsheet_id,
                range=f'{self.MASTER_SHEET}!E{target_book.row_number}:F{target_book.row_number}',
                valueInputOption='USER_ENTERED',
                body={'values': values}
            ).execute()
            
            logger.info(f"書籍ステータスを更新: {n_code} -> {status}")
            return True
            
        except HttpError as e:
            logger.error(f"ステータス更新エラー: {e}")
            return False
    
    # ==========================================
    # Updated API互換メソッド
    # ==========================================
    
    def read_all_books(self) -> List[BookRecord]:
        """Updated API: 全書籍データを読み取る"""
        return self._read_updated_books()
    
    def get_books_without_links(self, channels: Optional[List[SalesChannel]] = None) -> List[BookRecord]:
        """Updated API: 指定チャンネルのリンクが未設定の書籍を取得"""
        all_books = self.read_books()
        
        if channels is None:
            channels = list(SalesChannel)
        
        books_without_links = []
        channel_names = {ch.display_name for ch in channels}
        
        for book in all_books:
            missing_channels = channel_names - set(book.sales_links.keys())
            if missing_channels:
                books_without_links.append(book)
        
        logger.info(f"{len(books_without_links)}件の書籍でリンクが不足しています")
        return books_without_links
    
    def update_sales_link(self, n_code: str, channel: SalesChannel, url: str) -> bool:
        """Updated API: 特定の販売リンクを更新"""
        try:
            books = self.read_books()
            target_book = next((book for book in books if book.n_code == n_code), None)
            
            if target_book is None:
                logger.warning(f"Nコード {n_code} が見つかりません")
                return False
            
            cell_range = f'{self.WORK_SHEET}!{channel.column}{target_book.row_number}'
            result = self.sheet.values().update(
                spreadsheetId=self.spreadsheet_id,
                range=cell_range,
                valueInputOption='USER_ENTERED',
                body={'values': [[url]]}
            ).execute()
            
            logger.info(f"販売リンクを更新: {n_code} - {channel.display_name}")
            return True
            
        except HttpError as e:
            logger.error(f"販売リンク更新エラー: {e}")
            return False
    
    def batch_update_sales_links(self, updates: List[SalesLinkUpdate]) -> int:
        """Updated API: 複数の販売リンクを一括更新"""
        try:
            books = self.read_books()
            book_map = {book.n_code: book for book in books}
            
            data = []
            for update in updates:
                if update.n_code not in book_map:
                    logger.warning(f"Nコード {update.n_code} が見つかりません")
                    continue
                
                book = book_map[update.n_code]
                data.append({
                    'range': f'{self.WORK_SHEET}!{update.channel.column}{book.row_number}',
                    'values': [[update.url]]
                })
            
            if not data:
                logger.warning("更新対象のデータがありません")
                return 0
            
            body = {
                'valueInputOption': 'USER_ENTERED',
                'data': data
            }
            
            result = self.sheet.values().batchUpdate(
                spreadsheetId=self.spreadsheet_id,
                body=body
            ).execute()
            
            updated_cells = result.get('totalUpdatedCells', 0)
            logger.info(f"{len(data)}件の販売リンクを更新しました（{updated_cells}セル更新）")
            return len(data)
            
        except HttpError as e:
            logger.error(f"バッチ更新エラー: {e}")
            return 0
    
    # ==========================================
    # 販売リンク管理 (Legacy形式)
    # ==========================================
    
    def append_sales_links(self, links: List[SalesLinkRecord]) -> bool:
        """Legacy API: 販売リンクをシートに追加"""
        try:
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
        """Legacy API: 特定書籍の既存販売リンクをクリア"""
        try:
            result = self.sheet.values().get(
                spreadsheetId=self.spreadsheet_id,
                range=f'{self.SALES_LINKS_SHEET}!A2:H'
            ).execute()
            
            values = result.get('values', [])
            rows_to_delete = []
            
            for i in range(len(values) - 1, -1, -1):
                if len(values[i]) > 1 and values[i][1] == n_code:
                    rows_to_delete.append(i + 2)
            
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
    
    # ==========================================
    # ログ機能
    # ==========================================
    
    def log_execution(self, process_type: str, target_count: int, success_count: int,
                      failure_count: int, duration_seconds: int, details: str = ""):
        """Legacy API: 実行ログを記録"""
        try:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            values = [[timestamp, process_type, target_count, success_count, 
                      failure_count, duration_seconds, details]]
            
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
    
    def log_scraping_result(self, n_code: str, site_name: str, success: bool,
                           url: Optional[str] = None, error: Optional[str] = None):
        """Updated API: スクレイピング結果をログシートに記録"""
        try:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            values = [[timestamp, n_code, site_name, 'SUCCESS' if success else 'FAILED',
                      url if url else '', error if error else '']]
            
            result = self.sheet.values().append(
                spreadsheetId=self.spreadsheet_id,
                range=f'{self.LOG_SHEET}!A2',
                valueInputOption='USER_ENTERED',
                insertDataOption='INSERT_ROWS',
                body={'values': values}
            ).execute()
            
            logger.debug(f"スクレイピング結果を記録: {n_code} - {site_name}")
            
        except HttpError as e:
            logger.error(f"ログ記録エラー: {e}")
    
    # ==========================================
    # 統計・ユーティリティ
    # ==========================================
    
    def get_summary_stats(self) -> Dict[str, Any]:
        """Updated API: 収集状況のサマリー統計を取得"""
        try:
            books = self.read_books()
            
            total_books = len(books)
            total_links_expected = total_books * len(SalesChannel)
            total_links_collected = sum(len(book.sales_links) for book in books)
            
            channel_stats = {}
            for channel in SalesChannel:
                collected = sum(
                    1 for book in books 
                    if channel.display_name in book.sales_links
                )
                channel_stats[channel.display_name] = {
                    'collected': collected,
                    'total': total_books,
                    'percentage': (collected / total_books * 100) if total_books > 0 else 0
                }
            
            return {
                'total_books': total_books,
                'total_links_expected': total_links_expected,
                'total_links_collected': total_links_collected,
                'collection_rate': (total_links_collected / total_links_expected * 100) 
                                  if total_links_expected > 0 else 0,
                'channel_stats': channel_stats
            }
            
        except HttpError as e:
            logger.error(f"統計情報取得エラー: {e}")
            return {}
    
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
        """Legacy API: 必要なシートが存在しない場合は作成"""
        try:
            sheet_metadata = self.sheet.get(
                spreadsheetId=self.spreadsheet_id
            ).execute()
            
            existing_sheets = [
                sheet['properties']['title'] 
                for sheet in sheet_metadata.get('sheets', [])
            ]
            
            if self.sheet_mode == "legacy":
                required_sheets = [self.MASTER_SHEET, self.SALES_LINKS_SHEET, self.LOG_SHEET]
                headers = {
                    self.MASTER_SHEET: ['N番号', '書籍タイトル', '巻数', '発売日', 'ステータス', '最終更新', '備考'],
                    self.SALES_LINKS_SHEET: ['ID', 'N番号', 'サイト名', 'URL', '価格', '取得日時', '有効性', 'エラー'],
                    self.LOG_SHEET: ['タイムスタンプ', '処理種別', '対象数', '成功数', '失敗数', '処理時間(秒)', '詳細']
                }
            else:
                required_sheets = [self.WORK_SHEET, self.LOG_SHEET]
                headers = {
                    self.LOG_SHEET: ['タイムスタンプ', 'Nコード', 'サイト名', 'ステータス', 'URL', 'エラー']
                }
            
            requests = []
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
            self._setup_headers(headers)
            
        except HttpError as e:
            logger.error(f"シート作成エラー: {e}")
            raise
    
    def _setup_headers(self, headers: Dict[str, List[str]]):
        """各シートのヘッダー行を設定"""
        for sheet_name, header_values in headers.items():
            try:
                result = self.sheet.values().get(
                    spreadsheetId=self.spreadsheet_id,
                    range=f'{sheet_name}!A1:Z1'
                ).execute()
                
                if not result.get('values'):
                    self.sheet.values().update(
                        spreadsheetId=self.spreadsheet_id,
                        range=f'{sheet_name}!A1',
                        valueInputOption='USER_ENTERED',
                        body={'values': [header_values]}
                    ).execute()
                    logger.info(f"{sheet_name}のヘッダーを設定しました")
                    
            except HttpError as e:
                logger.error(f"ヘッダー設定エラー ({sheet_name}): {e}")


# ==========================================
# 後方互換性のためのエイリアス
# ==========================================

# Legacy API用のエイリアス
BookMaster = BookRecord  # BookMaster -> BookRecord
BookInfo = BookRecord    # BookInfo -> BookRecord

# Updated API用のエイリアス  
UnifiedGoogleSheetsClient = GoogleSheetsClient


# ==========================================
# テスト用関数
# ==========================================

def test_connection(credentials_path: str, spreadsheet_id: str) -> bool:
    """接続テスト"""
    try:
        client = GoogleSheetsClient(credentials_path, spreadsheet_id)
        client.create_required_sheets()
        books = client.read_books()
        
        logger.info(f"接続テスト成功: {len(books)}件の書籍データを確認")
        
        # サマリー統計を表示
        stats = client.get_summary_stats()
        if stats:
            logger.info(f"収集率: {stats.get('collection_rate', 0):.1f}%")
        
        return True
    except Exception as e:
        logger.error(f"接続テスト失敗: {e}")
        return False
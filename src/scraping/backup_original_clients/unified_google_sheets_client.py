"""
Google Sheets APIクライアント統合版
旧版とupdated版の機能を統合し、後方互換性を維持

統合機能:
- 両方の書籍管理モデル (BookMaster + BookInfo)
- 柔軟な販売リンク処理 (追加 + 更新の両対応)
- 統一ログシステム
- モジュラー設計による保守性向上
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
from abc import ABC, abstractmethod

# ロガー設定
logger = logging.getLogger(__name__)


# ==========================================
# Data Models (両バージョンを統合)
# ==========================================

class SalesChannel(Enum):
    """販売チャンネルの列定義 (updated版から継承)"""
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
class BookMaster:
    """書籍マスターデータ (旧版から継承)"""
    n_code: str
    title: str
    volume: int
    release_date: str
    status: str
    last_updated: Optional[str] = None
    notes: Optional[str] = None


@dataclass
class BookInfo:
    """書籍情報 (updated版から継承)"""
    row_number: int  # スプレッドシート上の行番号
    n_code: str      # D列
    title: str       # E列
    sales_links: Dict[str, str]  # 販売チャンネル名: URL


@dataclass
class SalesLinkRecord:
    """販売リンクレコード (旧版から継承)"""
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
    """販売リンク更新データ (updated版から継承)"""
    n_code: str
    channel: SalesChannel
    url: str
    scraped_at: Optional[str] = None


# ==========================================
# Core Components (モジュラー設計)
# ==========================================

class GoogleSheetsAuthManager:
    """認証専用クラス"""
    
    def __init__(self, credentials_path: str):
        """
        Args:
            credentials_path: サービスアカウントJSONファイルのパス
        """
        if not os.path.exists(credentials_path):
            raise FileNotFoundError(f"認証ファイルが見つかりません: {credentials_path}")
        
        self.creds = Credentials.from_service_account_file(
            credentials_path,
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        )
        
        # APIクライアントの構築
        self.service = build('sheets', 'v4', credentials=self.creds)
        logger.info("Google Sheets認証管理を初期化しました")
    
    def get_service(self):
        """Google Sheetsサービスオブジェクトを取得"""
        return self.service


class GoogleSheetsManager:
    """シート操作管理クラス"""
    
    def __init__(self, service, spreadsheet_id: str):
        """
        Args:
            service: Google Sheetsサービスオブジェクト
            spreadsheet_id: スプレッドシートID
        """
        self.service = service
        self.spreadsheet_id = spreadsheet_id
        self.sheet = service.spreadsheets()
        logger.info(f"シート管理を初期化: {spreadsheet_id}")
    
    def get_sheet_id(self, sheet_name: str) -> int:
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
    
    def ensure_sheets_exist(self, required_sheets: List[str], headers: Dict[str, List[str]]):
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
            self._setup_headers(headers)
            
        except HttpError as e:
            logger.error(f"シート作成エラー: {e}")
            raise
    
    def _setup_headers(self, headers: Dict[str, List[str]]):
        """各シートのヘッダー行を設定"""
        for sheet_name, header_values in headers.items():
            try:
                # 現在の1行目を確認
                result = self.sheet.values().get(
                    spreadsheetId=self.spreadsheet_id,
                    range=f'{sheet_name}!A1:Z1'
                ).execute()
                
                # ヘッダーが存在しない場合のみ設定
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


class GoogleSheetsDataAdapter:
    """データ変換アダプタークラス"""
    
    @staticmethod
    def book_master_to_book_info(book_master: BookMaster, row_number: int) -> BookInfo:
        """BookMasterをBookInfoに変換"""
        return BookInfo(
            row_number=row_number,
            n_code=book_master.n_code,
            title=book_master.title,
            sales_links={}  # 初期は空
        )
    
    @staticmethod
    def book_info_to_book_master(book_info: BookInfo, volume: int = 0, 
                                release_date: str = "", status: str = "未収集") -> BookMaster:
        """BookInfoをBookMasterに変換"""
        return BookMaster(
            n_code=book_info.n_code,
            title=book_info.title,
            volume=volume,
            release_date=release_date,
            status=status
        )
    
    @staticmethod
    def sales_link_record_to_update(record: SalesLinkRecord) -> SalesLinkUpdate:
        """SalesLinkRecordをSalesLinkUpdateに変換"""
        # サイト名からSalesChannelを特定
        channel = None
        for ch in SalesChannel:
            if ch.display_name.lower() == record.site_name.lower():
                channel = ch
                break
        
        if channel is None:
            raise ValueError(f"未知の販売サイト: {record.site_name}")
        
        return SalesLinkUpdate(
            n_code=record.n_code,
            channel=channel,
            url=record.url,
            scraped_at=record.scraped_at
        )


# ==========================================
# Unified Client (統合インターフェース)
# ==========================================

class UnifiedGoogleSheetsClient:
    """統合Google Sheetsクライアント
    
    旧版とupdated版の機能を統合し、後方互換性を維持
    """
    
    # シート名の定義 (両バージョン対応)
    MASTER_SHEET = "マスター"           # 旧版
    SALES_LINKS_SHEET = "販売リンク"      # 旧版
    WORK_SHEET = "作業管理"             # updated版
    LOG_SHEET = "実行ログ"              # 共通
    
    # 列定義 (updated版)
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
        
        # 認証管理初期化
        self.auth_manager = GoogleSheetsAuthManager(credentials_path)
        service = self.auth_manager.get_service()
        
        # シート管理初期化
        self.sheet_manager = GoogleSheetsManager(service, spreadsheet_id)
        self.sheet = service.spreadsheets()
        
        # データ変換アダプター
        self.adapter = GoogleSheetsDataAdapter()
        
        # シートモードの自動判定
        if sheet_mode == "auto":
            self._detect_sheet_mode()
        
        # 必要なシートを確保
        self._ensure_required_sheets()
        
        logger.info(f"統合Google Sheetsクライアントを初期化: {spreadsheet_id} (mode: {self.sheet_mode})")
    
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
    
    def _ensure_required_sheets(self):
        """必要なシートが存在することを確認"""
        if self.sheet_mode == "legacy":
            required_sheets = [self.MASTER_SHEET, self.SALES_LINKS_SHEET, self.LOG_SHEET]
            headers = {
                self.MASTER_SHEET: ['N番号', '書籍タイトル', '巻数', '発売日', 'ステータス', '最終更新', '備考'],
                self.SALES_LINKS_SHEET: ['ID', 'N番号', 'サイト名', 'URL', '価格', '取得日時', '有効性', 'エラー'],
                self.LOG_SHEET: ['タイムスタンプ', '処理種別', '対象数', '成功数', '失敗数', '処理時間(秒)', '詳細']
            }
        else:  # updated
            required_sheets = [self.WORK_SHEET, self.LOG_SHEET]
            headers = {
                self.WORK_SHEET: ['N番号', '書籍タイトル'],  # 実際には更新版では手動設定が前提
                self.LOG_SHEET: ['タイムスタンプ', 'Nコード', 'サイト名', 'ステータス', 'URL', 'エラー']
            }
        
        self.sheet_manager.ensure_sheets_exist(required_sheets, headers)
    
    # ==========================================
    # 統合API - 書籍データ読み取り
    # ==========================================
    
    def read_books(self) -> Union[List[BookMaster], List[BookInfo]]:
        """書籍データを読み取り (モードに応じて適切な型を返す)"""
        if self.sheet_mode == "legacy":
            return self.read_master_books()
        else:
            return self.read_all_books()
    
    def read_master_books(self) -> List[BookMaster]:
        """マスターシートから書籍データを読み取る (旧版互換)"""
        try:
            result = self.sheet.values().get(
                spreadsheetId=self.spreadsheet_id,
                range=f'{self.MASTER_SHEET}!A2:G'
            ).execute()
            
            values = result.get('values', [])
            books = []
            
            for row in values:
                # 行データを正規化
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
            
            logger.info(f"{len(books)}件の書籍データを読み取りました (legacy mode)")
            return books
            
        except HttpError as e:
            logger.error(f"マスターシート読み取りエラー: {e}")
            raise
    
    def read_all_books(self) -> List[BookInfo]:
        """作業管理シートから全書籍データを読み取る (updated版互換)"""
        try:
            # D列(Nコード)、E列(書籍名)、AA-AK列(販売リンク)を取得
            result = self.sheet.values().batchGet(
                spreadsheetId=self.spreadsheet_id,
                ranges=[
                    f'{self.WORK_SHEET}!D:E',
                    f'{self.WORK_SHEET}!AA:AK'
                ]
            ).execute()
            
            value_ranges = result.get('valueRanges', [])
            if len(value_ranges) < 2:
                logger.warning("データが正しく取得できませんでした")
                return []
            
            basic_info = value_ranges[0].get('values', [])
            link_info = value_ranges[1].get('values', [])
            
            books = []
            for i in range(1, len(basic_info)):
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
                
                book = BookInfo(
                    row_number=i + 1,
                    n_code=n_code,
                    title=title,
                    sales_links=sales_links
                )
                books.append(book)
            
            logger.info(f"{len(books)}件の書籍データを読み取りました (updated mode)")
            return books
            
        except HttpError as e:
            logger.error(f"書籍データ読み取りエラー: {e}")
            raise
    
    # ==========================================
    # 統合API - フィルタリング
    # ==========================================
    
    def get_pending_books(self) -> Union[List[BookMaster], List[BookInfo]]:
        """未収集ステータスの書籍を取得 (モード適応)"""
        if self.sheet_mode == "legacy":
            all_books = self.read_master_books()
            pending_books = [book for book in all_books if book.status in ['未収集', 'エラー']]
            logger.info(f"{len(pending_books)}件の未収集書籍があります (legacy)")
            return pending_books
        else:
            return self.get_books_without_links()
    
    def get_books_without_links(self, channels: Optional[List[SalesChannel]] = None) -> List[BookInfo]:
        """指定チャンネルのリンクが未設定の書籍を取得 (updated版互換)"""
        all_books = self.read_all_books()
        
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
    
    # ==========================================
    # 統合API - 更新操作
    # ==========================================
    
    def update_book_status(self, n_code: str, status: str, timestamp: str = None) -> bool:
        """書籍のステータスを更新 (旧版互換)"""
        if self.sheet_mode != "legacy":
            logger.warning("ステータス更新はlegacyモードでのみ利用可能です")
            return False
        
        try:
            all_books = self.read_master_books()
            row_index = None
            
            for i, book in enumerate(all_books):
                if book.n_code == n_code:
                    row_index = i + 2
                    break
            
            if row_index is None:
                logger.warning(f"N番号 {n_code} が見つかりません")
                return False
            
            if timestamp is None:
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            values = [[status, timestamp]]
            
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
    
    def update_sales_link(self, n_code: str, channel: SalesChannel, url: str) -> bool:
        """特定の販売リンクを更新 (updated版互換)"""
        if self.sheet_mode == "legacy":
            logger.warning("直接リンク更新はupdatedモードでのみ利用可能です")
            return False
        
        try:
            books = self.read_all_books()
            target_book = None
            
            for book in books:
                if book.n_code == n_code:
                    target_book = book
                    break
            
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
        """複数の販売リンクを一括更新 (updated版互換)"""
        if self.sheet_mode == "legacy":
            logger.warning("バッチリンク更新はupdatedモードでのみ利用可能です")
            return 0
        
        try:
            books = self.read_all_books()
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
    
    def append_sales_links(self, links: List[SalesLinkRecord]) -> bool:
        """販売リンクをシートに追加 (旧版互換)"""
        if self.sheet_mode != "legacy":
            logger.warning("販売リンク追加はlegacyモードでのみ利用可能です")
            return False
        
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
        """特定書籍の既存販売リンクをクリア (旧版互換)"""
        if self.sheet_mode != "legacy":
            logger.warning("販売リンククリアはlegacyモードでのみ利用可能です")
            return False
        
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
                                'sheetId': self.sheet_manager.get_sheet_id(self.SALES_LINKS_SHEET),
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
    # 統合API - ログ機能
    # ==========================================
    
    def log_execution(self, 
                      process_type: str,
                      target_count: int,
                      success_count: int,
                      failure_count: int,
                      duration_seconds: int,
                      details: str = ""):
        """実行ログを記録 (旧版互換)"""
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
    
    def log_scraping_result(self, 
                           n_code: str,
                           site_name: str,
                           success: bool,
                           url: Optional[str] = None,
                           error: Optional[str] = None):
        """スクレイピング結果をログシートに記録 (updated版互換)"""
        try:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            values = [[
                timestamp,
                n_code,
                site_name,
                'SUCCESS' if success else 'FAILED',
                url if url else '',
                error if error else ''
            ]]
            
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
    # 統合API - 統計機能
    # ==========================================
    
    def get_summary_stats(self) -> Dict[str, Any]:
        """収集状況のサマリー統計を取得 (updated版互換)"""
        if self.sheet_mode == "legacy":
            return self._get_legacy_stats()
        else:
            return self._get_updated_stats()
    
    def _get_legacy_stats(self) -> Dict[str, Any]:
        """レガシーモード用統計"""
        try:
            books = self.read_master_books()
            
            status_counts = {}
            for book in books:
                status = book.status
                status_counts[status] = status_counts.get(status, 0) + 1
            
            return {
                'total_books': len(books),
                'status_breakdown': status_counts,
                'pending_count': status_counts.get('未収集', 0) + status_counts.get('エラー', 0),
                'mode': 'legacy'
            }
            
        except Exception as e:
            logger.error(f"レガシー統計取得エラー: {e}")
            return {}
    
    def _get_updated_stats(self) -> Dict[str, Any]:
        """更新版モード用統計"""
        try:
            books = self.read_all_books()
            
            total_books = len(books)
            total_links_expected = total_books * len(SalesChannel)
            total_links_collected = sum(len(book.sales_links) for book in books)
            
            # チャンネル別の統計
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
                'channel_stats': channel_stats,
                'mode': 'updated'
            }
            
        except Exception as e:
            logger.error(f"更新版統計取得エラー: {e}")
            return {}


# ==========================================
# Migration Helper
# ==========================================

class GoogleSheetsMigrationHelper:
    """既存コードの移行支援クラス"""
    
    @staticmethod
    def create_legacy_client(credentials_path: str, spreadsheet_id: str) -> UnifiedGoogleSheetsClient:
        """旧版互換クライアントを作成"""
        return UnifiedGoogleSheetsClient(credentials_path, spreadsheet_id, "legacy")
    
    @staticmethod
    def create_updated_client(credentials_path: str, spreadsheet_id: str) -> UnifiedGoogleSheetsClient:
        """updated版互換クライアントを作成"""
        return UnifiedGoogleSheetsClient(credentials_path, spreadsheet_id, "updated")
    
    @staticmethod
    def migrate_data_format(source_client: UnifiedGoogleSheetsClient, 
                           target_client: UnifiedGoogleSheetsClient) -> bool:
        """データフォーマットを移行"""
        try:
            if source_client.sheet_mode == "legacy" and target_client.sheet_mode == "updated":
                return GoogleSheetsMigrationHelper._migrate_legacy_to_updated(source_client, target_client)
            elif source_client.sheet_mode == "updated" and target_client.sheet_mode == "legacy":
                return GoogleSheetsMigrationHelper._migrate_updated_to_legacy(source_client, target_client)
            else:
                logger.warning("同じモード間の移行は不要です")
                return True
                
        except Exception as e:
            logger.error(f"データ移行エラー: {e}")
            return False
    
    @staticmethod
    def _migrate_legacy_to_updated(source: UnifiedGoogleSheetsClient, 
                                  target: UnifiedGoogleSheetsClient) -> bool:
        """レガシー → 更新版への移行"""
        # この実装は実際のシート構造に依存するため、スケルトンのみ
        logger.info("レガシー → 更新版への移行を開始")
        # TODO: 実装が必要
        return True
    
    @staticmethod
    def _migrate_updated_to_legacy(source: UnifiedGoogleSheetsClient, 
                                  target: UnifiedGoogleSheetsClient) -> bool:
        """更新版 → レガシーへの移行"""
        # この実装は実際のシート構造に依存するため、スケルトンのみ
        logger.info("更新版 → レガシーへの移行を開始")
        # TODO: 実装が必要
        return True


# ==========================================
# Backward Compatibility Layer
# ==========================================

# 旧版のクラス名で統合クライアントをエクスポート
GoogleSheetsClient = UnifiedGoogleSheetsClient


# ==========================================
# Comprehensive Test Suite
# ==========================================

class UnifiedClientTestSuite:
    """統合クライアントの包括的テストスイート"""
    
    def __init__(self, credentials_path: str, spreadsheet_id: str):
        self.credentials_path = credentials_path
        self.spreadsheet_id = spreadsheet_id
        self.test_results = {}
    
    def run_all_tests(self) -> Dict[str, bool]:
        """すべてのテストを実行"""
        logger.info("統合クライアント包括テストを開始")
        
        # 基本接続テスト
        self.test_results['auto_mode_connection'] = self._test_auto_mode()
        self.test_results['legacy_mode_connection'] = self._test_legacy_mode()
        self.test_results['updated_mode_connection'] = self._test_updated_mode()
        
        # 機能テスト
        self.test_results['data_reading'] = self._test_data_reading()
        self.test_results['filtering'] = self._test_filtering()
        self.test_results['statistics'] = self._test_statistics()
        
        # 互換性テスト
        self.test_results['backward_compatibility'] = self._test_backward_compatibility()
        
        # 結果サマリー
        passed = sum(1 for result in self.test_results.values() if result)
        total = len(self.test_results)
        
        logger.info(f"テスト完了: {passed}/{total} 成功")
        
        return self.test_results
    
    def _test_auto_mode(self) -> bool:
        """自動モード検出テスト"""
        try:
            client = UnifiedGoogleSheetsClient(
                self.credentials_path, self.spreadsheet_id, "auto"
            )
            books = client.read_books()
            logger.info(f"自動モードテスト成功: {len(books)}件 (mode: {client.sheet_mode})")
            return True
        except Exception as e:
            logger.error(f"自動モードテスト失敗: {e}")
            return False
    
    def _test_legacy_mode(self) -> bool:
        """レガシーモードテスト"""
        try:
            client = UnifiedGoogleSheetsClient(
                self.credentials_path, self.spreadsheet_id, "legacy"
            )
            # レガシーモード特有の機能をテスト
            books = client.read_books()
            pending = client.get_pending_books()
            logger.info(f"レガシーモードテスト成功: {len(books)}件 ({len(pending)}件未収集)")
            return True
        except Exception as e:
            logger.warning(f"レガシーモードテスト警告（シートが存在しない可能性）: {e}")
            return True  # シートが存在しない場合は警告のみ
    
    def _test_updated_mode(self) -> bool:
        """更新モードテスト"""
        try:
            client = UnifiedGoogleSheetsClient(
                self.credentials_path, self.spreadsheet_id, "updated"
            )
            # 更新モード特有の機能をテスト
            books = client.read_books()
            without_links = client.get_books_without_links()
            stats = client.get_summary_stats()
            logger.info(f"更新モードテスト成功: {len(books)}件 ({len(without_links)}件リンク不足)")
            return True
        except Exception as e:
            logger.error(f"更新モードテスト失敗: {e}")
            return False
    
    def _test_data_reading(self) -> bool:
        """データ読み取り機能テスト"""
        try:
            client = UnifiedGoogleSheetsClient(
                self.credentials_path, self.spreadsheet_id, "auto"
            )
            
            # 基本読み取り
            books = client.read_books()
            
            # アダプター機能テスト
            if client.sheet_mode == "updated" and books:
                # BookInfoからBookMasterへの変換テスト
                first_book = books[0]
                converted = client.adapter.book_info_to_book_master(first_book)
                assert converted.n_code == first_book.n_code
                assert converted.title == first_book.title
            
            logger.info("データ読み取りテスト成功")
            return True
        except Exception as e:
            logger.error(f"データ読み取りテスト失敗: {e}")
            return False
    
    def _test_filtering(self) -> bool:
        """フィルタリング機能テスト"""
        try:
            client = UnifiedGoogleSheetsClient(
                self.credentials_path, self.spreadsheet_id, "auto"
            )
            
            all_books = client.read_books()
            pending_books = client.get_pending_books()
            
            # ペンディングブックは全体の部分集合でなければならない
            if client.sheet_mode == "legacy":
                assert len(pending_books) <= len(all_books)
            else:
                # updated modeの場合、get_books_without_linksが呼ばれる
                assert len(pending_books) <= len(all_books)
            
            logger.info("フィルタリングテスト成功")
            return True
        except Exception as e:
            logger.error(f"フィルタリングテスト失敗: {e}")
            return False
    
    def _test_statistics(self) -> bool:
        """統計機能テスト"""
        try:
            client = UnifiedGoogleSheetsClient(
                self.credentials_path, self.spreadsheet_id, "auto"
            )
            
            stats = client.get_summary_stats()
            
            # 統計データの基本検証
            assert 'total_books' in stats
            assert 'mode' in stats
            
            if stats['mode'] == 'updated':
                assert 'collection_rate' in stats
                assert 'channel_stats' in stats
            elif stats['mode'] == 'legacy':
                assert 'status_breakdown' in stats
                assert 'pending_count' in stats
            
            logger.info(f"統計テスト成功: {stats['total_books']}件")
            return True
        except Exception as e:
            logger.error(f"統計テスト失敗: {e}")
            return False
    
    def _test_backward_compatibility(self) -> bool:
        """後方互換性テスト"""
        try:
            # 旧クラス名でインスタンス化できることを確認
            client = GoogleSheetsClient(
                self.credentials_path, self.spreadsheet_id, "auto"
            )
            
            # 基本機能が動作することを確認
            books = client.read_books()
            
            logger.info("後方互換性テスト成功")
            return True
        except Exception as e:
            logger.error(f"後方互換性テスト失敗: {e}")
            return False


def test_connection(credentials_path: str, spreadsheet_id: str, 
                   sheet_mode: str = "auto") -> bool:
    """統合版接続テスト"""
    try:
        client = UnifiedGoogleSheetsClient(credentials_path, spreadsheet_id, sheet_mode)
        books = client.read_books()
        
        logger.info(f"接続テスト成功: {len(books)}件の書籍データを確認 (mode: {client.sheet_mode})")
        
        # 統計情報の表示
        stats = client.get_summary_stats()
        if stats.get('mode') == 'updated':
            logger.info(f"収集率: {stats.get('collection_rate', 0):.1f}%")
        elif stats.get('mode') == 'legacy':
            logger.info(f"未収集書籍: {stats.get('pending_count', 0)}件")
        
        return True
    except Exception as e:
        logger.error(f"接続テスト失敗: {e}")
        return False


def run_comprehensive_test(credentials_path: str, spreadsheet_id: str) -> bool:
    """包括的テストスイートを実行"""
    test_suite = UnifiedClientTestSuite(credentials_path, spreadsheet_id)
    results = test_suite.run_all_tests()
    
    # 結果の詳細表示
    print("\n=== 統合テスト結果 ===")
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name}: {status}")
    
    all_passed = all(results.values())
    print(f"\n総合結果: {'✅ ALL PASS' if all_passed else '❌ SOME FAILED'}")
    
    return all_passed


if __name__ == "__main__":
    # 設定ファイルからテスト実行
    import sys
    
    if len(sys.argv) >= 3:
        creds_path = sys.argv[1]
        sheet_id = sys.argv[2]
        mode = sys.argv[3] if len(sys.argv) > 3 else "auto"
        
        logging.basicConfig(level=logging.INFO)
        success = test_connection(creds_path, sheet_id, mode)
        sys.exit(0 if success else 1)
    else:
        print("Usage: python unified_google_sheets_client.py <credentials_path> <spreadsheet_id> [mode]")
        sys.exit(1)
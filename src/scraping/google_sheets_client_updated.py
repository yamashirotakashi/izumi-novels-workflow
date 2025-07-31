"""
Google Sheets APIクライアント（更新版）
いずみノベルズスケジュール・刊行時設定情報シートに対応
"""
import os
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import logging
from dataclasses import dataclass
from enum import Enum

# ロガー設定
logger = logging.getLogger(__name__)


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
class BookInfo:
    """書籍情報"""
    row_number: int  # スプレッドシート上の行番号
    n_code: str      # D列
    title: str       # E列
    sales_links: Dict[str, str]  # 販売チャンネル名: URL


@dataclass
class SalesLinkUpdate:
    """販売リンク更新データ"""
    n_code: str
    channel: SalesChannel
    url: str
    scraped_at: Optional[str] = None


class GoogleSheetsClient:
    """Google Sheets APIクライアント（更新版）"""
    
    # シート名の定義
    WORK_SHEET = "作業管理"
    LOG_SHEET = "実行ログ"
    
    # 列定義
    COL_N_CODE = 'D'
    COL_TITLE = 'E'
    
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
    
    def read_all_books(self) -> List[BookInfo]:
        """作業管理シートから全書籍データを読み取る"""
        try:
            # D列(Nコード)、E列(書籍名)、AA-AK列(販売リンク)を取得
            result = self.sheet.values().batchGet(
                spreadsheetId=self.spreadsheet_id,
                ranges=[
                    f'{self.WORK_SHEET}!D:E',  # Nコードと書籍名
                    f'{self.WORK_SHEET}!AA:AK'  # 販売リンク
                ]
            ).execute()
            
            value_ranges = result.get('valueRanges', [])
            if len(value_ranges) < 2:
                logger.warning("データが正しく取得できませんでした")
                return []
            
            # 基本情報とリンク情報を取得
            basic_info = value_ranges[0].get('values', [])
            link_info = value_ranges[1].get('values', [])
            
            books = []
            # ヘッダー行をスキップして処理（行番号は2から開始）
            for i in range(1, len(basic_info)):
                if i >= len(basic_info) or not basic_info[i]:
                    continue
                
                # 基本情報を取得
                row_data = basic_info[i] + [''] * (2 - len(basic_info[i]))
                n_code = row_data[0].strip()
                title = row_data[1].strip()
                
                # 空行はスキップ
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
                    row_number=i + 1,  # スプレッドシートの行番号（1始まり）
                    n_code=n_code,
                    title=title,
                    sales_links=sales_links
                )
                books.append(book)
            
            logger.info(f"{len(books)}件の書籍データを読み取りました")
            return books
            
        except HttpError as e:
            logger.error(f"書籍データ読み取りエラー: {e}")
            raise
    
    def get_books_without_links(self, channels: Optional[List[SalesChannel]] = None) -> List[BookInfo]:
        """指定チャンネルのリンクが未設定の書籍を取得"""
        all_books = self.read_all_books()
        
        if channels is None:
            channels = list(SalesChannel)
        
        books_without_links = []
        channel_names = {ch.display_name for ch in channels}  # Set comprehension for O(1) lookups
        
        for book in all_books:
            # 指定されたチャンネルのいずれかでリンクが欠けている場合
            missing_channels = channel_names - set(book.sales_links.keys())
            
            if missing_channels:
                books_without_links.append(book)
                logger.debug(f"{book.n_code}: {len(missing_channels)}個のチャンネルでリンク未設定")
        
        logger.info(f"{len(books_without_links)}件の書籍でリンクが不足しています")
        return books_without_links
    
    def update_sales_link(self, n_code: str, channel: SalesChannel, url: str) -> bool:
        """特定の販売リンクを更新"""
        try:
            # まず該当書籍を検索
            books = self.read_all_books()
            target_book = None
            
            for book in books:
                if book.n_code == n_code:
                    target_book = book
                    break
            
            if target_book is None:
                logger.warning(f"Nコード {n_code} が見つかりません")
                return False
            
            # セル範囲を計算
            cell_range = f'{self.WORK_SHEET}!{channel.column}{target_book.row_number}'
            
            # 更新実行
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
        """複数の販売リンクを一括更新"""
        try:
            # 書籍情報を取得してマッピング作成
            books = self.read_all_books()
            book_map = {book.n_code: book for book in books}
            
            # バッチ更新データを構築
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
            
            # バッチ更新実行
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
    
    def log_scraping_result(self, 
                           n_code: str,
                           site_name: str,
                           success: bool,
                           url: Optional[str] = None,
                           error: Optional[str] = None):
        """スクレイピング結果をログシートに記録"""
        try:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # ログシートが存在しない場合は作成
            self._ensure_log_sheet()
            
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
    
    def _ensure_log_sheet(self):
        """ログシートが存在することを確認（なければ作成）"""
        try:
            # 既存のシートを確認
            sheet_metadata = self.sheet.get(
                spreadsheetId=self.spreadsheet_id
            ).execute()
            
            existing_sheets = [
                sheet['properties']['title'] 
                for sheet in sheet_metadata.get('sheets', [])
            ]
            
            if self.LOG_SHEET not in existing_sheets:
                # シートを作成
                requests = [{
                    'addSheet': {
                        'properties': {
                            'title': self.LOG_SHEET
                        }
                    }
                }]
                
                body = {'requests': requests}
                self.sheet.batchUpdate(
                    spreadsheetId=self.spreadsheet_id,
                    body=body
                ).execute()
                
                # ヘッダーを設定
                headers = [['タイムスタンプ', 'Nコード', 'サイト名', 'ステータス', 'URL', 'エラー']]
                self.sheet.values().update(
                    spreadsheetId=self.spreadsheet_id,
                    range=f'{self.LOG_SHEET}!A1',
                    valueInputOption='USER_ENTERED',
                    body={'values': headers}
                ).execute()
                
                logger.info(f"{self.LOG_SHEET}シートを作成しました")
                
        except HttpError as e:
            logger.error(f"ログシート確認エラー: {e}")
    
    def get_summary_stats(self) -> Dict[str, Any]:
        """収集状況のサマリー統計を取得"""
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
                'channel_stats': channel_stats
            }
            
        except HttpError as e:
            logger.error(f"統計情報取得エラー: {e}")
            return {}


# テスト用関数
def test_connection(credentials_path: str, spreadsheet_id: str) -> bool:
    """接続テスト"""
    try:
        client = GoogleSheetsClient(credentials_path, spreadsheet_id)
        books = client.read_all_books()
        
        logger.info(f"接続テスト成功: {len(books)}件の書籍データを確認")
        
        # サマリー統計を表示
        stats = client.get_summary_stats()
        logger.info(f"収集率: {stats.get('collection_rate', 0):.1f}%")
        
        return True
    except Exception as e:
        logger.error(f"接続テスト失敗: {e}")
        return False
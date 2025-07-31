"""
スクレイピング結果のエクスポート機能
JSON、CSV、Excel形式での出力をサポート
"""
import json
import csv
import logging
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timezone
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum
import pandas as pd

logger = logging.getLogger(__name__)


class ExportFormat(Enum):
    """エクスポート形式"""
    JSON = "json"
    CSV = "csv"
    EXCEL = "excel"
    XML = "xml"


class ResultStatus(Enum):
    """結果ステータス"""
    SUCCESS = "success"
    NOT_FOUND = "not_found"
    ERROR = "error"
    SKIPPED = "skipped"


@dataclass
class ScrapingResult:
    """スクレイピング結果"""
    n_code: str
    title: str
    site_name: str
    status: ResultStatus
    url: Optional[str] = None
    price: Optional[float] = None
    currency: str = "JPY"
    scraped_at: Optional[datetime] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    processing_time: float = 0.0
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.scraped_at is None:
            self.scraped_at = datetime.now(timezone.utc)
        if self.metadata is None:
            self.metadata = {}


@dataclass
class BatchResult:
    """バッチ処理結果"""
    batch_id: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    total_books: int = 0
    successful_results: int = 0
    failed_results: int = 0
    skipped_results: int = 0
    processing_time: float = 0.0
    results: List[ScrapingResult] = None
    error_summary: Dict[str, int] = None
    
    def __post_init__(self):
        if self.results is None:
            self.results = []
        if self.error_summary is None:
            self.error_summary = {}
    
    @property
    def success_rate(self) -> float:
        """成功率の計算"""
        if self.total_books == 0:
            return 0.0
        return (self.successful_results / self.total_books) * 100
    
    def add_result(self, result: ScrapingResult):
        """結果の追加"""
        self.results.append(result)
        self.total_books = len(self.results)
        
        # 統計の更新
        if result.status == ResultStatus.SUCCESS:
            self.successful_results += 1
        elif result.status == ResultStatus.ERROR:
            self.failed_results += 1
            # エラーサマリーの更新
            error_key = result.error_message or "Unknown Error"
            self.error_summary[error_key] = self.error_summary.get(error_key, 0) + 1
        elif result.status == ResultStatus.SKIPPED:
            self.skipped_results += 1
    
    def finalize(self):
        """バッチ処理の完了"""
        self.completed_at = datetime.now(timezone.utc)
        if self.started_at:
            # タイムゾーンを統一して計算
            if self.started_at.tzinfo is None:
                started_at_utc = self.started_at.replace(tzinfo=timezone.utc)
            else:
                started_at_utc = self.started_at
            self.processing_time = (self.completed_at - started_at_utc).total_seconds()


class ResultExporter:
    """結果エクスポーター"""
    
    def __init__(self, output_dir: Path):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def export_batch_result(self, 
                          batch_result: BatchResult,
                          format: ExportFormat = ExportFormat.JSON,
                          filename: Optional[str] = None) -> Path:
        """バッチ結果のエクスポート"""
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"scraping_results_{batch_result.batch_id}_{timestamp}.{format.value}"
        
        output_path = self.output_dir / filename
        
        if format == ExportFormat.JSON:
            self._export_json(batch_result, output_path)
        elif format == ExportFormat.CSV:
            self._export_csv(batch_result, output_path)
        elif format == ExportFormat.EXCEL:
            self._export_excel(batch_result, output_path)
        elif format == ExportFormat.XML:
            self._export_xml(batch_result, output_path)
        else:
            raise ValueError(f"Unsupported export format: {format}")
        
        logger.info(f"バッチ結果をエクスポート: {output_path}")
        return output_path
    
    def _export_json(self, batch_result: BatchResult, output_path: Path):
        """JSON形式でのエクスポート"""
        # データの準備
        export_data = {
            'batch_info': {
                'batch_id': batch_result.batch_id,
                'started_at': batch_result.started_at.isoformat(),
                'completed_at': batch_result.completed_at.isoformat() if batch_result.completed_at else None,
                'processing_time': batch_result.processing_time,
                'total_books': batch_result.total_books,
                'successful_results': batch_result.successful_results,
                'failed_results': batch_result.failed_results,
                'skipped_results': batch_result.skipped_results,
                'success_rate': batch_result.success_rate,
                'error_summary': batch_result.error_summary
            },
            'results': []
        }
        
        # 個別結果の変換
        for result in batch_result.results:
            result_dict = asdict(result)
            # datetimeをISO形式に変換
            if result_dict['scraped_at']:
                result_dict['scraped_at'] = result.scraped_at.isoformat()
            # EnumをValueに変換
            result_dict['status'] = result.status.value
            export_data['results'].append(result_dict)
        
        # ファイル出力
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
    
    def _export_csv(self, batch_result: BatchResult, output_path: Path):
        """CSV形式でのエクスポート"""
        fieldnames = [
            'n_code', 'title', 'site_name', 'status', 'url', 'price', 'currency',
            'scraped_at', 'error_message', 'retry_count', 'processing_time'
        ]
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for result in batch_result.results:
                row = {
                    'n_code': result.n_code,
                    'title': result.title,
                    'site_name': result.site_name,
                    'status': result.status.value,
                    'url': result.url or '',
                    'price': result.price or '',
                    'currency': result.currency,
                    'scraped_at': result.scraped_at.isoformat() if result.scraped_at else '',
                    'error_message': result.error_message or '',
                    'retry_count': result.retry_count,
                    'processing_time': result.processing_time
                }
                writer.writerow(row)
    
    def _export_excel(self, batch_result: BatchResult, output_path: Path):
        """Excel形式でのエクスポート"""
        try:
            # データフレームの作成
            data = []
            for result in batch_result.results:
                data.append({
                    'Nコード': result.n_code,
                    '書籍タイトル': result.title,
                    'サイト名': result.site_name,
                    'ステータス': result.status.value,
                    'URL': result.url or '',
                    '価格': result.price or '',
                    '通貨': result.currency,
                    '取得日時': result.scraped_at.strftime('%Y-%m-%d %H:%M:%S') if result.scraped_at else '',
                    'エラーメッセージ': result.error_message or '',
                    'リトライ回数': result.retry_count,
                    '処理時間(秒)': result.processing_time
                })
            
            df = pd.DataFrame(data)
            
            # Excelファイルの作成
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                # メインデータ
                df.to_excel(writer, sheet_name='スクレイピング結果', index=False)
                
                # サマリーシート
                summary_data = {
                    '項目': ['バッチID', '開始時刻', '完了時刻', '処理時間(秒)', 
                           '総書籍数', '成功数', '失敗数', 'スキップ数', '成功率(%)'],
                    '値': [
                        batch_result.batch_id,
                        batch_result.started_at.strftime('%Y-%m-%d %H:%M:%S'),
                        batch_result.completed_at.strftime('%Y-%m-%d %H:%M:%S') if batch_result.completed_at else '',
                        batch_result.processing_time,
                        batch_result.total_books,
                        batch_result.successful_results,
                        batch_result.failed_results,
                        batch_result.skipped_results,
                        f"{batch_result.success_rate:.1f}%"
                    ]
                }
                summary_df = pd.DataFrame(summary_data)
                summary_df.to_excel(writer, sheet_name='サマリー', index=False)
                
        except ImportError:
            logger.warning("pandas/openpyxlが利用できません。CSV形式にフォールバック")
            csv_path = output_path.with_suffix('.csv')
            self._export_csv(batch_result, csv_path)
            return csv_path
    
    def _export_xml(self, batch_result: BatchResult, output_path: Path):
        """XML形式でのエクスポート"""
        from xml.etree.ElementTree import Element, SubElement, ElementTree
        
        # ルート要素
        root = Element('scraping_results')
        
        # バッチ情報
        batch_info = SubElement(root, 'batch_info')
        SubElement(batch_info, 'batch_id').text = batch_result.batch_id
        SubElement(batch_info, 'started_at').text = batch_result.started_at.isoformat()
        if batch_result.completed_at:
            SubElement(batch_info, 'completed_at').text = batch_result.completed_at.isoformat()
        SubElement(batch_info, 'processing_time').text = str(batch_result.processing_time)
        SubElement(batch_info, 'total_books').text = str(batch_result.total_books)
        SubElement(batch_info, 'successful_results').text = str(batch_result.successful_results)
        SubElement(batch_info, 'failed_results').text = str(batch_result.failed_results)
        SubElement(batch_info, 'success_rate').text = f"{batch_result.success_rate:.1f}"
        
        # 結果データ
        results_elem = SubElement(root, 'results')
        for result in batch_result.results:
            result_elem = SubElement(results_elem, 'result')
            SubElement(result_elem, 'n_code').text = result.n_code
            SubElement(result_elem, 'title').text = result.title
            SubElement(result_elem, 'site_name').text = result.site_name
            SubElement(result_elem, 'status').text = result.status.value
            if result.url:
                SubElement(result_elem, 'url').text = result.url
            if result.price:
                SubElement(result_elem, 'price').text = str(result.price)
            if result.scraped_at:
                SubElement(result_elem, 'scraped_at').text = result.scraped_at.isoformat()
            if result.error_message:
                SubElement(result_elem, 'error_message').text = result.error_message
        
        # ファイル出力
        tree = ElementTree(root)
        tree.write(output_path, encoding='utf-8', xml_declaration=True)
    
    def export_summary_report(self, 
                            batch_results: List[BatchResult],
                            filename: Optional[str] = None) -> Path:
        """サマリーレポートのエクスポート"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"scraping_summary_{timestamp}.json"
        
        output_path = self.output_dir / filename
        
        # サマリーデータの作成
        summary = {
            'report_generated_at': datetime.now(timezone.utc).isoformat(),
            'total_batches': len(batch_results),
            'overall_statistics': self._calculate_overall_stats(batch_results),
            'batch_summaries': []
        }
        
        for batch in batch_results:
            batch_summary = {
                'batch_id': batch.batch_id,
                'started_at': batch.started_at.isoformat(),
                'completed_at': batch.completed_at.isoformat() if batch.completed_at else None,
                'processing_time': batch.processing_time,
                'total_books': batch.total_books,
                'success_rate': batch.success_rate,
                'error_summary': batch.error_summary
            }
            summary['batch_summaries'].append(batch_summary)
        
        # ファイル出力
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        logger.info(f"サマリーレポートをエクスポート: {output_path}")
        return output_path
    
    def _calculate_overall_stats(self, batch_results: List[BatchResult]) -> Dict[str, Any]:
        """全体統計の計算"""
        if not batch_results:
            return {}
        
        total_books = sum(batch.total_books for batch in batch_results)
        total_successful = sum(batch.successful_results for batch in batch_results)
        total_failed = sum(batch.failed_results for batch in batch_results)
        total_skipped = sum(batch.skipped_results for batch in batch_results)
        
        avg_processing_time = sum(batch.processing_time for batch in batch_results) / len(batch_results)
        overall_success_rate = (total_successful / total_books * 100) if total_books > 0 else 0
        
        # サイト別統計
        site_stats = {}
        for batch in batch_results:
            for result in batch.results:
                site_name = result.site_name
                if site_name not in site_stats:
                    site_stats[site_name] = {'total': 0, 'successful': 0}
                
                site_stats[site_name]['total'] += 1
                if result.status == ResultStatus.SUCCESS:
                    site_stats[site_name]['successful'] += 1
        
        # サイト別成功率の計算
        for site_name, stats in site_stats.items():
            stats['success_rate'] = (stats['successful'] / stats['total'] * 100) if stats['total'] > 0 else 0
        
        return {
            'total_books': total_books,
            'total_successful': total_successful,
            'total_failed': total_failed,
            'total_skipped': total_skipped,
            'overall_success_rate': overall_success_rate,
            'average_processing_time': avg_processing_time,
            'site_statistics': site_stats
        }
    
    def create_result_from_dict(self, data: Dict[str, Any]) -> ScrapingResult:
        """辞書からScrapingResultを作成"""
        return ScrapingResult(
            n_code=data.get('n_code', ''),
            title=data.get('title', ''),
            site_name=data.get('site_name', ''),
            status=ResultStatus(data.get('status', 'error')),
            url=data.get('url'),
            price=data.get('price'),
            currency=data.get('currency', 'JPY'),
            scraped_at=datetime.fromisoformat(data['scraped_at']) if data.get('scraped_at') else None,
            error_message=data.get('error_message'),
            retry_count=data.get('retry_count', 0),
            processing_time=data.get('processing_time', 0.0),
            metadata=data.get('metadata', {})
        )
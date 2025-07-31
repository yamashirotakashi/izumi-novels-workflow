"""
スクレイピング用エラーハンドリング・リトライ機構
"""
import asyncio
import logging
from typing import Any, Callable, Dict, List, Optional, Type, Union
from datetime import datetime, timedelta
from enum import Enum
import random
import json
from pathlib import Path

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """エラー重要度"""
    LOW = "low"          # ログのみ
    MEDIUM = "medium"    # リトライ
    HIGH = "high"        # 即座にエスカレーション
    CRITICAL = "critical" # システム停止


class RetryStrategy(Enum):
    """リトライ戦略"""
    FIXED = "fixed"              # 固定間隔
    EXPONENTIAL = "exponential"  # 指数バックオフ
    LINEAR = "linear"            # 線形増加
    RANDOM = "random"            # ランダム間隔


class ErrorCategory(Enum):
    """エラーカテゴリ"""
    NETWORK = "network"          # ネットワークエラー
    TIMEOUT = "timeout"          # タイムアウト
    CAPTCHA = "captcha"          # CAPTCHA検出
    RATE_LIMIT = "rate_limit"    # レート制限
    PARSING = "parsing"          # パース失敗
    VALIDATION = "validation"    # 検証失敗
    AUTHENTICATION = "auth"      # 認証エラー
    SITE_CHANGE = "site_change"  # サイト構造変更
    UNKNOWN = "unknown"          # 不明なエラー


class ScrapingError(Exception):
    """スクレイピングエラーの基底クラス"""
    
    def __init__(self, 
                 message: str, 
                 category: ErrorCategory = ErrorCategory.UNKNOWN,
                 severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                 recoverable: bool = True,
                 site_name: str = "",
                 context: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.category = category
        self.severity = severity
        self.recoverable = recoverable
        self.site_name = site_name
        self.context = context or {}
        self.timestamp = datetime.now()


class NetworkError(ScrapingError):
    """ネットワークエラー"""
    def __init__(self, message: str, **kwargs):
        super().__init__(message, category=ErrorCategory.NETWORK, **kwargs)


class TimeoutError(ScrapingError):
    """タイムアウトエラー"""
    def __init__(self, message: str, **kwargs):
        super().__init__(message, category=ErrorCategory.TIMEOUT, **kwargs)


class CaptchaError(ScrapingError):
    """CAPTCHAエラー"""
    def __init__(self, message: str, **kwargs):
        super().__init__(message, category=ErrorCategory.CAPTCHA, 
                        severity=ErrorSeverity.HIGH, **kwargs)


class RateLimitError(ScrapingError):
    """レート制限エラー"""
    def __init__(self, message: str, **kwargs):
        super().__init__(message, category=ErrorCategory.RATE_LIMIT, **kwargs)


class ParsingError(ScrapingError):
    """パースエラー"""
    def __init__(self, message: str, **kwargs):
        super().__init__(message, category=ErrorCategory.PARSING, **kwargs)


class SiteChangeError(ScrapingError):
    """サイト構造変更エラー"""
    def __init__(self, message: str, **kwargs):
        super().__init__(message, category=ErrorCategory.SITE_CHANGE,
                        severity=ErrorSeverity.HIGH, **kwargs)


class RetryConfig:
    """リトライ設定"""
    
    def __init__(self,
                 max_attempts: int = 3,
                 strategy: RetryStrategy = RetryStrategy.EXPONENTIAL,
                 base_delay: float = 1.0,
                 max_delay: float = 60.0,
                 backoff_factor: float = 2.0,
                 jitter: bool = True,
                 retry_on: Optional[List[Type[Exception]]] = None):
        self.max_attempts = max_attempts
        self.strategy = strategy
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        self.jitter = jitter
        self.retry_on = retry_on or [ScrapingError]
    
    def calculate_delay(self, attempt: int) -> float:
        """遅延時間の計算"""
        if self.strategy == RetryStrategy.FIXED:
            delay = self.base_delay
        elif self.strategy == RetryStrategy.EXPONENTIAL:
            delay = self.base_delay * (self.backoff_factor ** attempt)
        elif self.strategy == RetryStrategy.LINEAR:
            delay = self.base_delay * (attempt + 1)
        elif self.strategy == RetryStrategy.RANDOM:
            delay = random.uniform(self.base_delay, self.max_delay)
        else:
            delay = self.base_delay
        
        # 最大遅延時間の制限
        delay = min(delay, self.max_delay)
        
        # ジッターの追加
        if self.jitter and self.strategy != RetryStrategy.RANDOM:
            jitter_range = delay * 0.1
            delay += random.uniform(-jitter_range, jitter_range)
        
        return max(0, delay)


class ErrorTracker:
    """エラー追跡・統計"""
    
    def __init__(self):
        self.errors: List[ScrapingError] = []
        self.error_counts: Dict[str, int] = {}
        self.site_error_counts: Dict[str, Dict[str, int]] = {}
        self.last_errors: Dict[str, datetime] = {}
    
    def record_error(self, error: ScrapingError):
        """エラーの記録"""
        self.errors.append(error)
        
        # カテゴリ別カウント
        category = error.category.value
        self.error_counts[category] = self.error_counts.get(category, 0) + 1
        
        # サイト別カウント
        if error.site_name:
            if error.site_name not in self.site_error_counts:
                self.site_error_counts[error.site_name] = {}
            site_counts = self.site_error_counts[error.site_name]
            site_counts[category] = site_counts.get(category, 0) + 1
        
        # 最終エラー時刻の更新
        self.last_errors[category] = error.timestamp
        
        logger.error(f"エラー記録: {error.site_name} - {category} - {error.message}")
    
    def get_error_rate(self, category: str, site_name: str = None, 
                      time_window: timedelta = timedelta(hours=1)) -> float:
        """エラー率の計算"""
        cutoff_time = datetime.now() - time_window
        
        filtered_errors = [
            e for e in self.errors 
            if e.timestamp >= cutoff_time and e.category.value == category
        ]
        
        if site_name:
            filtered_errors = [e for e in filtered_errors if e.site_name == site_name]
        
        # 簡単な実装：エラー数を返す（実際の処理数データが必要）
        return len(filtered_errors)
    
    def is_site_healthy(self, site_name: str, 
                       error_threshold: int = 5,
                       time_window: timedelta = timedelta(minutes=30)) -> bool:
        """サイトの健全性チェック"""
        cutoff_time = datetime.now() - time_window
        
        recent_errors = [
            e for e in self.errors 
            if e.timestamp >= cutoff_time and e.site_name == site_name
        ]
        
        return len(recent_errors) < error_threshold
    
    def get_stats(self) -> Dict[str, Any]:
        """統計情報の取得"""
        return {
            'total_errors': len(self.errors),
            'error_counts_by_category': self.error_counts,
            'error_counts_by_site': self.site_error_counts,
            'recent_errors': len([
                e for e in self.errors 
                if e.timestamp >= datetime.now() - timedelta(hours=1)
            ])
        }


class ErrorHandler:
    """エラーハンドラー"""
    
    def __init__(self, 
                 default_retry_config: Optional[RetryConfig] = None,
                 error_log_path: Optional[Path] = None):
        self.retry_configs: Dict[Type[Exception], RetryConfig] = {}
        self.default_retry_config = default_retry_config or RetryConfig()
        self.error_tracker = ErrorTracker()
        self.error_log_path = error_log_path
        
        # カテゴリ別のデフォルト設定
        self._setup_default_configs()
    
    def _setup_default_configs(self):
        """デフォルト設定のセットアップ"""
        # CAPTCHA: 長時間待機
        self.retry_configs[CaptchaError] = RetryConfig(
            max_attempts=2,
            strategy=RetryStrategy.FIXED,
            base_delay=60.0,
            max_delay=120.0
        )
        
        # レート制限: 指数バックオフ
        self.retry_configs[RateLimitError] = RetryConfig(
            max_attempts=4,
            strategy=RetryStrategy.EXPONENTIAL,
            base_delay=5.0,
            max_delay=300.0,
            backoff_factor=3.0
        )
        
        # タイムアウト: 線形増加
        self.retry_configs[TimeoutError] = RetryConfig(
            max_attempts=3,
            strategy=RetryStrategy.LINEAR,
            base_delay=10.0,
            max_delay=60.0
        )
        
        # ネットワークエラー: 指数バックオフ
        self.retry_configs[NetworkError] = RetryConfig(
            max_attempts=3,
            strategy=RetryStrategy.EXPONENTIAL,
            base_delay=2.0,
            max_delay=30.0
        )
    
    def register_retry_config(self, error_type: Type[Exception], config: RetryConfig):
        """カスタムリトライ設定の登録"""
        self.retry_configs[error_type] = config
    
    async def execute_with_retry(self, 
                               func: Callable,
                               *args,
                               retry_config: Optional[RetryConfig] = None,
                               context: Optional[Dict[str, Any]] = None,
                               **kwargs) -> Any:
        """リトライ付きで関数を実行"""
        config = retry_config or self.default_retry_config
        last_exception = None
        
        for attempt in range(config.max_attempts):
            try:
                result = await func(*args, **kwargs)
                
                # 成功時のログ
                if attempt > 0:
                    logger.info(f"リトライ成功: {func.__name__} (試行 {attempt + 1}/{config.max_attempts})")
                
                return result
                
            except Exception as e:
                last_exception = e
                
                # ScrapingErrorでない場合は変換
                if not isinstance(e, ScrapingError):
                    scraping_error = ScrapingError(
                        str(e),
                        category=self._categorize_error(e),
                        context=context
                    )
                else:
                    scraping_error = e
                
                # エラーの記録
                self.error_tracker.record_error(scraping_error)
                
                # リトライ可能かチェック
                if not self._should_retry(e, config):
                    logger.error(f"リトライ不可能なエラー: {e}")
                    raise e
                
                # 最終試行の場合
                if attempt == config.max_attempts - 1:
                    logger.error(f"リトライ回数上限に達しました: {func.__name__}")
                    break
                
                # 遅延計算と待機
                delay = config.calculate_delay(attempt)
                logger.warning(f"リトライ待機: {func.__name__} (試行 {attempt + 1}/{config.max_attempts}, {delay:.1f}秒後)")
                
                await asyncio.sleep(delay)
        
        # すべてのリトライが失敗
        raise last_exception
    
    def _should_retry(self, error: Exception, config: RetryConfig) -> bool:
        """リトライすべきかの判定"""
        # リトライ対象外のエラータイプ
        if not any(isinstance(error, retry_type) for retry_type in config.retry_on):
            return False
        
        # ScrapingErrorの場合、回復可能性をチェック
        if isinstance(error, ScrapingError):
            if not error.recoverable:
                return False
            
            # 重要度がCRITICALの場合はリトライしない
            if error.severity == ErrorSeverity.CRITICAL:
                return False
        
        return True
    
    def _categorize_error(self, error: Exception) -> ErrorCategory:
        """エラーのカテゴリ分類"""
        error_str = str(error).lower()
        
        if 'timeout' in error_str or 'timed out' in error_str:
            return ErrorCategory.TIMEOUT
        elif 'network' in error_str or 'connection' in error_str:
            return ErrorCategory.NETWORK
        elif 'captcha' in error_str:
            return ErrorCategory.CAPTCHA
        elif 'rate limit' in error_str or 'too many requests' in error_str:
            return ErrorCategory.RATE_LIMIT
        elif 'parse' in error_str or 'parsing' in error_str:
            return ErrorCategory.PARSING
        elif 'auth' in error_str or 'unauthorized' in error_str:
            return ErrorCategory.AUTHENTICATION
        else:
            return ErrorCategory.UNKNOWN
    
    async def log_error_to_file(self, error: ScrapingError):
        """エラーをファイルに記録"""
        if not self.error_log_path:
            return
        
        error_data = {
            'timestamp': error.timestamp.isoformat(),
            'message': error.message,
            'category': error.category.value,
            'severity': error.severity.value,
            'site_name': error.site_name,
            'recoverable': error.recoverable,
            'context': error.context
        }
        
        try:
            with open(self.error_log_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(error_data, ensure_ascii=False) + '\n')
        except Exception as e:
            logger.error(f"エラーログファイル書き込み失敗: {e}")
    
    def get_health_report(self) -> Dict[str, Any]:
        """システム健全性レポート"""
        stats = self.error_tracker.get_stats()
        
        # 最近のエラー傾向
        recent_trend = "stable"
        if stats['recent_errors'] > 10:
            recent_trend = "degraded"
        elif stats['recent_errors'] > 20:
            recent_trend = "critical"
        
        return {
            'overall_health': recent_trend,
            'error_statistics': stats,
            'recommendations': self._generate_recommendations()
        }
    
    def _generate_recommendations(self) -> List[str]:
        """改善提案の生成"""
        recommendations = []
        stats = self.error_tracker.get_stats()
        
        # CAPTCHA頻発の場合
        captcha_count = stats['error_counts_by_category'].get('captcha', 0)
        if captcha_count > 5:
            recommendations.append("CAPTCHA検出が頻発しています。User-Agentやリクエスト間隔の調整を検討してください。")
        
        # レート制限頻発の場合
        rate_limit_count = stats['error_counts_by_category'].get('rate_limit', 0)
        if rate_limit_count > 3:
            recommendations.append("レート制限に頻繁にかかっています。リクエスト間隔を長くしてください。")
        
        # タイムアウト頻発の場合
        timeout_count = stats['error_counts_by_category'].get('timeout', 0)
        if timeout_count > 10:
            recommendations.append("タイムアウトが頻発しています。ネットワーク環境やタイムアウト設定を確認してください。")
        
        return recommendations


# グローバルエラーハンドラーのインスタンス
default_error_handler = ErrorHandler()


def with_retry(retry_config: Optional[RetryConfig] = None):
    """リトライデコレータ"""
    def decorator(func: Callable):
        async def wrapper(*args, **kwargs):
            return await default_error_handler.execute_with_retry(
                func, *args, retry_config=retry_config, **kwargs
            )
        return wrapper
    return decorator
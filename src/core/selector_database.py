#!/usr/bin/env python3
"""
セレクタデータベース管理システム
SQLiteベースの設定データベース実装
"""
import sqlite3
import json
import gzip
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
import logging


@dataclass
class SiteInfo:
    """サイト情報データクラス"""
    id: int
    site_key: str
    name: str
    base_url: str
    search_url: str
    status: str
    priority: int
    created_at: datetime
    updated_at: datetime


@dataclass
class SelectorInfo:
    """セレクタ情報データクラス"""
    id: int
    site_id: int
    selector_type: str
    selector_value: str
    priority: int
    is_active: bool
    success_rate: float
    last_tested: Optional[datetime]
    created_at: datetime
    updated_at: datetime

class DatabaseSchemaManager:
    """データベーススキーマ管理クラス"""
    
    SCHEMA_VERSION = "1.0.0"
    
    def __init__(self, db_path: Path, logger: logging.Logger):
        """
        スキーママネージャー初期化
        
        Args:
            db_path: データベースファイルパス
            logger: ロガーインスタンス
        """
        self.db_path = db_path
        self.logger = logger
    
    def _get_connection(self) -> sqlite3.Connection:
        """データベース接続取得"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # 辞書形式でアクセス可能
        return conn
    
    def initialize_database(self) -> None:
        """データベース初期化"""
        with self._get_connection() as conn:
            # テーブル作成
            self.create_tables(conn)
            # 初期データ投入
            self.insert_default_global_settings(conn)
            conn.commit()
    
    def create_tables(self, conn: sqlite3.Connection) -> None:
        """テーブル作成"""
        
        # サイト基本情報テーブル
        conn.execute("""
        CREATE TABLE IF NOT EXISTS sites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            site_key VARCHAR(50) UNIQUE NOT NULL,
            name VARCHAR(100) NOT NULL,
            base_url VARCHAR(500) NOT NULL,
            search_url VARCHAR(500) NOT NULL,
            status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'deprecated')),
            priority INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # セレクタ情報テーブル
        conn.execute("""
        CREATE TABLE IF NOT EXISTS selectors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            site_id INTEGER NOT NULL,
            selector_type VARCHAR(50) NOT NULL 
                CHECK (selector_type IN ('search_input', 'search_results', 'book_title', 'book_link', 'pagination')),
            selector_value TEXT NOT NULL,
            priority INTEGER DEFAULT 0,
            is_active BOOLEAN DEFAULT TRUE,
            success_rate DECIMAL(5,2) DEFAULT 0.00,
            last_tested TIMESTAMP NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (site_id) REFERENCES sites(id) ON DELETE CASCADE
        )
        """)
        
        # サイト設定テーブル
        conn.execute("""
        CREATE TABLE IF NOT EXISTS site_configs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            site_id INTEGER NOT NULL,
            config_key VARCHAR(100) NOT NULL,
            config_value TEXT NOT NULL,
            config_type VARCHAR(20) NOT NULL 
                CHECK (config_type IN ('wait_time', 'search_param', 'chrome_option', 'other')),
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (site_id) REFERENCES sites(id) ON DELETE CASCADE,
            UNIQUE(site_id, config_key)
        )
        """)
        
        # セレクタ変更履歴テーブル
        conn.execute("""
        CREATE TABLE IF NOT EXISTS selector_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            selector_id INTEGER NOT NULL,
            old_value TEXT,
            new_value TEXT NOT NULL,
            change_type VARCHAR(20) NOT NULL 
                CHECK (change_type IN ('created', 'updated', 'deleted', 'priority_changed')),
            change_reason TEXT,
            success_rate_before DECIMAL(5,2),
            success_rate_after DECIMAL(5,2),
            changed_by VARCHAR(100),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (selector_id) REFERENCES selectors(id) ON DELETE CASCADE
        )
        """)
        
        # 有効性チェック結果テーブル
        conn.execute("""
        CREATE TABLE IF NOT EXISTS validation_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            site_id INTEGER NOT NULL,
            selector_id INTEGER,
            test_query VARCHAR(200) NOT NULL,
            test_result VARCHAR(20) NOT NULL 
                CHECK (test_result IN ('success', 'partial', 'failed')),
            elements_found INTEGER DEFAULT 0,
            error_message TEXT,
            response_time_ms INTEGER,
            test_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            test_environment TEXT,
            FOREIGN KEY (site_id) REFERENCES sites(id) ON DELETE CASCADE,
            FOREIGN KEY (selector_id) REFERENCES selectors(id) ON DELETE SET NULL
        )
        """)
        
        # グローバル設定テーブル
        conn.execute("""
        CREATE TABLE IF NOT EXISTS global_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            setting_key VARCHAR(100) UNIQUE NOT NULL,
            setting_value TEXT NOT NULL,
            setting_type VARCHAR(20) NOT NULL 
                CHECK (setting_type IN ('chrome_options', 'timeouts', 'retry', 'other')),
            description TEXT,
            is_editable BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # バックアップ管理テーブル
        conn.execute("""
        CREATE TABLE IF NOT EXISTS database_backups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            backup_name VARCHAR(200) NOT NULL,
            backup_path VARCHAR(500) NOT NULL,
            backup_size INTEGER,
            backup_type VARCHAR(20) DEFAULT 'auto' 
                CHECK (backup_type IN ('manual', 'auto', 'migration')),
            compression_type VARCHAR(20) DEFAULT 'gzip',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            restored_at TIMESTAMP NULL,
            is_valid BOOLEAN DEFAULT TRUE
        )
        """)
        
        # インデックス作成
        self.create_indexes(conn)
    
    def create_indexes(self, conn: sqlite3.Connection) -> None:
        """インデックス作成"""
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_selectors_site_type ON selectors(site_id, selector_type)",
            "CREATE INDEX IF NOT EXISTS idx_selectors_priority ON selectors(site_id, selector_type, priority DESC)",
            "CREATE INDEX IF NOT EXISTS idx_validation_results_site_date ON validation_results(site_id, test_date DESC)",
            "CREATE INDEX IF NOT EXISTS idx_selector_history_date ON selector_history(selector_id, created_at DESC)",
            "CREATE INDEX IF NOT EXISTS idx_sites_status_priority ON sites(status, priority DESC)"
        ]
        
        for index_sql in indexes:
            conn.execute(index_sql)
    
    def insert_default_global_settings(self, conn: sqlite3.Connection) -> None:
        """デフォルトグローバル設定の投入"""
        default_settings = [
            {
                'setting_key': 'chrome_options',
                'setting_value': json.dumps([
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-blink-features=AutomationControlled",
                    "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                ]),
                'setting_type': 'chrome_options',
                'description': 'Chrome WebDriverのデフォルトオプション'
            },
            {
                'setting_key': 'default_timeout',
                'setting_value': '10',
                'setting_type': 'timeouts',
                'description': 'デフォルトタイムアウト（秒）'
            },
            {
                'setting_key': 'retry_attempts',
                'setting_value': '3',
                'setting_type': 'retry',
                'description': 'デフォルト再試行回数'
            },
            {
                'setting_key': 'screenshot_on_error',
                'setting_value': 'true',
                'setting_type': 'other',
                'description': 'エラー時のスクリーンショット取得'
            }
        ]
        
        for setting in default_settings:
            conn.execute("""
            INSERT OR IGNORE INTO global_settings 
            (setting_key, setting_value, setting_type, description)
            VALUES (?, ?, ?, ?)
            """, (setting['setting_key'], setting['setting_value'], 
                  setting['setting_type'], setting['description']))


class SelectorRepository:
    """セレクタリポジトリクラス"""
    
    def __init__(self, db_path: Path, logger: logging.Logger):
        """
        リポジトリ初期化
        
        Args:
            db_path: データベースファイルパス
            logger: ロガーインスタンス
        """
        self.db_path = db_path
        self.logger = logger
    
    def _get_connection(self) -> sqlite3.Connection:
        """データベース接続取得"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # 辞書形式でアクセス可能
        return conn
    
    # ====== サイト管理メソッド ======
    
    def add_site(self, site_data: Dict[str, Any]) -> int:
        """
        サイト追加
        
        Args:
            site_data: サイト情報辞書
            
        Returns:
            int: 作成されたサイトID
        """
        with self._get_connection() as conn:
            cursor = conn.execute("""
            INSERT INTO sites (site_key, name, base_url, search_url, status, priority)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (
                site_data['site_key'],
                site_data['name'],
                site_data['base_url'],
                site_data['search_url'],
                site_data.get('status', 'active'),
                site_data.get('priority', 0)
            ))
            site_id = cursor.lastrowid
            conn.commit()
            
        self.logger.info(f"サイト追加: {site_data['site_key']} (ID: {site_id})")
        return site_id
    
    def update_site(self, site_id: int, site_data: Dict[str, Any]) -> bool:
        """
        サイト更新
        
        Args:
            site_id: サイトID
            site_data: 更新データ
            
        Returns:
            bool: 更新成功フラグ
        """
        with self._get_connection() as conn:
            cursor = conn.execute("""
            UPDATE sites SET 
                name = COALESCE(?, name),
                base_url = COALESCE(?, base_url),
                search_url = COALESCE(?, search_url),
                status = COALESCE(?, status),
                priority = COALESCE(?, priority),
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """, (
                site_data.get('name'),
                site_data.get('base_url'),
                site_data.get('search_url'),
                site_data.get('status'),
                site_data.get('priority'),
                site_id
            ))
            success = cursor.rowcount > 0
            conn.commit()
            
        self.logger.info(f"サイト更新: ID {site_id}, Success: {success}")
        return success
    
    def get_site(self, site_key: str) -> Optional[Dict[str, Any]]:
        """
        サイト情報取得
        
        Args:
            site_key: サイトキー
            
        Returns:
            Optional[Dict]: サイト情報
        """
        with self._get_connection() as conn:
            cursor = conn.execute("""
            SELECT * FROM sites WHERE site_key = ?
            """, (site_key,))
            row = cursor.fetchone()
            
        return dict(row) if row else None
    
    def list_sites(self, status: str = 'active') -> List[Dict[str, Any]]:
        """
        サイト一覧取得
        
        Args:
            status: フィルタリング状態
            
        Returns:
            List[Dict]: サイト一覧
        """
        with self._get_connection() as conn:
            if status == 'all':
                cursor = conn.execute("""
                SELECT * FROM sites ORDER BY priority DESC, name
                """)
            else:
                cursor = conn.execute("""
                SELECT * FROM sites WHERE status = ? ORDER BY priority DESC, name
                """, (status,))
            rows = cursor.fetchall()
            
        return [dict(row) for row in rows]
    
    def delete_site(self, site_id: int) -> bool:
        """
        サイト削除
        
        Args:
            site_id: サイトID
            
        Returns:
            bool: 削除成功フラグ
        """
        with self._get_connection() as conn:
            cursor = conn.execute("DELETE FROM sites WHERE id = ?", (site_id,))
            success = cursor.rowcount > 0
            conn.commit()
            
        self.logger.info(f"サイト削除: ID {site_id}, Success: {success}")
        return success
    
    # ====== セレクタ管理メソッド ======
    
    def add_selector(self, site_id: int, selector_data: Dict[str, Any]) -> int:
        """
        セレクタ追加
        
        Args:
            site_id: サイトID
            selector_data: セレクタ情報
            
        Returns:
            int: 作成されたセレクタID
        """
        with self._get_connection() as conn:
            cursor = conn.execute("""
            INSERT INTO selectors (site_id, selector_type, selector_value, priority, is_active)
            VALUES (?, ?, ?, ?, ?)
            """, (
                site_id,
                selector_data['selector_type'],
                selector_data['selector_value'],
                selector_data.get('priority', 0),
                selector_data.get('is_active', True)
            ))
            selector_id = cursor.lastrowid
            
            # 履歴記録
            conn.execute("""
            INSERT INTO selector_history (selector_id, new_value, change_type, changed_by)
            VALUES (?, ?, 'created', ?)
            """, (
                selector_id,
                selector_data['selector_value'],
                selector_data.get('changed_by', 'system')
            ))
            
            conn.commit()
            
        self.logger.info(f"セレクタ追加: site_id={site_id}, type={selector_data['selector_type']}, ID={selector_id}")
        return selector_id
    
    def update_selector(self, selector_id: int, new_value: str, reason: str = None) -> bool:
        """
        セレクタ更新
        
        Args:
            selector_id: セレクタID
            new_value: 新しい値
            reason: 変更理由
            
        Returns:
            bool: 更新成功フラグ
        """
        with self._get_connection() as conn:
            # 現在の値を取得
            cursor = conn.execute("""
            SELECT selector_value, success_rate FROM selectors WHERE id = ?
            """, (selector_id,))
            current_row = cursor.fetchone()
            
            if not current_row:
                return False
            
            old_value = current_row['selector_value']
            old_success_rate = current_row['success_rate']
            
            # セレクタ更新
            cursor = conn.execute("""
            UPDATE selectors SET 
                selector_value = ?,
                success_rate = 0.00,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """, (new_value, selector_id))
            
            # 履歴記録
            conn.execute("""
            INSERT INTO selector_history 
            (selector_id, old_value, new_value, change_type, change_reason, success_rate_before)
            VALUES (?, ?, ?, 'updated', ?, ?)
            """, (selector_id, old_value, new_value, reason, old_success_rate))
            
            success = cursor.rowcount > 0
            conn.commit()
            
        self.logger.info(f"セレクタ更新: ID {selector_id}, Success: {success}")
        return success
    
    def get_selectors(self, site_id: int, selector_type: str = None) -> List[Dict[str, Any]]:
        """
        セレクタ一覧取得
        
        Args:
            site_id: サイトID
            selector_type: セレクタタイプ（オプション）
            
        Returns:
            List[Dict]: セレクタ一覧
        """
        with self._get_connection() as conn:
            if selector_type:
                cursor = conn.execute("""
                SELECT * FROM selectors 
                WHERE site_id = ? AND selector_type = ? AND is_active = TRUE
                ORDER BY priority DESC, id
                """, (site_id, selector_type))
            else:
                cursor = conn.execute("""
                SELECT * FROM selectors 
                WHERE site_id = ? AND is_active = TRUE
                ORDER BY selector_type, priority DESC, id
                """, (site_id,))
            rows = cursor.fetchall()
            
        return [dict(row) for row in rows]
    
    def delete_selector(self, selector_id: int, reason: str = None) -> bool:
        """
        セレクタ削除（論理削除）
        
        Args:
            selector_id: セレクタID
            reason: 削除理由
            
        Returns:
            bool: 削除成功フラグ
        """
        with self._get_connection() as conn:
            # 現在の値を取得
            cursor = conn.execute("""
            SELECT selector_value FROM selectors WHERE id = ?
            """, (selector_id,))
            current_row = cursor.fetchone()
            
            if not current_row:
                return False
            
            # 論理削除
            cursor = conn.execute("""
            UPDATE selectors SET 
                is_active = FALSE,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """, (selector_id,))
            
            # 履歴記録
            conn.execute("""
            INSERT INTO selector_history 
            (selector_id, old_value, new_value, change_type, change_reason)
            VALUES (?, ?, '', 'deleted', ?)
            """, (selector_id, current_row['selector_value'], reason))
            
            success = cursor.rowcount > 0
            conn.commit()
            
        self.logger.info(f"セレクタ削除: ID {selector_id}, Success: {success}")
        return success


class BackupManager:
    """バックアップ管理クラス"""
    
    def __init__(self, db_path: Path, logger: logging.Logger):
        """
        バックアップマネージャー初期化
        
        Args:
            db_path: データベースファイルパス
            logger: ロガーインスタンス
        """
        self.db_path = db_path
        self.logger = logger
    
    def _get_connection(self) -> sqlite3.Connection:
        """データベース接続取得"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # 辞書形式でアクセス可能
        return conn
    
    def create_backup(self, backup_name: str = None) -> str:
        """
        データベースバックアップ作成
        
        Args:
            backup_name: バックアップ名（省略時は自動生成）
            
        Returns:
            str: バックアップファイルパス
        """
        if not backup_name:
            backup_name = f"selector_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        backup_dir = self.db_path.parent / "backups"
        backup_dir.mkdir(exist_ok=True)
        
        backup_path = backup_dir / f"{backup_name}.db.gz"
        
        # データベースファイルを圧縮してコピー
        with open(self.db_path, 'rb') as f_in:
            with gzip.open(backup_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        # バックアップ情報をデータベースに記録
        with self._get_connection() as conn:
            conn.execute("""
            INSERT INTO database_backups (backup_name, backup_path, backup_size, backup_type)
            VALUES (?, ?, ?, 'manual')
            """, (backup_name, str(backup_path), backup_path.stat().st_size))
            conn.commit()
        
        self.logger.info(f"バックアップ作成: {backup_path}")
        return str(backup_path)
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """
        バックアップ一覧取得
        
        Returns:
            List[Dict]: バックアップ一覧
        """
        with self._get_connection() as conn:
            cursor = conn.execute("""
            SELECT * FROM database_backups 
            WHERE is_valid = TRUE
            ORDER BY created_at DESC
            """)
            rows = cursor.fetchall()
            
        return [dict(row) for row in rows]
    
    def restore_backup(self, backup_id: int) -> bool:
        """
        バックアップから復旧
        
        Args:
            backup_id: バックアップID
            
        Returns:
            bool: 復旧成功フラグ
        """
        with self._get_connection() as conn:
            cursor = conn.execute("""
            SELECT backup_path FROM database_backups 
            WHERE id = ? AND is_valid = TRUE
            """, (backup_id,))
            row = cursor.fetchone()
            
        if not row:
            self.logger.error(f"バックアップが見つかりません: ID {backup_id}")
            return False
        
        backup_path = Path(row['backup_path'])
        if not backup_path.exists():
            self.logger.error(f"バックアップファイルが存在しません: {backup_path}")
            return False
        
        try:
            # 現在のDBをバックアップ
            emergency_backup = self.create_backup("emergency_before_restore")
            
            # バックアップから復元
            with gzip.open(backup_path, 'rb') as f_in:
                with open(self.db_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            # 復旧記録を更新
            with self._get_connection() as conn:
                conn.execute("""
                UPDATE database_backups SET restored_at = CURRENT_TIMESTAMP WHERE id = ?
                """, (backup_id,))
                conn.commit()
            
            self.logger.info(f"バックアップ復旧完了: ID {backup_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"バックアップ復旧エラー: {e}")
            return False


class SelectorDatabase:
    """セレクタデータベース管理クラス（オーケストレーター）"""
    
    SCHEMA_VERSION = "1.0.0"
    
    def __init__(self, db_path: str = "config/selectors.db"):
        """
        データベース初期化
        
        Args:
            db_path: データベースファイルパス
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.logger = self._setup_logger()
        
        # 各コンポーネントを初期化
        self.schema_manager = DatabaseSchemaManager(self.db_path, self.logger)
        self.repository = SelectorRepository(self.db_path, self.logger)
        self.backup_manager = BackupManager(self.db_path, self.logger)
        
        # データベース初期化
        self.schema_manager.initialize_database()
    
    def _setup_logger(self) -> logging.Logger:
        """ロガー設定"""
        logger = logging.getLogger(f"{__name__}.SelectorDatabase")
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger
    
    def _get_connection(self) -> sqlite3.Connection:
        """データベース接続取得（後方互換性のため）"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # 辞書形式でアクセス可能
        return conn
    
    # ====== 後方互換性のためのラッパーメソッド ======
    
    # スキーマ管理関連
    def _initialize_database(self) -> None:
        """データベース初期化（後方互換性）"""
        self.schema_manager.initialize_database()
    
    def _create_tables(self, conn: sqlite3.Connection) -> None:
        """テーブル作成（後方互換性）"""
        self.schema_manager.create_tables(conn)
    
    def _create_indexes(self, conn: sqlite3.Connection) -> None:
        """インデックス作成（後方互換性）"""
        self.schema_manager.create_indexes(conn)
    
    def _insert_default_global_settings(self, conn: sqlite3.Connection) -> None:
        """デフォルトグローバル設定の投入（後方互換性）"""
        self.schema_manager.insert_default_global_settings(conn)
    
    # サイト管理関連
    def add_site(self, site_data: Dict[str, Any]) -> int:
        """サイト追加"""
        return self.repository.add_site(site_data)
    
    def update_site(self, site_id: int, site_data: Dict[str, Any]) -> bool:
        """サイト更新"""
        return self.repository.update_site(site_id, site_data)
    
    def get_site(self, site_key: str) -> Optional[Dict[str, Any]]:
        """サイト情報取得"""
        return self.repository.get_site(site_key)
    
    def list_sites(self, status: str = 'active') -> List[Dict[str, Any]]:
        """サイト一覧取得"""
        return self.repository.list_sites(status)
    
    def delete_site(self, site_id: int) -> bool:
        """サイト削除"""
        return self.repository.delete_site(site_id)
    
    # セレクタ管理関連
    def add_selector(self, site_id: int, selector_data: Dict[str, Any]) -> int:
        """セレクタ追加"""
        return self.repository.add_selector(site_id, selector_data)
    
    def update_selector(self, selector_id: int, new_value: str, reason: str = None) -> bool:
        """セレクタ更新"""
        return self.repository.update_selector(selector_id, new_value, reason)
    
    def get_selectors(self, site_id: int, selector_type: str = None) -> List[Dict[str, Any]]:
        """セレクタ一覧取得"""
        return self.repository.get_selectors(site_id, selector_type)
    
    def delete_selector(self, selector_id: int, reason: str = None) -> bool:
        """セレクタ削除（論理削除）"""
        return self.repository.delete_selector(selector_id, reason)
    
    # バックアップ管理関連
    def create_backup(self, backup_name: str = None) -> str:
        """データベースバックアップ作成"""
        return self.backup_manager.create_backup(backup_name)
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """バックアップ一覧取得"""
        return self.backup_manager.list_backups()
    
    def restore_backup(self, backup_id: int) -> bool:
        """バックアップから復旧"""
        return self.backup_manager.restore_backup(backup_id)


if __name__ == "__main__":
    # テスト実行例
    db = SelectorDatabase("test_selectors.db")
    
    # サイト追加テスト
    site_id = db.add_site({
        'site_key': 'test_site',
        'name': 'テストサイト',
        'base_url': 'https://example.com',
        'search_url': 'https://example.com/search',
        'priority': 1
    })
    
    # セレクタ追加テスト
    selector_id = db.add_selector(site_id, {
        'selector_type': 'search_input',
        'selector_value': 'input[name="query"]',
        'priority': 1
    })
    
    print(f"テストサイト作成: ID {site_id}")
    print(f"テストセレクタ作成: ID {selector_id}")
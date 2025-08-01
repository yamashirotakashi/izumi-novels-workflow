# 設定データベース構築実装案

## 概要

現在のJSONベース設定管理をSQLiteデータベースに移行し、以下の機能を実装します：

1. 複数サイトのセレクタ情報の一括管理
2. 変更履歴の追跡
3. セレクタの有効性チェック
4. 自動バックアップ・復旧機能
5. Web UIでの設定管理

## データベース設計

### テーブル構造

#### 1. sites（サイト基本情報）
```sql
CREATE TABLE sites (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    site_key VARCHAR(50) UNIQUE NOT NULL,           -- kinoppy, reader_store等
    name VARCHAR(100) NOT NULL,                     -- 表示名
    base_url VARCHAR(500) NOT NULL,                 -- ベースURL
    search_url VARCHAR(500) NOT NULL,               -- 検索URL
    status ENUM('active', 'inactive', 'deprecated') DEFAULT 'active',
    priority INTEGER DEFAULT 0,                     -- 優先度（高い順）
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 2. selectors（セレクタ情報）
```sql
CREATE TABLE selectors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    site_id INTEGER NOT NULL,
    selector_type ENUM('search_input', 'search_results', 'book_title', 'book_link', 'pagination') NOT NULL,
    selector_value TEXT NOT NULL,                   -- CSSセレクタ
    priority INTEGER DEFAULT 0,                     -- 優先度（高い順で試行）
    is_active BOOLEAN DEFAULT TRUE,
    success_rate DECIMAL(5,2) DEFAULT 0.00,        -- 成功率（0-100%）
    last_tested TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (site_id) REFERENCES sites(id) ON DELETE CASCADE
);
```

#### 3. site_configs（サイト設定）
```sql
CREATE TABLE site_configs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    site_id INTEGER NOT NULL,
    config_key VARCHAR(100) NOT NULL,               -- wait_times.page_load等
    config_value TEXT NOT NULL,                     -- JSON形式で値を保存
    config_type ENUM('wait_time', 'search_param', 'chrome_option', 'other') NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (site_id) REFERENCES sites(id) ON DELETE CASCADE,
    UNIQUE(site_id, config_key)
);
```

#### 4. selector_history（セレクタ変更履歴）
```sql
CREATE TABLE selector_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    selector_id INTEGER NOT NULL,
    old_value TEXT,
    new_value TEXT NOT NULL,
    change_type ENUM('created', 'updated', 'deleted', 'priority_changed') NOT NULL,
    change_reason TEXT,
    success_rate_before DECIMAL(5,2),
    success_rate_after DECIMAL(5,2),
    changed_by VARCHAR(100),                        -- 変更者（admin, auto_check等）
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (selector_id) REFERENCES selectors(id) ON DELETE CASCADE
);
```

#### 5. validation_results（有効性チェック結果）
```sql
CREATE TABLE validation_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    site_id INTEGER NOT NULL,
    selector_id INTEGER,                            -- NULL=サイト全体のテスト
    test_query VARCHAR(200) NOT NULL,
    test_result ENUM('success', 'partial', 'failed') NOT NULL,
    elements_found INTEGER DEFAULT 0,
    error_message TEXT,
    response_time_ms INTEGER,
    test_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    test_environment TEXT,                          -- テスト環境情報
    FOREIGN KEY (site_id) REFERENCES sites(id) ON DELETE CASCADE,
    FOREIGN KEY (selector_id) REFERENCES selectors(id) ON DELETE SET NULL
);
```

#### 6. global_settings（グローバル設定）
```sql
CREATE TABLE global_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    setting_key VARCHAR(100) UNIQUE NOT NULL,
    setting_value TEXT NOT NULL,                    -- JSON形式
    setting_type ENUM('chrome_options', 'timeouts', 'retry', 'other') NOT NULL,
    description TEXT,
    is_editable BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 7. database_backups（バックアップ管理）
```sql
CREATE TABLE database_backups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    backup_name VARCHAR(200) NOT NULL,
    backup_path VARCHAR(500) NOT NULL,
    backup_size INTEGER,                            -- バイト単位
    backup_type ENUM('manual', 'auto', 'migration') DEFAULT 'auto',
    compression_type VARCHAR(20) DEFAULT 'gzip',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    restored_at TIMESTAMP NULL,
    is_valid BOOLEAN DEFAULT TRUE
);
```

### インデックス設計
```sql
-- パフォーマンス最適化用インデックス
CREATE INDEX idx_selectors_site_type ON selectors(site_id, selector_type);
CREATE INDEX idx_selectors_priority ON selectors(site_id, selector_type, priority DESC);
CREATE INDEX idx_validation_results_site_date ON validation_results(site_id, test_date DESC);
CREATE INDEX idx_selector_history_date ON selector_history(selector_id, created_at DESC);
CREATE INDEX idx_sites_status_priority ON sites(status, priority DESC);
```

## API設計

### 1. データベース管理クラス

```python
class SelectorDatabase:
    """セレクタデータベース管理クラス"""
    
    def __init__(self, db_path: str = "config/selectors.db"):
        self.db_path = db_path
        self.connection = None
        
    # サイト管理
    def add_site(self, site_data: dict) -> int
    def update_site(self, site_id: int, site_data: dict) -> bool
    def get_site(self, site_key: str) -> dict
    def list_sites(self, status: str = 'active') -> List[dict]
    def delete_site(self, site_id: int) -> bool
    
    # セレクタ管理
    def add_selector(self, site_id: int, selector_data: dict) -> int
    def update_selector(self, selector_id: int, new_value: str, reason: str = None) -> bool
    def get_selectors(self, site_id: int, selector_type: str = None) -> List[dict]
    def delete_selector(self, selector_id: int, reason: str = None) -> bool
    
    # 設定管理
    def set_site_config(self, site_id: int, config_key: str, config_value: Any) -> bool
    def get_site_config(self, site_id: int, config_key: str = None) -> dict
    
    # 履歴管理
    def get_selector_history(self, selector_id: int, limit: int = 10) -> List[dict]
    def get_site_changes(self, site_id: int, days: int = 30) -> List[dict]
    
    # 有効性チェック
    def record_validation_result(self, result_data: dict) -> int
    def get_validation_history(self, site_id: int, days: int = 7) -> List[dict]
    def update_success_rates(self) -> None
    
    # バックアップ管理
    def create_backup(self, backup_name: str = None) -> str
    def list_backups(self) -> List[dict]
    def restore_backup(self, backup_id: int) -> bool
```

### 2. 設定管理API

```python
class ConfigManager:
    """設定管理API"""
    
    def __init__(self, db: SelectorDatabase):
        self.db = db
        
    def export_to_json(self, site_key: str = None) -> dict:
        """現在の設定をJSON形式でエクスポート（後方互換性）"""
        
    def import_from_json(self, json_data: dict) -> bool:
        """JSON設定をデータベースにインポート"""
        
    def migrate_from_json(self, json_file_path: str) -> bool:
        """既存のJSONファイルからマイグレーション"""
        
    def get_site_config_for_scraper(self, site_key: str) -> dict:
        """スクレイパー用の設定データを取得（従来形式）"""
        
    def update_selector_performance(self, site_key: str, selector_type: str, 
                                  selector_value: str, success: bool) -> None:
        """セレクタの性能を更新"""
```

### 3. 有効性チェッカー

```python
class SelectorValidator:
    """セレクタ有効性チェッカー"""
    
    def __init__(self, db: SelectorDatabase, scraper_class):
        self.db = db
        self.scraper_class = scraper_class
        
    async def validate_site(self, site_key: str, test_queries: List[str]) -> dict:
        """サイト全体の有効性チェック"""
        
    async def validate_selector(self, selector_id: int, test_query: str) -> dict:
        """特定セレクタの有効性チェック"""
        
    async def auto_validate_all(self, interval_hours: int = 24) -> None:
        """全サイトの自動定期チェック"""
        
    def suggest_selector_improvements(self, site_key: str) -> List[dict]:
        """セレクタ改善提案"""
        
    def detect_broken_selectors(self, failure_threshold: float = 0.3) -> List[dict]:
        """破損セレクタの自動検出"""
```

## Web UI設計

### 1. ダッシュボード機能

```python
# FastAPI + Jinja2テンプレートベース
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates

app = FastAPI(title="Selector Configuration Manager")
templates = Jinja2Templates(directory="templates")

@app.get("/")
async def dashboard(request: Request):
    """メインダッシュボード"""
    # サイト一覧、最近の変更、エラー状況等を表示

@app.get("/sites")
async def site_list(request: Request):
    """サイト管理画面"""

@app.get("/sites/{site_key}/selectors")
async def selector_editor(request: Request, site_key: str):
    """セレクタ編集画面"""
    
@app.get("/validation")
async def validation_dashboard(request: Request):
    """有効性チェック結果画面"""
    
@app.get("/history")
async def change_history(request: Request):
    """変更履歴画面"""
```

### 2. フロントエンド機能

- **リアルタイム有効性チェック**: セレクタ入力時の即座チェック
- **ビジュアルセレクタエディタ**: ブラウザ上でのセレクタ選択支援
- **成功率ダッシュボード**: グラフでの性能可視化
- **変更差分表示**: Git風の変更履歴表示
- **バックアップ管理UI**: ワンクリックバックアップ・復旧

## 運用フロー

### 1. 初期セットアップ

```bash
# データベース初期化
python scripts/init_database.py

# 既存JSON設定のマイグレーション
python scripts/migrate_from_json.py config/site_selectors.json

# Web UI起動
python scripts/start_web_ui.py
```

### 2. 日常運用

```bash
# 自動有効性チェック（cron等で定期実行）
python scripts/daily_validation.py

# バックアップ作成
python scripts/create_backup.py

# 成功率レポート生成
python scripts/generate_performance_report.py
```

### 3. 障害対応

```bash
# 緊急時のバックアップ復旧
python scripts/emergency_restore.py --backup-id 123

# 破損セレクタの自動修復試行
python scripts/auto_fix_selectors.py --site kinoppy

# 設定の健全性チェック
python scripts/health_check.py
```

## 実装ロードマップ

### Phase 1: データベース基盤（2週間）
- [ ] SQLiteデータベース設計・作成
- [ ] 基本CRUD操作の実装
- [ ] JSONからのマイグレーション機能
- [ ] 基本的なバックアップ機能

### Phase 2: 有効性チェック機能（2週間）
- [ ] セレクタ有効性チェッカーの実装
- [ ] 自動テスト機能
- [ ] 成功率追跡機能
- [ ] 性能分析ツール

### Phase 3: Web UI（3週間）
- [ ] FastAPIバックエンド
- [ ] ダッシュボード画面
- [ ] セレクタ編集画面
- [ ] 履歴・分析画面

### Phase 4: 高度な機能（2週間）
- [ ] 自動セレクタ改善提案
- [ ] リアルタイム監視
- [ ] アラート機能
- [ ] API拡張

## セキュリティ考慮事項

1. **データベースアクセス制御**: SQLite暗号化の検討
2. **Web UI認証**: Basic認証またはOAuth実装
3. **バックアップ暗号化**: 機密データの保護
4. **設定変更ログ**: 全変更の監査ログ
5. **入力値検証**: SQLインジェクション対策

## パフォーマンス最適化

1. **インデックス最適化**: 頻繁なクエリへの最適化
2. **キャッシュ機能**: 設定データのメモリキャッシュ
3. **非同期処理**: 有効性チェックの並列化
4. **データ圧縮**: 履歴データの圧縮保存

この設計により、現在のJSONベース設定を大幅に拡張し、保守性・可視性・信頼性を向上させることができます。
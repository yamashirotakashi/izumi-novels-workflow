# WordPress REST API 統合技術仕様書（改訂版）

## 📋 概要

### 背景
管理会社からの情報により、既存サイトが高度にカスタマイズされたACF実装であることが判明。既存システムへの影響を最小限に抑えた安全な統合方式を採用する。

### 基本方針
- **既存ACFフィールドには一切触れない**
- **新規専用フィールドグループで完全分離**
- **段階的実装でリスクを最小化**
- **ロールバック可能な設計**

---

## 🏗️ アーキテクチャ設計

### システム構成図（安全重視版）
```
┌────────────────────┐     ┌─────────────────────┐
│ Scraping System    │────▶│ Staging Database    │
│ (External)         │     │ (検証用)            │
└────────────────────┘     └─────────────────────┘
                                    │
                                    ▼
                           ┌─────────────────────┐
                           │ Validation Layer    │
                           │ (データ検証)        │
                           └─────────────────────┘
                                    │
                                    ▼
┌────────────────────┐     ┌─────────────────────┐
│ WordPress          │◀────│ REST API Client     │
│ (ACF Custom Fields)│     │ (認証・更新)        │
└────────────────────┘     └─────────────────────┘
```

### データフロー設計
1. **収集フェーズ**: スクレイピングシステムが販売リンクを収集
2. **検証フェーズ**: ステージングDBでデータ整合性確認
3. **承認フェーズ**: 人間による最終確認（初期は必須）
4. **更新フェーズ**: REST API経由で安全に更新

---

## 🔐 認証・セキュリティ設計

### JWT認証実装
```php
// wp-config.php に追加
define('JWT_AUTH_SECRET_KEY', 'your-secret-key-here');
define('JWT_AUTH_CORS_ENABLE', true);

// 認証エンドポイント
POST /wp-json/jwt-auth/v1/token
{
    "username": "api_user",
    "password": "secure_password"
}

// レスポンス
{
    "token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "user_email": "api@example.com",
    "user_nicename": "api_user",
    "user_display_name": "API User"
}
```

### アクセス制限
```php
// functions.php に追加
add_filter('rest_pre_dispatch', function($result, $server, $request) {
    $route = $request->get_route();
    
    // いずみノベルズAPIへのアクセス制限
    if (strpos($route, '/wp/v2/books') !== false) {
        $allowed_ips = ['xxx.xxx.xxx.xxx']; // 許可IPリスト
        
        if (!in_array($_SERVER['REMOTE_ADDR'], $allowed_ips)) {
            return new WP_Error('rest_forbidden', 
                'このIPからのアクセスは許可されていません', 
                array('status' => 403)
            );
        }
    }
    
    return $result;
}, 10, 3);
```

---

## 📦 ACFフィールド設計（安全版）

### 専用フィールドグループ定義
```php
// 既存フィールドとの完全分離
if( function_exists('acf_add_local_field_group') ):

acf_add_local_field_group(array(
    'key' => 'group_izumi_auto_links',
    'title' => '【自動更新】いずみノベルズ販売リンク',
    'fields' => array(
        // メタ情報
        array(
            'key' => 'field_izumi_last_updated',
            'label' => '最終更新日時',
            'name' => 'izumi_links_last_updated',
            'type' => 'date_time_picker',
            'instructions' => '自動更新システムによる最終更新日時',
            'readonly' => 1,
        ),
        array(
            'key' => 'field_izumi_update_status',
            'label' => '更新ステータス',
            'name' => 'izumi_links_status',
            'type' => 'select',
            'choices' => array(
                'pending' => '未更新',
                'processing' => '更新中',
                'completed' => '完了',
                'error' => 'エラー'
            ),
            'readonly' => 1,
        ),
        // リンクデータ（JSON形式で保存）
        array(
            'key' => 'field_izumi_links_json',
            'label' => '販売リンクデータ',
            'name' => 'izumi_sales_links_json',
            'type' => 'textarea',
            'instructions' => 'JSON形式の販売リンクデータ（自動更新）',
            'readonly' => 1,
        ),
        // 人間可読形式（表示用）
        array(
            'key' => 'field_izumi_links_display',
            'label' => '販売リンク一覧',
            'name' => 'izumi_links_display',
            'type' => 'wysiwyg',
            'instructions' => '表示用HTML（自動生成）',
            'readonly' => 1,
        ),
    ),
    'location' => array(
        array(
            array(
                'param' => 'post_type',
                'operator' => '==',
                'value' => 'books', // 実際のカスタム投稿タイプ名
            ),
        ),
    ),
    'menu_order' => 100, // 既存フィールドの後に表示
    'position' => 'normal',
    'style' => 'default',
    'label_placement' => 'top',
    'instruction_placement' => 'label',
    'active' => true,
    'description' => '自動更新システム専用フィールド。手動編集禁止。',
));

endif;
```

---

## 🔌 REST APIエンドポイント設計

### カスタムエンドポイント登録
```php
// REST APIエンドポイントの追加
add_action('rest_api_init', function () {
    // 販売リンク更新エンドポイント
    register_rest_route('izumi/v1', '/books/(?P<id>\d+)/sales-links', array(
        'methods' => 'POST',
        'callback' => 'izumi_update_sales_links',
        'permission_callback' => 'izumi_api_permissions_check',
        'args' => array(
            'id' => array(
                'validate_callback' => function($param, $request, $key) {
                    return is_numeric($param);
                }
            ),
        ),
    ));
    
    // 更新ステータス確認エンドポイント
    register_rest_route('izumi/v1', '/books/(?P<id>\d+)/sales-links/status', array(
        'methods' => 'GET',
        'callback' => 'izumi_get_update_status',
        'permission_callback' => 'izumi_api_permissions_check',
    ));
});

// 権限チェック関数
function izumi_api_permissions_check($request) {
    // JWT認証チェック
    $auth = $request->get_header('Authorization');
    if (empty($auth)) {
        return new WP_Error('rest_forbidden', '認証が必要です', array('status' => 401));
    }
    
    // トークン検証
    $token = str_replace('Bearer ', '', $auth);
    $decoded = JWT::decode($token, JWT_AUTH_SECRET_KEY, array('HS256'));
    
    // ユーザー権限確認
    $user = get_user_by('login', $decoded->data->user->user_login);
    if (!$user || !user_can($user, 'edit_posts')) {
        return new WP_Error('rest_forbidden', '権限がありません', array('status' => 403));
    }
    
    return true;
}
```

### 更新処理実装
```php
function izumi_update_sales_links($request) {
    $post_id = $request['id'];
    $links_data = $request->get_json_params();
    
    // バリデーション
    $validation = izumi_validate_links_data($links_data);
    if (is_wp_error($validation)) {
        return $validation;
    }
    
    // トランザクション的な更新
    try {
        // ステータスを更新中に
        update_field('izumi_links_status', 'processing', $post_id);
        
        // リンクデータをJSON形式で保存
        update_field('izumi_sales_links_json', json_encode($links_data['links']), $post_id);
        
        // 表示用HTMLを生成
        $display_html = izumi_generate_links_html($links_data['links']);
        update_field('izumi_links_display', $display_html, $post_id);
        
        // 更新日時を記録
        update_field('izumi_links_last_updated', current_time('Y-m-d H:i:s'), $post_id);
        
        // ステータスを完了に
        update_field('izumi_links_status', 'completed', $post_id);
        
        // ログ記録
        izumi_log_update($post_id, 'success', $links_data);
        
        return array(
            'success' => true,
            'message' => '販売リンクを更新しました',
            'post_id' => $post_id,
            'updated_at' => current_time('c')
        );
        
    } catch (Exception $e) {
        // エラー処理
        update_field('izumi_links_status', 'error', $post_id);
        izumi_log_update($post_id, 'error', $e->getMessage());
        
        return new WP_Error('update_failed', 
            'Update failed: ' . $e->getMessage(), 
            array('status' => 500)
        );
    }
}
```

---

## 🧪 テスト実装

### テスト用スクリプト（Python）
```python
import requests
import json
from datetime import datetime

class WordPressAPIClient:
    def __init__(self, site_url, username, password):
        self.site_url = site_url.rstrip('/')
        self.token = None
        self.authenticate(username, password)
    
    def authenticate(self, username, password):
        """JWT認証"""
        response = requests.post(
            f"{self.site_url}/wp-json/jwt-auth/v1/token",
            json={"username": username, "password": password}
        )
        if response.status_code == 200:
            self.token = response.json()['token']
        else:
            raise Exception(f"Authentication failed: {response.text}")
    
    def update_sales_links(self, post_id, links_data):
        """販売リンク更新"""
        headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'links': links_data,
            'updated_by': 'automated_system',
            'timestamp': datetime.now().isoformat()
        }
        
        response = requests.post(
            f"{self.site_url}/wp-json/izumi/v1/books/{post_id}/sales-links",
            headers=headers,
            json=payload
        )
        
        return response.json()
    
    def test_connection(self):
        """接続テスト"""
        headers = {'Authorization': f'Bearer {self.token}'}
        response = requests.get(
            f"{self.site_url}/wp-json/wp/v2/types",
            headers=headers
        )
        return response.status_code == 200

# テスト実行
def test_wordpress_integration():
    client = WordPressAPIClient(
        'https://staging.example.com',
        'api_user',
        'secure_password'
    )
    
    # テストデータ
    test_links = [
        {
            'site': 'Amazon Kindle',
            'url': 'https://www.amazon.co.jp/dp/B0XXXXXX',
            'price': 1320,
            'available': True
        },
        {
            'site': '楽天Kobo',
            'url': 'https://books.rakuten.co.jp/rk/xxxxx',
            'price': 1320,
            'available': True
        }
    ]
    
    # 更新実行
    result = client.update_sales_links(123, test_links)
    print(json.dumps(result, indent=2, ensure_ascii=False))
```

---

## 🚦 段階的実装計画

### Phase 1: 読み取り専用実装（1週間）
1. REST APIの有効化確認
2. 認証なしでの読み取りテスト
3. 既存データへの影響確認

### Phase 2: 認証実装（1週間）
1. JWT認証プラグイン導入
2. APIユーザー作成
3. 権限設定とテスト

### Phase 3: 書き込みテスト（2週間）
1. テスト環境での更新テスト
2. エラーハンドリング確認
3. ロールバックテスト

### Phase 4: 本番環境実装（1週間）
1. 本番環境設定
2. 初回は手動承認付き更新
3. 段階的な自動化

---

## 📊 監視・ログ設計

### ログ記録
```php
function izumi_log_update($post_id, $status, $data) {
    $log_entry = array(
        'timestamp' => current_time('c'),
        'post_id' => $post_id,
        'status' => $status,
        'data' => $data,
        'user_agent' => $_SERVER['HTTP_USER_AGENT'],
        'ip_address' => $_SERVER['REMOTE_ADDR']
    );
    
    // カスタムテーブルまたはログファイルに記録
    error_log(json_encode($log_entry), 3, 
        WP_CONTENT_DIR . '/izumi-api-logs/' . date('Y-m-d') . '.log');
}
```

### 監視項目
- API呼び出し回数
- エラー発生率
- 更新成功率
- レスポンスタイム

---

## 🔄 ロールバック手順

### 緊急時の復旧手順
1. **API無効化**
   ```php
   // wp-config.php に追加
   define('IZUMI_API_DISABLED', true);
   ```

2. **フィールドデータクリア**
   ```sql
   DELETE FROM wp_postmeta 
   WHERE meta_key LIKE 'izumi_%';
   ```

3. **プラグイン無効化**
   - JWT認証プラグインを無効化
   - カスタムコードをコメントアウト

---

## 📝 実装チェックリスト

### 事前準備
- [ ] テスト環境の構築
- [ ] 管理会社への詳細説明
- [ ] バックアップ計画策定
- [ ] ロールバック手順書作成

### 実装時
- [ ] JWT認証プラグインインストール
- [ ] APIユーザー作成
- [ ] カスタムフィールド追加
- [ ] エンドポイント実装
- [ ] アクセス制限設定

### テスト
- [ ] 認証テスト
- [ ] 読み取りテスト
- [ ] 書き込みテスト
- [ ] エラーハンドリングテスト
- [ ] 負荷テスト

### 本番移行
- [ ] 管理会社承認取得
- [ ] 本番環境設定
- [ ] 初回手動実行
- [ ] 監視体制確立

---

**作成日**: 2025-01-31  
**リスクレベル**: 中（適切な対策により低減可能）  
**推奨**: テスト環境での十分な検証後に実装
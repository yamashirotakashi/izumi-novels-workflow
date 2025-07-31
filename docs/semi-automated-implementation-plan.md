# 半自動化実装計画書 - データ注入＋手動承認方式

## 📋 概要

### 基本コンセプト
「**自動でデータを準備、人間が最終確認して更新**」
- Google Sheetsからデータ取得：✅ 自動
- スクレイピングでリンク収集：✅ 自動
- WordPressへデータ注入：✅ 自動（下書き状態）
- 管理画面で確認：👤 人間
- 更新ボタン押下：👤 人間

### メリット
1. **安全性**: 人間の目で最終確認、誤データの公開を防止
2. **効率性**: データ収集・整形の手間を90%削減
3. **柔軟性**: 必要に応じて手動修正可能
4. **段階的移行**: 将来的な完全自動化への布石

---

## 🏗️ システムアーキテクチャ

### データフロー図
```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│ Google Sheets   │────▶│ Scraping Engine  │────▶│ Staging Area    │
│ (書籍マスター)  │     │ (11サイト巡回)   │     │ (一時保存)      │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                                                          │
                                                          ▼
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│ WordPress       │◀────│ Preview Mode     │◀────│ Data Injection  │
│ (最終確認・承認)│     │ (確認画面)       │     │ (API経由)       │
└─────────────────┘     └──────────────────┘     └─────────────────┘
         │
         ▼
   [更新ボタン]
         │
         ▼
┌─────────────────┐
│ 本番公開        │
└─────────────────┘
```

---

## 💡 実装方式

### 1. カスタムフィールド設計（二層構造）

```php
// ACFフィールドグループ定義
acf_add_local_field_group(array(
    'key' => 'group_izumi_sales_links',
    'title' => 'いずみノベルズ販売リンク管理',
    'fields' => array(
        
        // === ステージングエリア（自動更新） ===
        array(
            'key' => 'field_izumi_staging_tab',
            'label' => '📝 確認待ちデータ',
            'type' => 'tab',
        ),
        array(
            'key' => 'field_izumi_staging_status',
            'label' => 'ステータス',
            'name' => 'izumi_staging_status',
            'type' => 'message',
            'message' => '<span class="staging-status">🔄 新しいデータがあります</span>',
        ),
        array(
            'key' => 'field_izumi_staging_data',
            'label' => '収集データ（自動更新）',
            'name' => 'izumi_staging_links',
            'type' => 'repeater',
            'readonly' => 1,
            'sub_fields' => array(
                array(
                    'key' => 'field_site_name',
                    'label' => 'サイト名',
                    'name' => 'site_name',
                    'type' => 'text',
                ),
                array(
                    'key' => 'field_sales_url',
                    'label' => '販売URL',
                    'name' => 'url',
                    'type' => 'url',
                ),
                array(
                    'key' => 'field_status',
                    'label' => '状態',
                    'name' => 'status',
                    'type' => 'select',
                    'choices' => array(
                        'active' => '✅ 有効',
                        'not_found' => '❌ 未発見',
                        'error' => '⚠️ エラー'
                    ),
                ),
            ),
        ),
        array(
            'key' => 'field_izumi_staging_updated',
            'label' => 'データ取得日時',
            'name' => 'izumi_staging_updated',
            'type' => 'date_time_picker',
            'readonly' => 1,
        ),
        
        // === 本番エリア（手動承認後） ===
        array(
            'key' => 'field_izumi_production_tab',
            'label' => '✅ 公開中データ',
            'type' => 'tab',
        ),
        array(
            'key' => 'field_izumi_production_data',
            'label' => '公開中の販売リンク',
            'name' => 'izumi_production_links',
            'type' => 'repeater',
            'sub_fields' => array(
                // 同じ構造
            ),
        ),
        
        // === アクションボタン ===
        array(
            'key' => 'field_izumi_actions_tab',
            'label' => '🎯 アクション',
            'type' => 'tab',
        ),
        array(
            'key' => 'field_izumi_approve_button',
            'label' => '',
            'name' => 'izumi_approve_action',
            'type' => 'message',
            'message' => '<button type="button" class="button button-primary button-large" id="izumi-approve-btn">
                            ✅ 確認済み - 本番データを更新
                          </button>
                          <button type="button" class="button button-secondary" id="izumi-reject-btn">
                            ❌ 却下 - このデータを破棄
                          </button>',
        ),
    ),
));
```

### 2. 管理画面のUI/UX改善

```javascript
// 管理画面用JavaScript
jQuery(document).ready(function($) {
    // 視覚的な差分表示
    function highlightChanges() {
        const staging = $('.field_izumi_staging_data');
        const production = $('.field_izumi_production_data');
        
        // 新規追加されたリンクをハイライト
        staging.find('.acf-row').each(function() {
            const url = $(this).find('input[name*="url"]').val();
            if (!production.find(`input[value="${url}"]`).length) {
                $(this).addClass('new-link').prepend('<span class="badge new">NEW</span>');
            }
        });
        
        // 変更されたリンクをハイライト
        // ... 差分検出ロジック
    }
    
    // 承認ボタンの処理
    $('#izumi-approve-btn').on('click', function() {
        if (confirm('確認済みデータを本番環境に反映しますか？')) {
            // Ajaxで承認処理
            $.post(ajaxurl, {
                action: 'izumi_approve_links',
                post_id: $('#post_ID').val(),
                nonce: izumi_ajax.nonce
            }, function(response) {
                if (response.success) {
                    alert('✅ 販売リンクを更新しました');
                    location.reload();
                }
            });
        }
    });
});
```

### 3. REST APIエンドポイント（データ注入用）

```php
// データ注入エンドポイント
register_rest_route('izumi/v1', '/books/(?P<id>\d+)/inject-links', array(
    'methods' => 'POST',
    'callback' => 'izumi_inject_staging_links',
    'permission_callback' => 'izumi_api_permissions_check',
));

function izumi_inject_staging_links($request) {
    $post_id = $request['id'];
    $links_data = $request->get_json_params();
    
    try {
        // ステージングエリアにデータを保存（本番には触れない）
        update_field('izumi_staging_links', $links_data['links'], $post_id);
        update_field('izumi_staging_updated', current_time('Y-m-d H:i:s'), $post_id);
        update_field('izumi_staging_status', 'pending_approval', $post_id);
        
        // 管理者に通知（オプション）
        izumi_notify_admin_new_data($post_id);
        
        return array(
            'success' => true,
            'message' => 'データを注入しました。管理画面で確認してください。',
            'preview_url' => get_edit_post_link($post_id, 'raw')
        );
        
    } catch (Exception $e) {
        return new WP_Error('injection_failed', $e->getMessage());
    }
}

// 承認処理
function izumi_approve_staging_links($post_id) {
    // ステージングから本番へデータをコピー
    $staging_data = get_field('izumi_staging_links', $post_id);
    
    if ($staging_data) {
        // 本番データを更新
        update_field('izumi_production_links', $staging_data, $post_id);
        update_field('izumi_production_updated', current_time('Y-m-d H:i:s'), $post_id);
        
        // ステージングをクリア
        update_field('izumi_staging_links', array(), $post_id);
        update_field('izumi_staging_status', 'approved', $post_id);
        
        // ログ記録
        izumi_log_approval($post_id, get_current_user_id(), $staging_data);
        
        return true;
    }
    
    return false;
}
```

---

## 🔄 運用フロー

### 定期実行（月3回）の流れ

1. **自動実行フェーズ**（深夜2:00～3:00）
   ```
   Cron → Google Sheets読込 → 11サイトスクレイピング → データ整形 → API注入
   ```

2. **通知フェーズ**（朝9:00）
   ```
   メール/Slack通知: "3件の書籍で新しい販売リンクデータがあります"
   ```

3. **確認・承認フェーズ**（営業時間中）
   ```
   管理画面ログイン → 書籍ページ編集 → データ確認 → 更新ボタン押下
   ```

### 画面イメージ

```
┌─────────────────────────────────────────────────────┐
│ 書籍名: 異世界転生した件 第3巻                      │
├─────────────────────────────────────────────────────┤
│ 📝 確認待ちデータ | ✅ 公開中データ | 🎯 アクション │
├─────────────────────────────────────────────────────┤
│                                                     │
│ 🔄 新しいデータがあります (2025/02/01 02:30 取得)   │
│                                                     │
│ ┌─────────────┬──────────────────────┬──────────┐│
│ │ サイト名    │ URL                  │ 状態     ││
│ ├─────────────┼──────────────────────┼──────────┤│
│ │Amazon Kindle│ https://amzn.to/...  │ ✅ 有効  ││
│ │楽天Kobo  🆕│ https://books.rak... │ ✅ 有効  ││
│ │BOOK☆WALKER │ https://bookwal...   │ ✅ 有効  ││
│ │honto        │ -                    │ ❌ 未発見││
│ └─────────────┴──────────────────────┴──────────┘│
│                                                     │
│ [✅ 確認済み - 本番データを更新] [❌ 却下]         │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

## 📊 効果測定

### 作業時間の変化
| 工程 | 現在（手動） | 半自動化後 | 削減率 |
|------|-------------|-----------|--------|
| データ収集 | 120分 | 0分（自動） | 100% |
| リンク確認 | 30分 | 5分 | 83% |
| データ入力 | 15分 | 2分（確認のみ） | 87% |
| **合計** | **165分** | **7分** | **96%** |

### 品質向上
- ヒューマンエラー削減: 入力ミス・貼り付けミスがゼロに
- 更新漏れ防止: システムが自動で全サイトを巡回
- 履歴管理: いつ誰が承認したか記録

---

## 🚀 実装ステップ

### Phase 1: 基盤構築（2週間）
1. [ ] ACFフィールド構造の実装
2. [ ] REST APIエンドポイント開発
3. [ ] 管理画面UIのカスタマイズ
4. [ ] 権限管理・セキュリティ設定

### Phase 2: 連携開発（2週間）
1. [ ] Google Sheets連携
2. [ ] スクレイピングエンジン実装
3. [ ] データ注入クライアント開発
4. [ ] エラーハンドリング

### Phase 3: テスト運用（1週間）
1. [ ] テスト環境での動作確認
2. [ ] 本番環境での限定テスト
3. [ ] 運用手順書作成
4. [ ] 管理会社への説明・承認

### Phase 4: 本格運用（継続）
1. [ ] 定期実行スケジュール設定
2. [ ] 監視・アラート設定
3. [ ] 月次レポート作成
4. [ ] 改善要望の収集

---

## 🛡️ セキュリティ・安全対策

### データ保護
- ステージングと本番の完全分離
- 承認前のデータは公開されない
- 全操作のログ記録

### 権限管理
```php
// 承認権限の制御
function izumi_can_approve_links($user_id = null) {
    if (!$user_id) $user_id = get_current_user_id();
    
    // 特定のユーザーのみ承認可能
    $allowed_users = array('admin', 'izumi_admin');
    $user = get_user_by('id', $user_id);
    
    return in_array($user->user_login, $allowed_users);
}
```

### ロールバック
- 承認履歴から過去のデータを復元可能
- 誤承認時の即時差し戻し機能

---

## 💰 コストメリット

### 初期投資
- 開発費: 60-80万円（5-6週間）
- テスト・調整: 10万円

### 運用コスト
- サーバー費: 5,000円/月
- 保守費: 10,000円/月（簡易保守で十分）

### ROI計算
- 月間削減時間: 158分（2.6時間）
- 年間削減時間: 31.6時間
- 投資回収期間: 約8ヶ月

---

## ✅ この方式のメリット

1. **管理会社の懸念を解消**
   - 既存システムへの影響を最小限に
   - 人間の判断を残すことで安心感

2. **段階的な信頼構築**
   - まず半自動で運用実績を積む
   - 信頼が構築されたら完全自動化へ

3. **柔軟な運用**
   - 特殊なケースは手動修正可能
   - 緊急時は従来の手動運用に戻せる

4. **品質保証**
   - 最終確認により品質を担保
   - ミスや異常を事前に発見

---

**提案日**: 2025-01-31  
**推奨度**: ⭐⭐⭐⭐⭐  
**実現可能性**: 高（技術的リスク低）
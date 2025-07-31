# BOOK☆WALKER スクレイピング仕様書

## サイト概要
- **サイト名**: BOOK☆WALKER
- **URL**: https://bookwalker.jp/
- **運営**: 株式会社ブックウォーカー（KADOKAWA グループ）
- **特徴**: KADOKAWA系書籍の電子書籍配信プラットフォーム

## 検索仕様

### 基本検索URL
```
https://bookwalker.jp/search/?word={検索クエリ}&order=new
```

### 検索パラメータ
- `word`: 検索キーワード（URLエンコード必須）
- `order`: 並び順（new=新着順、popular=人気順、release=発売日順）
- `type`: 絞り込み（book=書籍、series=シリーズ）

### 検索戦略
1. **完全一致検索**: 書籍タイトルをそのまま検索
2. **部分一致検索**: 巻数を除いたタイトルで検索
3. **シリーズ検索**: 「シリーズ名 第X巻」形式で検索
4. **作者名併用**: 「タイトル 作者名」で検索

## セレクタ仕様

### 検索結果コンテナ
```css
.c-card-book-list .m-card-book
```

### 書籍情報抽出
```css
/* 書籍タイトル */
.m-card-book__title a

/* 書籍URL */
.m-card-book__title a[href]

/* 著者名 */
.m-card-book__author

/* 価格情報 */
.m-card-book__price

/* 書籍画像 */
.m-card-book__image img[src]

/* 出版社 */
.m-card-book__publisher

/* 発売日 */
.m-card-book__release-date
```

### 書籍詳細ページ
```css
/* 詳細書籍タイトル */
.p-main__title h1

/* 価格（税込） */
.p-price__value

/* シリーズ情報 */
.p-series-info

/* 書籍説明 */
.p-description__text
```

## タイトル正規化ルール

### BOOK☆WALKER固有パターン
1. **巻数表記統一**:
   - `第1巻` → `①`
   - `1巻` → `①`
   - `（上）` → `上`
   - `（下）` → `下`

2. **シリーズ名処理**:
   - KADOKAWA系ライトノベルの特殊な表記に対応
   - `～～～　第○巻　サブタイトル` 形式の処理

3. **特殊文字処理**:
   - `☆` → `*` （検索時のみ）
   - 全角英数字 → 半角英数字

### マッチング精度向上
```python
def normalize_bookwalker_title(title: str) -> List[str]:
    """BOOK☆WALKER用タイトル正規化"""
    variants = []
    
    # 基本正規化
    base_title = normalize_base_title(title)
    variants.append(base_title)
    
    # ☆文字のバリエーション
    if '☆' in title:
        variants.append(title.replace('☆', '*'))
        variants.append(title.replace('☆', ''))
    
    # 巻数表記のバリエーション
    volume_patterns = [
        (r'([①-⑳])', r'第\1巻'),
        (r'([①-⑳])', r'\1巻'),
        (r'第(\d+)巻', r'①巻')  # 数字を丸数字に変換
    ]
    
    for pattern, replacement in volume_patterns:
        for variant in variants[:]:
            new_variant = re.sub(pattern, replacement, variant)
            if new_variant not in variants:
                variants.append(new_variant)
    
    return variants
```

## アクセス制限・レート制限

### レート制限仕様
- **リクエスト間隔**: 2-3秒推奨
- **同時接続数**: 1接続のみ
- **User-Agent**: 必須（モバイル版推奨）
- **Cookie**: セッション管理あり

### アンチボット対策
- JavaScript必須ページあり
- Playwright推奨（requests不可）
- 画像認証の可能性（稀）

## エラーハンドリング

### 想定エラーパターン
1. **404エラー**: 書籍が存在しない
2. **503エラー**: サーバー過負荷
3. **検索結果0件**: タイトル不一致
4. **JavaScript待機タイムアウト**: 動的コンテンツ読み込み失敗
5. **Cookie認証エラー**: セッション切れ

### エラー対応戦略
```python
# 段階的検索戦略
search_strategies = [
    "完全一致検索",
    "部分一致検索", 
    "巻数除外検索",
    "作者名併用検索"
]

# リトライ条件
retry_conditions = [
    "503エラー: 30秒後リトライ",
    "タイムアウト: セレクタ変更して再試行",
    "JavaScript エラー: ページリロード"
]
```

## 動的コンテンツ対応

### JavaScript待機
```python
# 検索結果読み込み待機
await page.wait_for_selector('.c-card-book-list', timeout=10000)

# 価格情報読み込み待機（Ajax）
await page.wait_for_function(
    "document.querySelectorAll('.m-card-book__price').length > 0"
)
```

### 無限スクロール対応
```python
# 検索結果の追加読み込み
while True:
    await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
    await page.wait_for_timeout(2000)
    
    new_results = await page.query_selector_all('.m-card-book')
    if len(new_results) == previous_count:
        break  # これ以上読み込みなし
    previous_count = len(new_results)
```

## テストケース

### 基本テストデータ
```json
{
  "test_books": [
    {
      "n_code": "N0230FK",
      "title": "パラレイドデイズ④",
      "expected_url_pattern": "https://bookwalker.jp/de",
      "search_variants": [
        "パラレイドデイズ④",
        "パラレイドデイズ　第4巻",
        "パラレイドデイズ 4巻"
      ]
    },
    {
      "n_code": "N7975EJ", 
      "title": "エアボーンウイッチ④",
      "expected_url_pattern": "https://bookwalker.jp/de"
    }
  ]
}
```

### エッジケーステスト
- 長いタイトル（50文字以上）
- 特殊文字を含むタイトル（♪、★、etc）
- 英数字混在タイトル
- シリーズものの最新巻

## パフォーマンス目標
- **検索レスポンス**: 5秒以内
- **成功率**: 85%以上
- **エラー率**: 15%以下
- **メモリ使用量**: 100MB以下

## 実装優先度
1. **High**: 基本検索・結果抽出
2. **Medium**: タイトル正規化・エラーハンドリング
3. **Low**: 詳細情報取得・価格比較

---

**作成日**: 2025-07-31  
**作成者**: Phase 2 実装チーム  
**レビュー状況**: 実装前レビュー待ち
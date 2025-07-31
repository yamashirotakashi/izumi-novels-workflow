# Amazon Kindle スクレイピング仕様書

## 概要
Amazon KindleストアからいずみノベルズタイトルのURLを取得する仕様。

## 基本情報
- **サイト名**: Amazon Kindle
- **ベースURL**: https://www.amazon.co.jp
- **検索方式**: タイトル検索
- **安定性**: 高（サイト構造が比較的安定）
- **レート制限**: あり（過度なアクセスは制限される）

## 検索戦略

### 1. 検索URL構成
```
https://www.amazon.co.jp/s?k={タイトル}+いずみノベルズ&i=digital-text
```

### 2. 検索パラメータ
- `k`: 検索キーワード（タイトル + "いずみノベルズ"）
- `i`: カテゴリ（digital-text = Kindleストア）

### 3. 代替検索パターン
1. **完全一致検索**: `"{タイトル}" いずみノベルズ`
2. **著者名検索**: タイトルで見つからない場合
3. **ASIN検索**: 既知のASINがある場合

## セレクタ仕様

### 検索結果ページ
```javascript
// 検索結果コンテナ
const resultsContainer = 'div[data-component-type="s-search-result"]';

// 商品リンク
const productLink = 'h2.s-size-mini.s-spacing-none.s-color-base a';

// タイトル
const title = 'h2.s-size-mini.s-spacing-none.s-color-base span';

// 著者名
const author = 'span.a-size-base';

// 価格
const price = 'span.a-price-whole';
```

### 商品詳細ページ（検証用）
```javascript
// ASINの取得
const asin = document.querySelector('input[name="ASIN"]')?.value;

// タイトル確認
const detailTitle = 'span#productTitle';

// 出版社確認（「いずみノベルズ」を含むか）
const publisher = 'div#detailBullets_feature_div li:contains("出版社")';
```

## スクレイピングフロー

### 1. 初期検索
```python
async def search_kindle(self, book_title: str, n_code: str):
    # 検索URLを構築
    search_query = f'"{book_title}" いずみノベルズ'
    search_url = f'https://www.amazon.co.jp/s?k={quote(search_query)}&i=digital-text'
    
    # ページ読み込み
    await page.goto(search_url)
    await page.wait_for_selector('div[data-component-type="s-search-result"]', timeout=10000)
```

### 2. 結果の解析
```python
# 検索結果を取得
results = await page.query_selector_all('div[data-component-type="s-search-result"]')

for result in results[:5]:  # 上位5件をチェック
    # タイトルを取得
    title_elem = await result.query_selector('h2 span')
    title_text = await title_elem.text_content()
    
    # タイトルマッチング
    if self.is_title_match(book_title, title_text):
        link_elem = await result.query_selector('h2 a')
        product_url = await link_elem.get_attribute('href')
        return f'https://www.amazon.co.jp{product_url}'
```

### 3. 検証処理
```python
async def verify_kindle_url(self, url: str, expected_title: str):
    await page.goto(url)
    
    # 出版社チェック
    publisher_text = await page.text_content('#detailBullets_feature_div')
    if 'いずみノベルズ' not in publisher_text:
        return False
    
    # タイトル確認
    actual_title = await page.text_content('span#productTitle')
    return self.is_title_match(expected_title, actual_title)
```

## エラーハンドリング

### 1. CAPTCHA対策
```python
# CAPTCHAの検出
if await page.query_selector('form[action="/errors/validateCaptcha"]'):
    raise CaptchaError("CAPTCHA detected, retry with delay")
```

### 2. レート制限対策
- リクエスト間隔: 2-5秒のランダム遅延
- 並列数制限: 最大2接続
- リトライ間隔: エクスポネンシャルバックオフ（2, 4, 8秒）

### 3. 検索結果なしの処理
```python
# 結果が0件の場合
if not results:
    # 別の検索パターンを試行
    return await self.search_with_alternative_pattern(book_title)
```

## タイトルマッチングロジック

### 1. 正規化処理
```python
def normalize_title(self, title: str) -> str:
    # 全角・半角の統一
    title = unicodedata.normalize('NFKC', title)
    
    # 記号の除去
    title = re.sub(r'[【】\[\]（）\(\)「」『』]', '', title)
    
    # スペースの正規化
    title = re.sub(r'\s+', ' ', title).strip()
    
    return title.lower()
```

### 2. 類似度判定
```python
def is_title_match(self, expected: str, actual: str) -> bool:
    # 正規化
    expected_norm = self.normalize_title(expected)
    actual_norm = self.normalize_title(actual)
    
    # 完全一致
    if expected_norm == actual_norm:
        return True
    
    # 部分一致（期待タイトルが実際のタイトルに含まれる）
    if expected_norm in actual_norm:
        return True
    
    # レーベンシュタイン距離
    similarity = 1 - (editdistance.eval(expected_norm, actual_norm) / max(len(expected_norm), len(actual_norm)))
    return similarity > 0.85
```

## 特殊ケース

### 1. シリーズ物の処理
- 巻数付きタイトル: 「タイトル 第1巻」
- 副題付き: 「タイトル ～副題～」
- 分冊版: 検索から除外

### 2. 価格0円の書籍
- Kindle Unlimitedの表示確認
- 通常価格の取得

### 3. 予約商品
- 発売日の取得
- URLは取得可能

## テストケース

### 1. 基本検索
- タイトル: "ネット通販から始まる、現代の魔術師"
- 期待結果: 正しいKindle URLを取得

### 2. 特殊文字を含むタイトル
- タイトル: "異世界で『魔法』を作る！"
- 課題: 記号のエスケープ処理

### 3. 長いタイトル
- 32文字以上のタイトルでの検索
- 省略されたタイトルとのマッチング

## パフォーマンス目標
- 1書籍あたりの処理時間: 5-10秒
- 成功率: 95%以上
- タイムアウト: 30秒

## セキュリティ考慮事項
- User-Agentの適切な設定
- リファラーの設定
- クッキーの管理（セッション維持）
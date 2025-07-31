# 楽天Kobo スクレイピング仕様書

## 概要
楽天Kobo電子書籍ストアからいずみノベルズタイトルのURLを取得する仕様。

## 基本情報
- **サイト名**: 楽天Kobo
- **ベースURL**: https://books.rakuten.co.jp/e-book/
- **検索方式**: タイトル検索 + 出版社フィルタ
- **安定性**: 高（楽天のインフラは安定）
- **レート制限**: 緩い（Amazonより寛容）

## 検索戦略

### 1. 検索URL構成
```
https://search.books.rakuten.co.jp/bksearch/dt?g=101&sitem={タイトル}+いずみノベルズ
```

### 2. 検索パラメータ
- `g`: ジャンル（101 = 電子書籍）
- `sitem`: 検索キーワード
- `v`: 表示形式（2 = リスト表示）

### 3. 詳細検索オプション
```
https://books.rakuten.co.jp/search?sitem={タイトル}&g=101&f=2&v=2&s=1&e=0
```
- `f=2`: 電子書籍のみ
- `s=1`: 発売日順
- `e=0`: 在庫ありのみ

## セレクタ仕様

### 検索結果ページ
```javascript
// 検索結果アイテム
const resultItems = 'div.rbcomp__item';

// 商品リンク
const productLink = 'div.rbcomp__item-info__title a';

// タイトル
const title = 'div.rbcomp__item-info__title a';

// 著者名
const author = 'div.rbcomp__item-info__author a';

// 出版社
const publisher = 'div.rbcomp__item-info__details span:contains("出版社")';

// 価格
const price = 'span.rbcomp__item-price__num';
```

### 商品詳細ページ（検証用）
```javascript
// ISBN/商品番号
const itemNumber = 'span[itemprop="productID"]';

// 詳細タイトル
const detailTitle = 'h1[itemprop="name"]';

// 出版社確認
const publisherDetail = 'div.productPublisher a';

// 電子書籍フォーマット確認
const format = 'span.format';
```

## スクレイピングフロー

### 1. 初期検索
```python
async def search_kobo(self, book_title: str, n_code: str):
    # 検索パラメータ
    params = {
        'g': '101',  # 電子書籍
        'sitem': f'{book_title} いずみノベルズ',
        'v': '2',    # リスト表示
        'f': '2'     # 電子書籍のみ
    }
    
    search_url = 'https://search.books.rakuten.co.jp/bksearch/dt'
    full_url = f"{search_url}?{'&'.join([f'{k}={quote(str(v))}' for k, v in params.items()])}"
    
    await page.goto(full_url)
    await page.wait_for_selector('div.rbcomp__item', timeout=10000)
```

### 2. 結果の解析
```python
# 検索結果を取得
results = await page.query_selector_all('div.rbcomp__item')

for result in results[:10]:  # 上位10件をチェック
    # 出版社チェック
    publisher_elem = await result.query_selector('div.rbcomp__item-info__details')
    if publisher_elem:
        publisher_text = await publisher_elem.text_content()
        if 'いずみノベルズ' not in publisher_text:
            continue
    
    # タイトル取得
    title_elem = await result.query_selector('div.rbcomp__item-info__title a')
    title_text = await title_elem.text_content()
    
    # マッチング確認
    if self.is_title_match(book_title, title_text):
        product_url = await title_elem.get_attribute('href')
        return product_url
```

### 3. 検証処理
```python
async def verify_kobo_url(self, url: str, expected_title: str):
    await page.goto(url)
    
    # 電子書籍フォーマット確認
    format_elem = await page.query_selector('span.format')
    if format_elem:
        format_text = await format_elem.text_content()
        if 'kobo' not in format_text.lower():
            return False
    
    # 出版社確認
    publisher_elem = await page.query_selector('div.productPublisher a')
    if publisher_elem:
        publisher_text = await publisher_elem.text_content()
        if 'いずみノベルズ' not in publisher_text:
            return False
    
    return True
```

## エラーハンドリング

### 1. 検索結果0件
```python
# 結果なしメッセージの検出
no_result = await page.query_selector('p.rbcomp__noresult')
if no_result:
    # 検索キーワードを調整して再試行
    return await self.search_with_shorter_title(book_title)
```

### 2. タイムアウト対策
- ページ読み込みタイムアウト: 30秒
- セレクタ待機タイムアウト: 10秒
- リトライ回数: 3回

### 3. 楽天特有のポップアップ
```python
# キャンペーンポップアップを閉じる
popup_close = await page.query_selector('button.popup-close')
if popup_close:
    await popup_close.click()
```

## 特殊ケース

### 1. 楽天ポイント表示
- ポイント還元率の取得（オプション）
- 実質価格の計算

### 2. 複数フォーマット
- 同一書籍で複数フォーマット（ePub/PDF）がある場合
- 標準フォーマット（ePub）を優先

### 3. セット商品
- まとめ買いセットは除外
- 単巻のみを対象とする

## タイトルマッチングロジック

### 1. 楽天特有の処理
```python
def normalize_kobo_title(self, title: str) -> str:
    # 楽天特有の表記を除去
    title = re.sub(r'【.*?】', '', title)  # 【電子書籍】など
    title = re.sub(r'\[.*?\]', '', title)  # [楽天Kobo]など
    
    # 基本正規化
    return self.normalize_title(title)
```

### 2. シリーズ名の扱い
```python
# 「シリーズ名 作品名」形式への対応
def extract_main_title(self, full_title: str) -> str:
    # パターン1: 「シリーズ名」作品名
    match = re.match(r'「(.+?)」(.+)', full_title)
    if match:
        return match.group(2).strip()
    
    return full_title
```

## API代替手段

### 楽天ブックス検索API（オプション）
```python
# APIキーが利用可能な場合
RAKUTEN_APP_ID = os.getenv('RAKUTEN_APP_ID')
if RAKUTEN_APP_ID:
    api_url = f'https://app.rakuten.co.jp/services/api/Kobo/EbookSearch/20170426'
    params = {
        'applicationId': RAKUTEN_APP_ID,
        'title': book_title,
        'publisherName': 'いずみノベルズ'
    }
```

## テストケース

### 1. 基本検索
- タイトル: "ネメシス戦域の強襲巨兵"
- 期待結果: 正しいKobo URLを取得

### 2. 出版社フィルタ
- 同名タイトルが複数出版社から出ている場合
- いずみノベルズ版のみを取得

### 3. 価格比較
- 通常価格とキャンペーン価格の取得
- ポイント還元の確認

## パフォーマンス目標
- 1書籍あたりの処理時間: 3-8秒
- 成功率: 90%以上
- API利用時の成功率: 98%以上

## セキュリティ・マナー
- robots.txtの遵守
- 適切なUser-Agent設定
- リクエスト間隔の確保（最低1秒）
- 楽天APIガイドラインの遵守（API利用時）

## 取得データ形式
```json
{
  "n_code": "N01357",
  "title": "ネット通販から始まる、現代の魔術師",
  "kobo_url": "https://books.rakuten.co.jp/rk/xxxxx/",
  "price": 1320,
  "points": 12,
  "format": "ePub",
  "scraped_at": "2024-01-20T15:30:00+09:00"
}
```
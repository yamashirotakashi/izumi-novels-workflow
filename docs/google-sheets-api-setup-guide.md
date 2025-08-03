# Google Sheets API 設定ガイド

## 📋 概要

このガイドでは、IzumiNovels-WorkflowプロジェクトでGoogle Sheets APIを使用するための設定手順を詳しく説明します。

### 必要な手順
1. Google Cloud Platform（GCP）プロジェクトの作成
2. Google Sheets APIの有効化
3. サービスアカウントの作成
4. 認証キー（JSON）の取得
5. スプレッドシートへのアクセス権限設定

---

## 🚀 Step 1: GCPプロジェクトの作成

### 1.1 Google Cloud Consoleにアクセス
1. [Google Cloud Console](https://console.cloud.google.com/)にアクセス
2. Googleアカウントでログイン

### 1.2 新規プロジェクトの作成
1. 画面上部のプロジェクトセレクタをクリック
2. 「新しいプロジェクト」をクリック
3. 以下の情報を入力：
   - **プロジェクト名**: `izumi-novels-workflow`
   - **プロジェクトID**: 自動生成されるID（変更可能）
   - **組織**: なし（個人アカウントの場合）
4. 「作成」をクリック

![プロジェクト作成画面](https://via.placeholder.com/600x400?text=Project+Creation+Screen)

---

## 📚 Step 2: Google Sheets APIの有効化

### 2.1 APIライブラリへ移動
1. 左側メニューから「APIとサービス」→「ライブラリ」をクリック
2. または直接アクセス: [API Library](https://console.cloud.google.com/apis/library)

### 2.2 Google Sheets APIを検索・有効化
1. 検索バーに「Google Sheets API」と入力
2. 検索結果から「Google Sheets API」をクリック
3. 「有効にする」ボタンをクリック
4. APIが有効になるまで待機（通常数秒）

### 2.3 確認
- 「APIとサービス」→「有効なAPI」で Google Sheets API が表示されることを確認

---

## 🔐 Step 3: サービスアカウントの作成

### 3.1 認証情報ページへ移動
1. 「APIとサービス」→「認証情報」をクリック
2. または直接アクセス: [Credentials](https://console.cloud.google.com/apis/credentials)

### 3.2 サービスアカウント作成
1. 「+ 認証情報を作成」→「サービスアカウント」を選択
2. 以下の情報を入力：

#### サービスアカウントの詳細
```
サービスアカウント名: izumi-workflow-bot
サービスアカウントID: izumi-workflow-bot（自動入力）
サービスアカウントの説明: いずみノベルズ販売リンク自動化システム用
```

3. 「作成して続行」をクリック

#### ロールの設定（オプション）
- 今回はスキップ可能（「続行」をクリック）
- 必要に応じて「編集者」ロールを付与

#### ユーザーアクセス（オプション）
- スキップ可能（「完了」をクリック）

---

## 🔑 Step 4: 認証キー（JSON）の生成

### 4.1 キーの作成
1. 作成したサービスアカウントをクリック
2. 「キー」タブを選択
3. 「鍵を追加」→「新しい鍵を作成」をクリック
4. 「JSON」を選択（デフォルト）
5. 「作成」をクリック

### 4.2 JSONファイルの保存
- ファイルが自動的にダウンロードされます
- ファイル名例: `izumi-novels-workflow-xxxxxx.json`
- **重要**: このファイルは秘密情報です。Git管理から除外してください

### 4.3 JSONファイルの配置
```bash
# プロジェクトディレクトリに移動
cd /mnt/c/Users/tky99/DEV/izumi-novels-workflow

# configディレクトリにJSONを配置
mkdir -p config/credentials
mv ~/Downloads/izumi-novels-workflow-*.json config/credentials/google-sheets-key.json

# .gitignoreに追加
echo "config/credentials/" >> .gitignore
```

---

## 📊 Step 5: Google Sheetsの準備

管理用スプレッドシートは既存のNコードから作品検索も行うシートで一元管理する。

ワークブック名
いずみノベルズスケジュール・刊行時設定情報
https://docs.google.com/spreadsheets/d/1hMhDw3HJsUMetceMvy2lszDeLCxarNavn_2E6Inf84M/edit?usp=sharing

シート名
作業管理

D列：Nコード
E列：書籍名
AA列　Kindle
AB列　AmazonPOD（印刷版）
AC列　BookWalker
AD列　Kobo
AE列　Google
AF列　Apple
AG列　Kinoppy
AH列　honto
AI列　ReaderStore
AJ列　BookLive
AK列　ebookjapan






### 5.3 サービスアカウントへの権限付与
1. スプレッドシートの「共有」ボタンをクリック
2. サービスアカウントのメールアドレスを入力：
   ```
   izumi-workflow-bot@izumi-novels-workflow.iam.gserviceaccount.com
   ```
3. 権限を「編集者」に設定
4. 「送信」をクリック

### 5.4 スプレッドシートIDの取得
1hMhDw3HJsUMetceMvy2lszDeLCxarNavn_2E6Inf84M

- URL例: `https://docs.google.com/spreadsheets/d/[SPREADSHEET_ID]/edit`
- `SPREADSHEET_ID`の部分をコピー（例: `1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms`）

---

## 🐍 Step 6: Pythonコードでの使用

### 6.1 必要なライブラリのインストール
```bash
pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib
```

### 6.2 認証とクライアント初期化
```python
# src/scraping/google_sheets_client.py
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import json

class GoogleSheetsClient:
    def __init__(self, credentials_path: str, spreadsheet_id: str):
        """Google Sheets APIクライアントの初期化
        
        Args:
            credentials_path: サービスアカウントJSONファイルのパス
            spreadsheet_id: スプレッドシートID
        """
        self.spreadsheet_id = spreadsheet_id
        
        # 認証情報の読み込み
        self.creds = Credentials.from_service_account_file(
            credentials_path,
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        )
        
        # APIクライアントの構築
        self.service = build('sheets', 'v4', credentials=self.creds)
        self.sheet = self.service.spreadsheets()
    
    def read_master_sheet(self) -> list:
        """マスターシートからデータを読み取る"""
        result = self.sheet.values().get(
            spreadsheetId=self.spreadsheet_id,
            range='マスター!A2:F'  # ヘッダーを除く全行
        ).execute()
        
        return result.get('values', [])
    
    def update_sales_links(self, links: list) -> bool:
        """販売リンクシートを更新"""
        body = {
            'values': links
        }
        
        result = self.sheet.values().append(
            spreadsheetId=self.spreadsheet_id,
            range='販売リンク!A2',
            valueInputOption='USER_ENTERED',
            body=body
        ).execute()
        
        return result.get('updates', {}).get('updatedCells', 0) > 0
```

### 6.3 環境変数の設定
```bash
# .env ファイル
GOOGLE_SHEETS_CREDENTIALS_PATH=config/credentials/google-sheets-key.json
GOOGLE_SHEETS_SPREADSHEET_ID=your_spreadsheet_id_here
```

### 6.4 使用例
```python
# scripts/test_google_sheets.py
import os
from dotenv import load_dotenv
from src.scraping.google_sheets_client_consolidated import GoogleSheetsClient

# 環境変数の読み込み
load_dotenv()

# クライアントの初期化
client = GoogleSheetsClient(
    credentials_path=os.getenv('GOOGLE_SHEETS_CREDENTIALS_PATH'),
    spreadsheet_id=os.getenv('GOOGLE_SHEETS_SPREADSHEET_ID')
)

# マスターデータの読み取り
books = client.read_master_sheet()
for book in books:
    print(f"N番号: {book[0]}, タイトル: {book[1]}")

# 販売リンクの更新
new_links = [
    ['link_001', 'n1234567', 'Amazon Kindle', 'https://...', '1320', '2025-01-31 10:00:00'],
    ['link_002', 'n1234567', '楽天Kobo', 'https://...', '1320', '2025-01-31 10:00:00']
]
client.update_sales_links(new_links)
```

---

## 🔧 トラブルシューティング

### よくあるエラーと対処法

#### 1. 認証エラー
```
google.auth.exceptions.DefaultCredentialsError: Could not automatically determine credentials
```
**対処法**: 
- JSONファイルのパスが正しいか確認
- ファイルの読み取り権限を確認

#### 2. 権限エラー
```
googleapiclient.errors.HttpError: 403 The caller does not have permission
```
**対処法**:
- サービスアカウントのメールアドレスがスプレッドシートに共有されているか確認
- 編集権限が付与されているか確認

#### 3. API未有効化エラー
```
Google Sheets API has not been used in project
```
**対処法**:
- GCPコンソールでGoogle Sheets APIが有効になっているか確認
- プロジェクトIDが正しいか確認

#### 4. レート制限エラー
```
Quota exceeded for quota metric 'Read requests'
```
**対処法**:
- リクエスト間隔を調整（1秒以上の間隔を推奨）
- バッチ処理を使用してリクエスト数を削減

---

## 📝 セキュリティのベストプラクティス

### 1. 認証情報の管理
- JSONファイルは絶対にGitにコミットしない
- 環境変数や秘密管理ツールを使用
- 定期的にキーをローテーション

### 2. アクセス権限
- サービスアカウントには最小限の権限のみ付与
- 不要になったアクセス権限は即座に削除
- 定期的にアクセスログを確認

### 3. データ保護
- センシティブなデータは暗号化
- HTTPSを使用（API経由は自動的にHTTPS）
- データのバックアップを定期的に実施

---

## 🎯 次のステップ

1. **テスト実行**
   ```bash
   python scripts/test_google_sheets.py
   ```

2. **スクレイピングとの統合**
   - スクレイピング結果をGoogle Sheetsに自動保存
   - 定期実行スケジュールの設定

3. **エラー監視**
   - ログ収集システムの構築
   - アラート通知の設定

---

**作成日**: 2025-01-31  
**更新日**: 2025-01-31  
**ドキュメントバージョン**: 1.0
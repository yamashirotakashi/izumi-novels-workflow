# IzumiNovels-Workflow Windows実機テスト実行ガイド

## 📋 概要

本ガイドは、IzumiNovels-Workflowプロジェクトの**Phase 1実機テスト**をWindows PowerShell環境で実行するための手順書です。

## 🎯 テスト目的

- **Linux環境で完成したPhase 1機能のWindows環境動作確認**
- **11サイト スクレイピング機能の実機検証**
- **undetected-chromedriver + Seleniumの動作確認**
- **日本語キーワード抽出・類似度計算の精度検証**

## ⚡ クイックスタート

### 1. 環境セットアップ（初回のみ）

```powershell
# プロジェクトディレクトリに移動
cd "C:\Users\tky99\dev\izumi-novels-workflow"

# Windows環境セットアップ実行
.\scripts\windows\setup_windows_environment.ps1
```

### 2. 実機テスト実行

```powershell
# 高速テスト（推奨4サイト）
.\scripts\windows\run_windows_tests.ps1

# 全サイトテスト
.\scripts\windows\run_windows_tests.ps1 -TestType full

# 特定サイトのみテスト
.\scripts\windows\run_windows_tests.ps1 -TestType single -Site amazon
```

## 📚 詳細手順

### Step 1: 事前準備

#### 必要なソフトウェア
- **Python 3.8以上** (PATH設定済み)
- **Google Chrome** (最新版推奨)
- **PowerShell 5.1以上**

#### 確認コマンド
```powershell
# Python確認
python --version
# 期待される出力: Python 3.8.x 以上

# Chrome確認
Get-Process chrome -ErrorAction SilentlyContinue
# Chromeが見つからない場合はインストール
```

### Step 2: プロジェクト環境構築

```powershell
# プロジェクトディレクトリに移動
cd "C:\Users\tky99\dev\izumi-novels-workflow"

# 環境セットアップスクリプト実行
.\scripts\windows\setup_windows_environment.ps1

# オプション指定例
.\scripts\windows\setup_windows_environment.ps1 -Force -Verbose
```

**セットアップ内容:**
- Python仮想環境作成 (`venv/`)
- 依存パッケージインストール
- ChromeDriver動作確認
- ログ・結果出力ディレクトリ作成

### Step 3: 実機テスト実行

#### 基本実行

```powershell
# デフォルト（quick test）
.\scripts\windows\run_windows_tests.ps1
```

#### 詳細オプション

```powershell
# フルテスト（全11サイト）
.\scripts\windows\run_windows_tests.ps1 -TestType full

# 特定サイトテスト
.\scripts\windows\run_windows_tests.ps1 -TestType single -Site amazon

# ヘッドレスモード（GUI非表示）
.\scripts\windows\run_windows_tests.ps1 -Headless

# 詳細ログ出力
.\scripts\windows\run_windows_tests.ps1 -Verbose

# タイムアウト設定（秒）
.\scripts\windows\run_windows_tests.ps1 -Timeout 600
```

#### 対象サイト一覧

| サイトキー | サイト名 | 優先度 | Quick Test |
|------------|----------|--------|------------|
| amazon | Amazon Kindle | 1 | ✅ |
| bookwalker | BOOK☆WALKER | 2 | ✅ |
| rakuten | 楽天Kobo | 2 | ✅ |
| google | Google Play Books | 2 | ✅ |
| honto | honto | 3 | ❌ |
| kinoppy | 紀伊國屋書店（Kinoppy） | 3 | ❌ |
| reader_store | Reader Store | 3 | ❌ |
| apple | Apple Books | 4 | ❌ |
| booklive | BookLive | 4 | ❌ |
| ebookjapan | ebookjapan | 4 | ❌ |
| amazon_pod | Amazon POD（印刷版） | 5 | ❌ |

## 📊 テスト結果の確認

### 実行中の出力例

```
🚀 IzumiNovels-Workflow Windows実機テスト開始
============================================================
テストタイプ: quick
対象サイト: 全サイト
ヘッドレスモード: False
タイムアウト: 300 秒

🎯 テスト対象サイト (4サイト):
  - Amazon Kindle
  - BOOK☆WALKER
  - 楽天Kobo
  - Google Play Books

[1/4] 🌐 Amazon Kindle テスト開始...
✅ Amazon Kindle テスト成功 (45.2秒)

[2/4] 🌐 BOOK☆WALKER テスト開始...
✅ BOOK☆WALKER テスト成功 (38.7秒)
```

### 結果ファイル

#### サマリーファイル
```
test_results/test_summary_20250802_143022.json
```

#### 個別結果ファイル
```
test_results/amazon.json
test_results/bookwalker.json
test_results/rakuten.json
test_results/google.json
```

#### ログファイル
```
logs/windows_tests/test_execution_20250802.log
logs/windows_tests/amazon.log
logs/windows_tests/bookwalker.log
```

### 結果の読み方

#### 成功例
```json
{
  "site": "amazon",
  "name": "Amazon Kindle",
  "status": "SUCCESS",
  "message": "テスト成功: 類似度スコア 0.85",
  "duration": 45.2,
  "timestamp": "2025-08-02 14:30:22"
}
```

#### 失敗例
```json
{
  "site": "bookwalker",
  "name": "BOOK☆WALKER",
  "status": "FAILED",
  "message": "要素が見つかりません: .book-title",
  "duration": 12.1,
  "timestamp": "2025-08-02 14:31:10"
}
```

## 🔧 トラブルシューティング

### よくある問題と解決方法

#### 1. Python関連エラー

**エラー:** `python: command not found`

**解決方法:**
```powershell
# Python インストール確認
where python

# PATHに追加（例）
$env:PATH += ";C:\Python39;C:\Python39\Scripts"
```

#### 2. ChromeDriver関連エラー

**エラー:** `chromedriver executable needs to be in PATH`

**解決方法:**
- Chromeを最新版に更新
- セットアップスクリプトを再実行
```powershell
.\scripts\windows\setup_windows_environment.ps1 -Force
```

#### 3. ネットワーク関連エラー

**エラー:** `TimeoutException: Page load timeout`

**解決方法:**
```powershell
# タイムアウト延長
.\scripts\windows\run_windows_tests.ps1 -Timeout 600

# ヘッドレスモード無効化（デバッグ用）
.\scripts\windows\run_windows_tests.ps1 -Headless:$false
```

#### 4. 仮想環境関連エラー

**エラー:** `cannot activate virtual environment`

**解決方法:**
```powershell
# 実行ポリシー変更
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# 仮想環境再作成
.\scripts\windows\setup_windows_environment.ps1 -Force
```

### 詳細デバッグ

#### 詳細ログ有効化
```powershell
.\scripts\windows\run_windows_tests.ps1 -Verbose
```

#### 個別サイトデバッグ
```powershell
# 特定サイトのみ実行
.\scripts\windows\run_windows_tests.ps1 -TestType single -Site amazon -Verbose

# ヘッドレス無効（ブラウザ動作確認）
.\scripts\windows\run_windows_tests.py1 -TestType single -Site amazon -Headless:$false
```

## 📈 期待される結果

### Phase 1 品質目標

- **成功率**: 75%以上（quick test）
- **平均実行時間**: 60秒/サイト以下
- **類似度スコア**: 0.4以上

### ベンチマーク（Linux環境実績）

| サイト | 成功率 | 平均時間 | 類似度スコア |
|--------|--------|----------|--------------|
| Amazon | 100% | 45秒 | 0.85 |
| BOOK☆WALKER | 100% | 38秒 | 0.78 |
| 楽天Kobo | 95% | 52秒 | 0.72 |
| Google Play | 90% | 41秒 | 0.68 |

## 🚀 次のステップ

### テスト完了後の作業

1. **結果分析**
   - 成功率の確認
   - 失敗原因の分析
   - パフォーマンス評価

2. **問題修正** (必要に応じて)
   - サイト固有の調整
   - タイムアウト設定最適化
   - エラーハンドリング改善

3. **Phase 2 準備**
   - WordPress REST API統合テスト
   - GoogleSheets連携確認
   - 運用環境デプロイ準備

## 📞 サポート

### 問題報告先
- **プロジェクトリポジトリ**: Issues
- **ログファイル**: `logs/windows_tests/`
- **設定ファイル**: `config/site_selectors.json`

### 緊急時の対応
1. 全テスト停止: `Ctrl + C`
2. 仮想環境リセット: `.\scripts\windows\setup_windows_environment.ps1 -Force`
3. Chrome プロセス強制終了: `taskkill /f /im chrome.exe`

---

**更新日**: 2025-08-02  
**バージョン**: Phase 1.0  
**作成者**: IzumiNovels-Workflow開発チーム
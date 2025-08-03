# Windows実機テスト実行環境

## 📋 概要

IzumiNovels-Workflow Phase 1のWindows環境での実機テスト実行に必要なPowerShellスクリプト群です。

## 📁 ファイル構成

```
scripts/windows/
├── setup_windows_environment.ps1    # 環境セットアップ
├── run_windows_tests.ps1            # 実機テスト実行
├── generate_test_report.ps1          # レポート生成
└── README.md                        # 本ファイル
```

## 🚀 クイックスタート

### 1. 環境セットアップ

```powershell
# プロジェクトルートに移動
cd "C:\Users\tky99\dev\izumi-novels-workflow"

# 初回セットアップ実行
.\scripts\windows\setup_windows_environment.ps1
```

### 2. テスト実行

```powershell
# 高速テスト（推奨4サイト）
.\scripts\windows\run_windows_tests.ps1

# 全サイトテスト
.\scripts\windows\run_windows_tests.ps1 -TestType full
```

### 3. レポート生成

```powershell
# HTMLレポート生成
.\scripts\windows\generate_test_report.ps1

# CSVレポート生成
.\scripts\windows\generate_test_report.ps1 -OutputFormat csv
```

## 📚 詳細な使用方法

詳細な手順については以下をご参照ください：
- [Windows実機テスト実行ガイド](../../docs/windows_testing_guide.md)

## 🎯 スクリプト詳細

### setup_windows_environment.ps1

**用途**: Windows環境でのプロジェクト実行環境構築

**機能**:
- Python仮想環境作成
- 依存パッケージインストール
- ChromeDriver動作確認
- ディレクトリ構成初期化

**オプション**:
- `-Force`: 既存環境の強制再作成
- `-Verbose`: 詳細ログ出力

### run_windows_tests.ps1

**用途**: Windows環境での実機テスト実行

**機能**:
- 11サイトのスクレイピングテスト
- 結果の構造化記録
- ログ出力・管理
- 成功率・パフォーマンス測定

**オプション**:
- `-TestType`: テストタイプ（quick/full/single）
- `-Site`: 特定サイトのみテスト
- `-Headless`: ヘッドレスモード
- `-Verbose`: 詳細出力
- `-Timeout`: タイムアウト設定（秒）

### generate_test_report.ps1

**用途**: テスト結果の包括的レポート生成

**機能**:
- HTML/CSV/JSON形式でのレポート出力
- 成功率・パフォーマンス分析
- 視覚的なダッシュボード
- Phase 1品質評価

**オプション**:
- `-InputPath`: 特定の結果ファイル指定
- `-OutputFormat`: 出力形式（html/csv/json）
- `-OpenReport`: レポート自動オープン
- `-Verbose`: 詳細出力

## 🔧 実行例

### 基本的な実行フロー

```powershell
# 1. 初回セットアップ
.\scripts\windows\setup_windows_environment.ps1

# 2. 高速テスト実行
.\scripts\windows\run_windows_tests.ps1

# 3. HTMLレポート生成・表示
.\scripts\windows\generate_test_report.ps1
```

### 詳細テスト・デバッグ

```powershell
# 特定サイトの詳細テスト
.\scripts\windows\run_windows_tests.ps1 -TestType single -Site amazon -Verbose -Headless:$false

# 全サイトテスト（タイムアウト延長）
.\scripts\windows\run_windows_tests.ps1 -TestType full -Timeout 600

# CSVレポート生成
.\scripts\windows\generate_test_report.ps1 -OutputFormat csv -OpenReport:$false
```

### 環境再構築

```powershell
# 仮想環境完全再作成
.\scripts\windows\setup_windows_environment.ps1 -Force -Verbose

# Chrome関連問題の対処
taskkill /f /im chrome.exe
.\scripts\windows\setup_windows_environment.ps1 -Force
```

## 📊 出力ファイル

### ディレクトリ構造

```
izumi-novels-workflow/
├── logs/
│   └── windows_tests/           # テスト実行ログ
│       ├── test_execution_YYYYMMDD.log
│       ├── amazon.log
│       └── bookwalker.log
├── test_results/                # テスト結果JSON
│   ├── test_summary_YYYYMMDD_HHMMSS.json
│   ├── amazon.json
│   └── bookwalker.json
└── reports/                     # 生成レポート
    ├── test_report_YYYYMMDD_HHMMSS.html
    ├── test_report_YYYYMMDD_HHMMSS.csv
    └── test_report_YYYYMMDD_HHMMSS.json
```

### ファイル形式

#### テスト結果 (JSON)
```json
{
  "site": "amazon",
  "name": "Amazon Kindle",
  "status": "SUCCESS",
  "message": "類似度スコア: 0.85",
  "duration": 45.2,
  "timestamp": "2025-08-02 14:30:22"
}
```

#### サマリーファイル (JSON)
```json
{
  "timestamp": "2025-08-02 14:30:00",
  "test_type": "quick",
  "total_tests": 4,
  "success_count": 3,
  "failed_count": 1,
  "success_rate": 75.0,
  "total_duration": 180.5,
  "results": [...]
}
```

## 🔍 トラブルシューティング

### 一般的な問題

1. **PowerShell実行ポリシーエラー**
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```

2. **Python/仮想環境問題**
   ```powershell
   .\scripts\windows\setup_windows_environment.ps1 -Force
   ```

3. **Chrome/ChromeDriverエラー**
   ```powershell
   taskkill /f /im chrome.exe
   # Chrome最新版に更新後
   .\scripts\windows\setup_windows_environment.ps1 -Force
   ```

### ログ確認

```powershell
# セットアップログ
Get-Content "logs\windows_setup.log" -Tail 20

# テスト実行ログ
Get-Content "logs\windows_tests\test_execution_$(Get-Date -Format 'yyyyMMdd').log" -Tail 50

# 特定サイトのエラー詳細
Get-Content "logs\windows_tests\amazon.log"
```

## 📈 期待される結果

### Phase 1 品質目標
- **成功率**: 75%以上
- **平均実行時間**: 60秒/サイト以下
- **類似度スコア**: 0.4以上

### Linux環境ベンチマーク
- Amazon: 100%成功率、45秒、0.85スコア
- BOOK☆WALKER: 100%成功率、38秒、0.78スコア
- 楽天Kobo: 95%成功率、52秒、0.72スコア
- Google Play: 90%成功率、41秒、0.68スコア

## 📞 サポート

### 問題が発生した場合

1. **ログファイル確認**
2. **環境再セットアップ実行**
3. **個別サイトテスト実行**
4. **詳細ログでのデバッグ**

### 緊急時対応

```powershell
# 全プロセス停止
Get-Process python,chrome | Stop-Process -Force

# 環境完全リセット
Remove-Item -Recurse -Force venv
.\scripts\windows\setup_windows_environment.ps1 -Force
```

---

**作成日**: 2025-08-02  
**対象**: Phase 1 Windows実機テスト  
**更新者**: IzumiNovels-Workflow開発チーム
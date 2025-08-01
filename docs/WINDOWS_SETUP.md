# Windows環境セットアップガイド

## ⚠️ 重要: WSLとWindowsの違い

WSL（Windows Subsystem for Linux）とネイティブWindows環境では、以下の点で大きく異なります：

1. **仮想環境の非互換性**
   - WSLで作成した仮想環境（`phase1_venv`等）はWindows環境では使用不可
   - Windows専用の仮想環境（`venv_windows`）を別途作成が必要

2. **パスの違い**
   - WSL: `/mnt/c/Users/tky99/DEV/izumi-novels-workflow`
   - Windows: `C:\Users\tky99\DEV\izumi-novels-workflow`

3. **Chrome実行の違い**
   - WSL: GUI表示に制限あり（headlessモード推奨）
   - Windows: 完全なGUI表示可能

## 🚀 Windows環境セットアップ手順

### 1. 前提条件
- Python 3.8以上がインストール済み
- Google Chromeがインストール済み
- PowerShellの実行ポリシーが適切に設定済み

### 2. セットアップ実行

```powershell
# プロジェクトディレクトリに移動
cd C:\Users\tky99\DEV\izumi-novels-workflow

# Windows用テストスクリプトを実行
powershell -ExecutionPolicy Bypass -File scripts\windows_test.ps1
```

### 3. 初回実行時の動作
1. Windows用仮想環境（`venv_windows`）を自動作成
2. 必要な依存関係を自動インストール
3. Windows固有の依存関係（pywin32等）を追加インストール
4. Chrome環境の自動検出と確認
5. Phase 1テストの実行

## 📋 手動セットアップ（必要な場合）

```powershell
# 1. Windows用仮想環境の作成
python -m venv venv_windows

# 2. 仮想環境の有効化
.\venv_windows\Scripts\Activate.ps1

# 3. 依存関係のインストール
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install pywin32  # Windows固有

# 4. 環境確認
python -c "import undetected_chromedriver; print('✅ UC ready')"
```

## 🔍 トラブルシューティング

### Chrome が見つからない場合
```powershell
# Chromeのインストール確認
Get-ItemProperty HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\* | Select-Object DisplayName | Where-Object {$_.DisplayName -like "*Chrome*"}
```

### PowerShell実行ポリシーエラー
```powershell
# 管理者権限で実行
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 仮想環境の有効化エラー
```powershell
# 代替方法
& "C:\Users\tky99\DEV\izumi-novels-workflow\venv_windows\Scripts\python.exe" your_script.py
```

## 📊 期待される結果

### Phase 1検証テスト
- **合格率**: 93.8%以上（WSL環境と同等）
- **Chrome互換性**: PASS（Windows環境では完全サポート）
- **GUI表示**: 完全動作

### 実行時の表示例
```
🚀 IzumiNovels-Workflow Phase 1 Windows実機テスト開始
======================================================================
✅ Windows用仮想環境を有効化しています...
✅ Chrome検出: C:\Program Files\Google\Chrome\Application\chrome.exe

📋 Phase 1基本動作確認テスト
[1/5] モジュールインポートテスト...
✅ SeleniumBaseScraper: OK
✅ KinoppyAdvanced: OK
✅ ReaderStoreAdvanced: OK
✅ undetected-chromedriver: OK

[2/5] スクレイパー初期化テスト...
✅ Kinoppyスクレイパー初期化: OK
✅ Reader Storeスクレイパー初期化: OK

📊 テスト結果サマリー:
  総合ステータス: EXCELLENT
  合格率: 100%
```

## 💡 次のステップ

1. **実サイトテスト**
   - Kinoppyでの書籍検索実行
   - Reader Storeでの検索実行

2. **成功率測定**
   - 複数の書籍タイトルでテスト
   - 成功/失敗のログ収集

3. **Phase 2準備**
   - 中安定性サイトの追加実装
   - WordPress連携機能の開発
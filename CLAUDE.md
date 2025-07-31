# IzumiNovels-Workflow プロジェクト設定

## グローバルルールの継承
@../CLAUDE.md

## プロジェクト概要
いずみノベルズの販売リンク自動収集・WordPress自動投稿システム

### 目的
- 毎月3冊×11サイト=33リンクの手動収集作業を自動化
- 月165分→15分（90%削減）の効率化実現
- 社長の時間を戦略的業務にシフト

### 技術スタック
- **フロントエンド**: WordPress + ACF Pro（導入済み）
- **バックエンド**: Python + Playwright/Selenium
- **データ管理**: Google Sheets API
- **連携**: WordPress REST API

## プロジェクト固有プロンプト

### [izumiwf] または [iwf]
IzumiNovels-Workflowプロジェクト専用プロンプト
- プロジェクトディレクトリ自動移動
- 開発状況確認
- システム動作テスト

### [LinkCheck] 
11サイトの販売リンク状態確認
- URL有効性チェック
- サイト構造変更検知
- エラーレポート生成

### [AutoUpdate]
自動更新システムの手動実行
- Googleシートからデータ取得
- リンク収集実行
- WordPress自動投稿

## 対象販売サイト

### 電子書籍版（10サイト）
1. Amazon Kindle
2. BOOK☆WALKER  
3. ebookjapan
4. 楽天Kobo
5. BookLive
6. honto
7. 紀伊國屋書店（Kinoppy）
8. Apple Books
9. Google Play Books
10. Reader Store（Sony）

### 印刷版（1サイト）
11. Amazon POD

## 開発フェーズ

### Phase 1: 基盤構築（4-6週間）
- ACF Pro設定
- 安定3サイト自動化（Amazon、楽天、Google）
- WordPress REST API統合

### Phase 2: 拡張実装（2-3週間）
- 中安定性サイト追加（honto、Apple等）
- エラーハンドリング強化

### Phase 3: 完全自動化（3-4週間）
- 全11サイト対応
- Googleシート完全統合
- 監視・アラート機能

## 品質基準

### パフォーマンス
- リンク収集時間: 11サイト合計5分以内
- WordPress投稿: 30秒以内

### 信頼性
- 成功率: 95%以上
- エラー時の自動復旧
- ログ・監視機能

### 保守性
- モジュール化設計
- サイト別独立性
- 設定変更の容易性

## リスク管理

### 技術的リスク
- サイト構造変更への対応
- CAPTCHA・レート制限
- WordPress/プラグイン更新影響

### 対策
- 月次保守契約（2万円/月）
- グレースフル・デグラデーション
- 段階的劣化設計

## 成功指標

### 定量的指標
- 作業時間削減: 90%達成
- システム稼働率: 95%以上
- エラー率: 5%以下

### 定性的指標
- 社長の満足度
- 運用負荷の軽減
- 新規事業への時間創出

---

**次回セッション**: Phase 1実装開始
**優先度**: 🟡 High Priority
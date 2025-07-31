# スクレイピング戦略・ツール選定指針

## サイト別最適ツール選定

### Tier 1: 軽量ツール（requests + BeautifulSoup）
**特徴**: 最高速度、軽量、サーバーレンダリング
**適用対象**:
- Amazon Kindle ✅
  - 理由: 基本的なHTMLレンダリング、検索結果が静的
  - 期待パフォーマンス: ~2秒/検索
- 楽天Kobo ✅ 
  - 理由: 従来型Web構造、JSミニマル
  - 期待パフォーマンス: ~1.5秒/検索

### Tier 2: 中軽量ツール（httpx + lxml）
**特徴**: 非同期処理、高速XML解析
**適用対象**:
- Google Play Books 🤔
  - 理由: API的アクセス可能性、XMLレスポンス
  - 期待パフォーマンス: ~1秒/検索
- Reader Store（Sony） 🤔
  - 理由: 比較的シンプルな構造予想
  - 期待パフォーマンス: ~2秒/検索

### Tier 3: ブラウザ自動化（Playwright）
**特徴**: JS完全対応、モダンブラウザ
**適用対象**:
- BOOK☆WALKER ⚠️
  - 理由: 中程度のJS使用、検索フィルタリング
  - 期待パフォーマンス: ~5秒/検索
- ebookjapan 🎯
  - 理由: Yahoo系、React使用予想
  - 期待パフォーマンス: ~4秒/検索
- BookLive 🎯
  - 理由: SPAアーキテクチャ予想
  - 期待パフォーマンス: ~4秒/検索

### Tier 4: 重量ツール（Selenium WebDriver）
**特徴**: 最高互換性、重厚、複雑JS対応
**適用対象**:
- Apple Books 🔥
  - 理由: 重いJS、複雑認証、地域制限
  - 期待パフォーマンス: ~8秒/検索
- honto 🔥
  - 理由: 書店系複雑UI、検索挙動が特殊
  - 期待パフォーマンス: ~6秒/検索
- 紀伊國屋書店（Kinoppy） 🔥
  - 理由: 従来型JSフレームワーク、複雑検索
  - 期待パフォーマンス: ~7秒/検索

## パフォーマンス目標設定

### 速度階層
1. **Ultra Fast** (0.5-2秒): requests + BeautifulSoup
2. **Fast** (1-3秒): httpx + lxml  
3. **Standard** (3-6秒): Playwright
4. **Slow** (5-10秒): Selenium

### 全体目標
- **11サイト合計**: 5分以内（平均27秒/サイト）
- **成功率**: 95%以上
- **リトライ込み**: 最大7.5分

## 実装優先順位

### Phase 2A: 軽量ツール先行実装（1週間）
1. requests + BeautifulSoup基盤クラス作成
2. Amazon Kindle実装（既存Playwright→移行）
3. 楽天Kobo実装（既存Playwright→移行）
4. パフォーマンス比較検証

### Phase 2B: 中軽量ツール（1週間）
1. httpx + lxml基盤クラス作成
2. Google Play Books移行検討
3. Reader Store実装

### Phase 2C: ブラウザ自動化継続（1週間）
1. BOOK☆WALKER（Playwright）最適化
2. ebookjapan（Playwright）実装
3. BookLive（Playwright）実装

### Phase 2D: 重量ツール最後（1週間）
1. Selenium基盤クラス作成
2. Apple Books実装
3. honto実装
4. Kinoppy実装

## エラーハンドリング戦略

### ツール別フォールバック
```python
def get_optimal_scraper(site_name: str) -> BaseScraper:
    primary_tool = SITE_TOOL_MAP[site_name]
    fallback_tool = FALLBACK_MAP[site_name]
    
    try:
        return primary_tool()
    except InitializationError:
        logger.warning(f"{site_name}: フォールバック {fallback_tool}")
        return fallback_tool()
```

### フォールバックマッピング
- requests失敗 → httpx
- httpx失敗 → Playwright  
- Playwright失敗 → Selenium
- Selenium失敗 → 手動確認要求

## 開発・テスト方針

### 段階的検証
1. **ツール基盤テスト**: 各ツールの基本動作確認
2. **サイト適合性テスト**: 1サイト×1ツールの詳細検証
3. **パフォーマンステスト**: 速度・安定性の計測
4. **統合テスト**: 全サイト×全ツールのマトリックステスト

### メトリクス収集
- 処理時間（初期化、検索、パース）
- メモリ使用量
- 成功率
- エラー分類

---

**最終更新**: 2025-07-31
**ステータス**: Phase 2A 準備完了
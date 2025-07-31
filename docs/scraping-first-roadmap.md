# スクレイピング先行実装ロードマップ

## 📋 概要

### 背景
WordPress統合は管理会社の回答待ちのため、先行してスクレイピング機能を独立して開発する。これにより：
- 技術的な課題を早期に発見・解決
- 動作するプロトタイプを早期に準備
- 管理会社へのデモが可能に

### 基本方針
- **独立動作**: WordPress連携なしで単独動作可能
- **モジュール設計**: 後でWordPressと容易に統合可能
- **段階的実装**: 安定サイトから順次対応

---

## 🏗️ アーキテクチャ設計

### システム構成
```
┌─────────────────────────────────────────────────────┐
│                 Scraping Engine                     │
│  ┌────────────────────────────────────────────┐    │
│  │            Core Components                  │    │
│  │  ┌─────────────┐  ┌──────────────────┐   │    │
│  │  │ BaseScraper │  │ ScrapingManager  │   │    │
│  │  └─────────────┘  └──────────────────┘   │    │
│  └────────────────────────────────────────────┘    │
│                                                     │
│  ┌────────────────────────────────────────────┐    │
│  │            Site Adapters                   │    │
│  │  ┌───────────┐ ┌───────────┐ ┌──────────┐│    │
│  │  │  Amazon   │ │  Rakuten  │ │  Google  ││    │
│  │  │  Kindle   │ │   Kobo    │ │  Play    ││    │
│  │  └───────────┘ └───────────┘ └──────────┘│    │
│  │  ... (他8サイト)                           │    │
│  └────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────┘
                         │
                         ▼
              ┌──────────────────┐
              │   Output Layer   │
              │  - JSON Export   │
              │  - CSV Export    │
              │  - API Ready     │
              └──────────────────┘
```

### ディレクトリ構造
```
izumi-novels-workflow/
├── src/
│   ├── scraping/
│   │   ├── __init__.py
│   │   ├── base/
│   │   │   ├── base_scraper.py      # 基底クラス
│   │   │   ├── exceptions.py        # カスタム例外
│   │   │   └── utils.py            # 共通ユーティリティ
│   │   ├── adapters/
│   │   │   ├── amazon_kindle.py    # Amazonアダプター
│   │   │   ├── rakuten_kobo.py     # 楽天アダプター
│   │   │   ├── google_play.py      # Google Playアダプター
│   │   │   └── ... (他8サイト)
│   │   ├── manager.py               # スクレイピング管理
│   │   └── config.py               # 設定管理
│   └── models/
│       ├── book.py                  # 書籍データモデル
│       └── sales_link.py            # 販売リンクモデル
├── tests/
│   ├── unit/                        # ユニットテスト
│   └── integration/                 # 統合テスト
├── docker/
│   ├── Dockerfile                   # Playwright環境
│   └── docker-compose.yml
└── scripts/
    ├── validate_selectors.py        # セレクタ検証
    └── test_single_site.py         # 単一サイトテスト
```

---

## 📊 実装優先順位

### Phase A: 基盤構築（1週間）

#### 1. 開発環境セットアップ
```yaml
# docker-compose.yml
version: '3.8'
services:
  playwright:
    build: ./docker
    volumes:
      - ./src:/app/src
      - ./tests:/app/tests
    environment:
      - PYTHONPATH=/app
      - HEADLESS=true
    command: python -m pytest tests/ -v
```

#### 2. 基底クラス設計
```python
# base_scraper.py
from abc import ABC, abstractmethod
from playwright.async_api import async_playwright
import asyncio
from typing import Optional, Dict, List

class BaseScraper(ABC):
    """全サイト共通の基底スクレイパークラス"""
    
    def __init__(self, headless: bool = True, timeout: int = 30000):
        self.headless = headless
        self.timeout = timeout
        self.browser = None
        self.page = None
        
    async def initialize(self):
        """ブラウザ初期化"""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=self.headless,
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )
        self.page = await self.browser.new_page()
        
    @abstractmethod
    async def search_book(self, n_code: str, title: str) -> Optional[str]:
        """書籍検索（各サイトで実装）"""
        pass
        
    @abstractmethod
    async def extract_book_info(self, url: str) -> Dict:
        """書籍情報抽出（各サイトで実装）"""
        pass
        
    async def close(self):
        """リソースクリーンアップ"""
        if self.browser:
            await self.browser.close()
```

### Phase B: 高安定サイト実装（1週間）

#### 3. Amazon Kindleアダプター
```python
# adapters/amazon_kindle.py
class AmazonKindleScraper(BaseScraper):
    BASE_URL = "https://www.amazon.co.jp"
    
    async def search_book(self, n_code: str, title: str) -> Optional[str]:
        # 検索ページへ移動
        search_url = f"{self.BASE_URL}/s?k={title}+{n_code}"
        await self.page.goto(search_url, wait_until='networkidle')
        
        # 検索結果から該当書籍を特定
        results = await self.page.query_selector_all('[data-component-type="s-search-result"]')
        
        for result in results:
            link = await result.query_selector('h2 a')
            if link:
                href = await link.get_attribute('href')
                return f"{self.BASE_URL}{href}"
        
        return None
```

#### 4. データモデル定義
```python
# models/sales_link.py
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class SalesLink:
    site_name: str
    url: str
    price: Optional[int] = None
    availability: bool = True
    scraped_at: datetime = None
    error: Optional[str] = None
    
    def to_dict(self):
        return {
            'site_name': self.site_name,
            'url': self.url,
            'price': self.price,
            'availability': self.availability,
            'scraped_at': self.scraped_at.isoformat() if self.scraped_at else None,
            'error': self.error
        }
```

### Phase C: エラーハンドリング・最適化（1週間）

#### 5. リトライ機構
```python
# base/utils.py
import asyncio
from functools import wraps

def retry_on_error(max_attempts=3, delay=1.0, backoff=2.0):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            attempt = 0
            current_delay = delay
            
            while attempt < max_attempts:
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    attempt += 1
                    if attempt >= max_attempts:
                        raise
                    
                    await asyncio.sleep(current_delay)
                    current_delay *= backoff
                    
        return wrapper
    return decorator
```

#### 6. 並列処理実装
```python
# manager.py
class ScrapingManager:
    def __init__(self, max_concurrent: int = 3):
        self.max_concurrent = max_concurrent
        self.scrapers = {
            'amazon_kindle': AmazonKindleScraper,
            'rakuten_kobo': RakutenKoboScraper,
            'google_play': GooglePlayScraper,
            # ... 他のスクレイパー
        }
    
    async def scrape_all_sites(self, n_code: str, title: str) -> Dict[str, SalesLink]:
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        async def scrape_with_limit(site_name, scraper_class):
            async with semaphore:
                scraper = scraper_class()
                try:
                    await scraper.initialize()
                    url = await scraper.search_book(n_code, title)
                    if url:
                        info = await scraper.extract_book_info(url)
                        return SalesLink(
                            site_name=site_name,
                            url=url,
                            price=info.get('price'),
                            scraped_at=datetime.now()
                        )
                except Exception as e:
                    return SalesLink(
                        site_name=site_name,
                        url=None,
                        availability=False,
                        error=str(e),
                        scraped_at=datetime.now()
                    )
                finally:
                    await scraper.close()
        
        tasks = [
            scrape_with_limit(name, scraper)
            for name, scraper in self.scrapers.items()
        ]
        
        results = await asyncio.gather(*tasks)
        return {r.site_name: r for r in results}
```

---

## 🧪 テスト戦略

### 1. セレクタ検証ツール
```python
# scripts/validate_selectors.py
async def validate_site_selectors(site_name: str):
    """サイトのセレクタが有効か検証"""
    scraper_class = SCRAPER_MAP.get(site_name)
    if not scraper_class:
        return
    
    scraper = scraper_class()
    await scraper.initialize()
    
    # テスト書籍で検証
    test_books = [
        {'n_code': 'n1234567', 'title': 'テスト書籍1'},
        # ...
    ]
    
    for book in test_books:
        try:
            url = await scraper.search_book(book['n_code'], book['title'])
            print(f"✅ {site_name}: 検索成功 - {url}")
        except Exception as e:
            print(f"❌ {site_name}: エラー - {e}")
```

### 2. 単体サイトテスト
```bash
# 単一サイトのテスト実行
python scripts/test_single_site.py --site amazon_kindle --ncode n1234567
```

---

## 📈 実装スケジュール

### Week 1: 基盤構築
- Day 1-2: Docker環境構築、プロジェクト構造作成
- Day 3-4: BaseScraper、データモデル実装
- Day 5: エラーハンドリング基盤

### Week 2: 高安定サイト実装
- Day 1-2: Amazon Kindleアダプター
- Day 3-4: 楽天Koboアダプター
- Day 5: Google Play Booksアダプター

### Week 3: 最適化・拡張
- Day 1-2: 並列処理、パフォーマンス最適化
- Day 3-4: 中安定性サイト（4サイト）追加
- Day 5: テスト・デバッグ

### Week 4: 完成・統合準備
- Day 1-2: 低安定性サイト（4サイト）追加
- Day 3: 包括的テスト実施
- Day 4-5: WordPress統合準備、ドキュメント整備

---

## 🚀 クイックスタート

### 1. 環境セットアップ
```bash
# リポジトリクローン
git clone https://github.com/yourusername/izumi-novels-workflow.git
cd izumi-novels-workflow

# Docker環境構築
docker-compose build
docker-compose up -d
```

### 2. テスト実行
```bash
# 全サイトスクレイピングテスト
docker-compose run playwright python scripts/test_all_sites.py

# 特定サイトのみ
docker-compose run playwright python scripts/test_single_site.py --site amazon_kindle
```

### 3. 実運用
```python
from src.scraping.manager import ScrapingManager

async def main():
    manager = ScrapingManager()
    results = await manager.scrape_all_sites('n1234567', '異世界転生した件')
    
    # JSON出力
    import json
    with open('results.json', 'w', encoding='utf-8') as f:
        json.dump(
            {site: link.to_dict() for site, link in results.items()},
            f,
            ensure_ascii=False,
            indent=2
        )

asyncio.run(main())
```

---

## 📊 成功指標

### パフォーマンス目標
- 単一サイトスクレイピング: < 10秒
- 11サイト並列実行: < 30秒
- メモリ使用量: < 500MB

### 品質目標
- 成功率: > 95%（高安定サイト）
- エラー復旧率: > 80%
- セレクタ更新頻度: < 月1回

---

**作成日**: 2025-01-31  
**次回アクション**: Playwright環境構築開始
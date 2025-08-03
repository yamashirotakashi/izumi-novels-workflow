# Codebase Structure and Architecture

## Directory Organization
```
src/
├── core/                    # Core infrastructure
│   ├── selector_database.py    # SQLite selector management (605 lines - LARGE!)
│   ├── config_manager.py       # Configuration handling
│   ├── parallel_scraping_engine.py  # Concurrent scraping
│   └── flexible_scraper.py     # Adaptive scraping logic
├── scrapers/               # New scraper architecture
│   ├── base_scraper.py         # Modern base class
│   ├── amazon_scraper.py       # Amazon Kindle implementation
│   └── bookwalker_scraper.py   # BOOK☆WALKER implementation
└── scraping/               # Legacy scraper implementations
    ├── base_scraper.py         # Original base class (366 lines)
    ├── amazon_kindle_scraper.py
    ├── bookwalker_scraper.py   # Contains complex logic (427 lines)
    ├── google_sheets_client.py
    └── [10+ other site scrapers]
```

## Key Architecture Patterns
- **Inheritance-based scraping**: BaseScraper → Site-specific scrapers
- **Async/await patterns**: Modern asynchronous scraping
- **Strategy pattern**: Multiple search strategies per site
- **Template method**: Common scraping flow with site customization
# Essential Development Commands

## Testing Commands
```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=src tests/

# Run specific test file
pytest tests/test_amazon_configuration_only.py

# Run individual scraper tests
python scripts/test_amazon_scraper.py
python scripts/test_bookwalker_scraper.py
```

## Code Quality Commands
```bash
# Format code automatically
black src/ scripts/ tests/

# Check code style
flake8 src/ scripts/ tests/

# Type checking
mypy src/
```

## Verification and Validation
```bash
# Phase 1 verification (main validation script)
python phase1_verification_final.py

# Test all 11 scrapers
python scripts/test_all_scrapers.py

# Test integrated workflow
python scripts/run_integrated_test.py
```

## Development Utilities
```bash
# Install Chrome for Testing
python scripts/install_chrome_for_testing.py

# Validate core components
python scripts/validate_components.py

# Test Google Sheets connection
python scripts/test_google_sheets_connection.py
```
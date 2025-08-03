# Task Completion Checklist

## Before Committing Changes
1. **Code Quality Checks**
   ```bash
   black src/ scripts/ tests/  # Format code
   flake8 src/ scripts/ tests/  # Style check
   mypy src/                   # Type check
   ```

2. **Testing Requirements**
   ```bash
   pytest --cov=src tests/     # Run tests with coverage
   python phase1_verification_final.py  # Core verification
   ```

3. **Scraper Validation**
   ```bash
   python scripts/test_all_scrapers.py  # Test all 11 scrapers
   python scripts/validate_components.py  # Component validation
   ```

## Integration Testing
- Test Google Sheets connectivity
- Verify Chrome/ChromeDriver compatibility
- Validate selector database integrity
- Check async/await patterns work correctly

## Documentation Updates
- Update CLAUDE.md if architectural changes made
- Update requirements.txt if dependencies changed
- Document any new scraper sites or configuration changes
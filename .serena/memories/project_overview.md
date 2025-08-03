# Izumi Novels Workflow - Project Overview

## Purpose
Japanese novel sales link automation system that:
- Scrapes 11 major e-book platforms (Amazon Kindle, BOOK☆WALKER, Rakuten Kobo, etc.)
- Automatically collects book availability and pricing information
- Integrates with Google Sheets for data management
- Supports WordPress automatic posting

## Key Business Value
- Automates manual checking of 11 sites for novel availability
- Maintains up-to-date sales link information for authors/publishers
- Reduces time spent on repetitive data collection tasks

## Technical Architecture
- **Core Language**: Python 3.x with async/await patterns
- **Web Scraping**: Playwright (primary) + Selenium (fallback)
- **Data Models**: Pydantic for structured data validation
- **Integration**: Google Sheets API for data persistence
- **Configuration**: SQLite database for selector management
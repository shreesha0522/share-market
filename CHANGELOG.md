# Changelog

All notable changes to this project are documented here.

## [Unreleased]
- Real survey data pending (currently using synthetic placeholder data)
- Literature review, background/business case, and discussion sections pending

## 2026-08-15
- Fixed division-by-zero bug in sector risk-adjusted return calculation
- Added test coverage for Value at Risk, correlation matrix, and edge cases
- Added sector-vs-survey linkage: connects real market volatility to survey respondents' perceived difficulty
- Added Value at Risk (95%), correlation matrix, best/worst single-day moves, and risk-adjusted return metrics
- Added normalized multi-company comparison chart
- Added metric glossary and hover tooltips for usability
- Refactored backend into analysis modules (market.py, survey.py) for maintainability
- Split frontend main.js into ES modules (utils.js, market.js, survey.js)
- Added GitHub Actions CI workflow to run tests on every push
- Added data quality validation script, data dictionary, OpenAPI spec
- Added type hints throughout backend
- Added python-dotenv configuration support
- Added SECURITY.md, CODEOWNERS, issue templates
- Added PDF export, auto-generated key findings, and branding polish
- Added Risk Consideration and Research Ethics section
- Removed unused Streamlit prototype and one-off scripts

## 2026-08-13
- Added date format validation to the market data API endpoint
- Added ARIA labels to charts and decorative elements for accessibility
- Added `.gitattributes` for consistent line endings across platforms
- Pinned backend dependency versions for reproducible installs
- Added MIT license
- Added favicon
- Added error handling, loading states, and mobile responsiveness to frontend
- Added Flask backend API for market and survey analysis
- Added HTML/CSS/JS frontend dashboard consuming the Flask API
- Updated README with setup instructions for Flask backend + frontend

## Earlier
- Built initial data pipeline: NEPSE historical price data (10 companies)
- Built synthetic survey data generator for pipeline testing
- Built standalone analysis script (`scripts/analysis.py`) producing charts and CSV outputs
- Built original Streamlit dashboard prototype

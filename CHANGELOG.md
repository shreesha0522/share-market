# Changelog

All notable changes to this project are documented here.

## [Unreleased]
- Real survey data pending (currently using synthetic placeholder data)
- Literature review, background/business case, and discussion sections pending

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

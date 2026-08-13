# Contributing

This is an academic thesis project, developed individually. This document
records the working conventions used throughout development.

## Project structure
- `backend/` — Flask API (Python)
- `frontend/` — static HTML/CSS/JS dashboard
- `data/` — market and survey data
- `scripts/` — standalone analysis scripts used before the web app existed

## Setup
See `README.md` for full setup instructions (running the backend and frontend
locally).

## Commit conventions
Commits are scoped to a single, complete change (a feature, a fix, or a
documentation update) and use a short, descriptive present-tense message,
e.g. `Add date format validation to market data API endpoint`.

## Code style
- Python: standard PEP 8 conventions, functions documented with docstrings
  where behaviour isn't obvious from the name.
- JavaScript: vanilla JS, no build step; functions grouped by concern
  (loading/error helpers, chart rendering, data fetching).
- CSS: custom properties (CSS variables) used for all colors and fonts to
  keep the design system centralized in `:root`.

## Data integrity
Any survey data used must be clearly labeled as synthetic or real
(`is_synthetic` flag in the API response). Synthetic data must never be
presented as real primary research findings.

# New Investor Risk Monitor — NEPSE

A thesis support tool for: *"Analysis and Identification of Challenges Faced by
New Investors in the Share Market Using Survey-Based and Market Data Analysis."*

Full-stack web app: a **Flask (Python) backend** serving analysis as a JSON API,
and a **static HTML/CSS/JS frontend** (charted with Chart.js) that consumes it.

---

## Project structure
investor-market-analysis/
├── backend/
│ ├── app.py # Flask API — market + survey analysis
│ └── requirements.txt
├── frontend/
│ ├── index.html
│ ├── css/style.css
│ └── js/main.js
├── data/
│ ├── market/*.csv # Real NEPSE historical price data (10 companies)
│ └── survey/survey_synthetic.csv # SYNTHETIC placeholder — see note below
├── scripts/
│ ├── analysis.py # Original standalone analysis script (charts, CSVs)
│ └── generate_synthetic_survey.py
└── outputs/ # Charts + CSV exports from scripts/analysis.py

---

## Running it (two servers, two terminal tabs)

### 1. Start the backend
```bash
cd backend
pip install -r requirements.txt
python app.py
```
Runs on `http://127.0.0.1:5000`. Leave this terminal open — it must keep running.

### 2. Start the frontend (separate terminal tab)
```bash
cd frontend
python3 -m http.server 8000
```
Runs on `http://127.0.0.1:8000`. Leave this terminal open too.

**Important:** don't open `index.html` directly via double-click / `file://` —
Safari (and some other browsers) block API requests from `file://` pages.
Always access it through `http://127.0.0.1:8000` in the address bar.

### 3. Open the dashboard
Go to **http://127.0.0.1:8000** in your browser.

---

## API endpoints (backend/app.py)

| Endpoint | Description |
|---|---|
| `GET /api/tickers` | List of all NEPSE tickers + sectors |
| `GET /api/market/<ticker>?start=&end=` | Time series: price, volatility, drawdown, moving averages, volume spikes |
| `GET /api/market/summary` | 5-year company + sector level metrics |
| `GET /api/survey/summary` | Ranked challenges, by-experience, by-age, profitability, confidence |
| `GET /api/survey/stats` | Correlation + regression analysis |
| `GET /api/health` | Health check |

---

## ⚠️ Survey data status

`data/survey/survey_synthetic.csv` is **synthetic placeholder data**, generated
by `scripts/generate_synthetic_survey.py` to build and test the analysis
pipeline before real responses arrive. The frontend flags this automatically
(`is_synthetic: true` in the API response triggers a warning banner on the
Survey Insights tab).

**Before this data can be presented as real primary research findings**, it
must be replaced with actual respondent data collected under institutional
ethics approval (see the "Risk Research Ethics Approval" form for this project).

---

## Running tests

The backend has unit tests covering the core analysis functions (sector
mapping, metric computation, aggregation logic):

```bash
cd backend
python3 -m pytest tests/ -v
```

## Tech stack

- **Backend:** Flask, pandas, numpy, scipy, statsmodels
- **Frontend:** vanilla HTML/CSS/JS, Chart.js (via CDN)
- **Data:** real NEPSE historical trading data (10 companies, 5 sectors);
  synthetic survey data pending real collection

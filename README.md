# New Investor Risk Monitor — NEPSE

A thesis support tool for: *"Analysis and Identification of Challenges Faced by
New Investors in the Share Market Using Survey-Based and Market Data Analysis."*

Full-stack web app: a **Flask (Python) backend** serving risk analytics and
machine learning models as a JSON API, and a **static HTML/CSS/JS frontend**
(charted with Chart.js) that consumes it.

---

## Project structure
investor-market-analysis/
├── backend/
│ ├── app.py # Flask routes only
│ ├── analysis/
│ │ ├── market.py # market data loading + risk metrics
│ │ ├── survey.py # survey analysis + OLS statistics
│ │ └── ml.py # Random Forest regression/classification + live prediction
│ ├── tests/
│ │ ├── test_app.py # pytest suite for market/survey logic
│ │ └── test_ml.py # pytest suite for the ML models
│ └── requirements.txt
├── frontend/
│ ├── index.html
│ ├── css/style.css
│ └── js/
│ ├── main.js # wires everything together
│ ├── utils.js # shared helpers (fetch errors, loading states)
│ ├── market.js # market tab logic + charts
│ ├── survey.js # survey tab logic + charts
│ ├── lessons.js # auto-generated investor lessons
│ ├── readiness.js # risk tolerance vs. sector volatility check
│ ├── ml.js # ML Predictions tab + live prediction form
│ └── methodology.js # model comparison & limitations (About tab)
├── data/
│ ├── market/*.csv # real NEPSE historical price data (10 companies)
│ ├── survey/
│ │ ├── survey_real.csv # real respondent data (used when present)
│ │ ├── survey_synthetic.csv # synthetic fallback — see note below
│ │ └── survey_raw_export.csv # raw Google Forms export (pre-processing)
│ └── ...
├── scripts/
│ ├── analysis.py # generates outputs/*.csv and outputs/charts/*
│ ├── generate_synthetic_survey.py
│ ├── convert_survey_responses.py # raw form export → survey_real.csv
│ ├── validate_data.py # data quality checks
│ └── plot_volatility_vs_difficulty_real.py # standalone thesis figure script
├── outputs/
│ ├── company_metrics.csv
│ ├── sector_metrics.csv
│ └── charts/ # generated figures for the written thesis
├── docs/
│ ├── openapi.yaml # API specification
│ └── data_dictionary.md # CSV schema reference
├── .github/
│ ├── workflows/tests.yml # CI: runs pytest on every push
│ └── ISSUE_TEMPLATE/
├── Makefile
└── .env.example

---

## Running it (two servers, two terminal tabs)

### Quick start with Make
```bash
# Terminal 1
make backend

# Terminal 2
make frontend
```

### Or manually

**1. Start the backend**
```bash
cd backend
pip install -r requirements.txt
python app.py
```
Runs on `http://127.0.0.1:5000`. Leave this terminal open.

**2. Start the frontend (separate terminal tab)**
```bash
cd frontend
python3 -m http.server 8000
```
Runs on `http://127.0.0.1:8000`. Leave this terminal open too.

**Important:** don't open `index.html` directly via double-click / `file://` —
browsers block ES module imports and API requests from `file://` pages.
Always access it through `http://127.0.0.1:8000` in the address bar.

### 3. Open the dashboard
Go to **http://127.0.0.1:8000** in your browser.

Configuration (port, debug mode) can optionally be set via a `.env` file —
see `.env.example`.

---

## API endpoints

Full specification in [`docs/openapi.yaml`](docs/openapi.yaml).

| Endpoint | Description |
|---|---|
| `GET /api/tickers` | List of all NEPSE tickers + sectors |
| `GET /api/market/<ticker>?start=&end=` | Time series: price, volatility, drawdown, moving averages, volume spikes, VaR, extreme days |
| `GET /api/market/summary` | 5-year company + sector level metrics, including risk-adjusted return |
| `GET /api/market/correlation` | Correlation matrix of daily returns across all companies |
| `GET /api/survey/summary` | Ranked challenges, by-experience, by-age, profitability, confidence |
| `GET /api/survey/stats` | OLS regression + Pearson correlation analysis |
| `GET /api/survey/linkage` | Links each sector's real volatility to survey respondents' perceived difficulty |
| `GET /api/survey/ml` | Cross-validated Random Forest regression (challenge score) + classification (high/low challenge), with a linear regression baseline for comparison |
| `GET /api/survey/ml/predict?experience=&portfolio=&trade_freq=&sector=` | Live prediction: trains on the full survey sample and returns a predicted challenge score + classification for one investor profile |
| `GET /api/health` | Health check |

---

## Dashboard features

- **Market Data tab** — volatility, drawdown, moving averages, volume spikes,
  Value at Risk, best/worst single-day moves, cross-company correlation matrix,
  normalized multi-company comparison, risk-adjusted return
- **Survey Insights tab** — ranked investor-reported challenges, breakdowns by
  experience/age, statistical findings, sector risk vs. perceived difficulty
- **ML Predictions tab** — Random Forest regression and classification results
  (cross-validated, with feature importance and a confusion matrix), plus an
  interactive form to predict a challenge score for a given investor profile
- **About tab** — study overview, metric glossary, ethics and risk
  considerations, and a **Model Comparison & Limitations** section that
  compares OLS vs. machine learning honestly, including a below-chance-baseline
  callout where applicable
- PDF export of key findings

---

## Machine learning approach

`analysis/ml.py` complements the classical OLS regression in `survey.py` with
two supervised models trained on the same survey data:

1. **Random Forest regressor** — predicts a respondent's overall challenge
   score from their investing traits (experience, portfolio size, trade
   frequency, sector volatility exposure), benchmarked against a plain linear
   regression baseline.
2. **Random Forest classifier** — predicts whether a respondent is
   "high challenge" (above the sample median) or "low challenge."

Both are evaluated with **K-fold cross-validation** (fold count scales with
sample size, capped at 5) rather than a single train/test split — with a
small survey sample, one split can swing wildly depending on which rows land
in the test set. Metrics are reported as mean ± standard deviation across
folds, which is what should be cited in the written thesis rather than any
single-split number.

Respondents who report investing only in sectors outside the tracked NEPSE
market dataset (e.g. "Manufacturing", "Hotels") have their sector-volatility
exposure **imputed** with the overall tracked-sector average rather than being
dropped — this is a stated, disclosed assumption (`n_imputed_sector_exposure`
in every relevant API response), not a hidden one.

A third function, `predict_for_investor()`, powers the live prediction form:
it trains on the **full** sample (no cross-validation split, since a one-off
prediction should use all available data) and returns a predicted score plus
classification for a given investor profile.

---

## ⚠️ Survey data status

The backend prefers `data/survey/survey_real.csv` when present, falling back
to `data/survey/survey_synthetic.csv` otherwise (`survey.SURVEY_PATH`,
resolved automatically). **Real respondent data is now in use** — the API
reports this via `is_synthetic: false` in relevant responses, and the frontend
only shows the synthetic-data warning banner when the fallback file is active.

The raw Google Forms export lives at `data/survey/survey_raw_export.csv` and
is converted into `survey_real.csv` by `scripts/convert_survey_responses.py`.

With a real sample this small (currently 18 respondents), treat all
statistical and ML findings as directional/exploratory rather than
statistically conclusive — this is stated explicitly throughout the dashboard
(caveats on the Survey Insights, ML Predictions, and About tabs) rather than
hidden.

---

## Running tests

```bash
make test
# or:
cd backend && python3 -m pytest tests/ -v
```

Covers both the classical analysis logic (`test_app.py`) and the ML models
(`test_ml.py`) — cross-validation shape, sector-exposure imputation, error
handling for too-small samples, and the live prediction endpoint.

## Validating data quality

```bash
make validate-data
# or:
python3 scripts/validate_data.py
```

Checks the market and survey CSVs for missing values, duplicate dates, and
out-of-range values.

## Regenerating thesis figures

```bash
python3 scripts/analysis.py                              # regenerates outputs/*.csv and outputs/charts/*
python3 scripts/plot_volatility_vs_difficulty_real.py     # regenerates the volatility-vs-difficulty figure
```

Figures read live from `outputs/sector_metrics.csv` rather than hardcoded
values, so they stay in sync automatically if the underlying market data
changes — run `scripts/analysis.py` first if that file is stale or missing.

---

## Tech stack

- **Backend:** Flask, pandas, numpy, scipy, statsmodels, scikit-learn, python-dotenv
- **Frontend:** vanilla HTML/CSS/JavaScript (ES modules), Chart.js (via CDN)
- **Testing:** pytest, GitHub Actions CI
- **Data:** real NEPSE historical trading data (10 companies, 5 sectors);
  real survey data (18 respondents) with a synthetic fallback for development

## Further documentation

- [`CONTRIBUTING.md`](CONTRIBUTING.md) — development conventions
- [`SECURITY.md`](SECURITY.md) — project scope and known limitations
- [`CHANGELOG.md`](CHANGELOG.md) — full development history
- [`docs/data_dictionary.md`](docs/data_dictionary.md) — CSV schema reference

# New Investor Risk Monitor — NEPSE

A thesis support tool for: *"Analysis and Identification of Challenges Faced by
New Investors in the Share Market Using Survey-Based and Market Data Analysis."*

Full-stack web app: a **Flask (Python) backend** serving risk analytics as a
JSON API, and a **static HTML/CSS/JS frontend** (charted with Chart.js) that
consumes it.

---

## Project structure
investor-market-analysis/
├── backend/
│ ├── app.py # Flask routes only
│ ├── analysis/
│ │ ├── market.py # market data loading + risk metrics
│ │ └── survey.py # survey analysis + statistics
│ ├── tests/
│ │ └── test_app.py # pytest suite
│ └── requirements.txt
├── frontend/
│ ├── index.html
│ ├── css/style.css
│ └── js/
│ ├── main.js # wires everything together
│ ├── utils.js # shared helpers (fetch errors, loading states)
│ ├── market.js # market tab logic + charts
│ └── survey.js # survey tab logic + charts
├── data/
│ ├── market/*.csv # real NEPSE historical price data (10 companies)
│ └── survey/survey_synthetic.csv # SYNTHETIC placeholder — see note below
├── scripts/
│ ├── generate_synthetic_survey.py
│ └── validate_data.py # data quality checks
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
browsers block API requests from `file://` pages. Always access it through
`http://127.0.0.1:8000` in the address bar.

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
| `GET /api/survey/stats` | Correlation + regression analysis |
| `GET /api/survey/linkage` | Links each sector's real volatility to survey respondents' perceived difficulty |
| `GET /api/health` | Health check |

---

## Dashboard features

- **Market Data tab** — volatility, drawdown, moving averages, volume spikes,
  Value at Risk, best/worst single-day moves, cross-company correlation matrix,
  normalized multi-company comparison, risk-adjusted return
- **Survey Insights tab** — ranked investor-reported challenges, breakdowns by
  experience/age, statistical findings, sector risk vs. perceived difficulty
- **About tab** — study overview, metric glossary, ethics and risk
  considerations
- PDF export of key findings

---

## ⚠️ Survey data status

`data/survey/survey_synthetic.csv` is **synthetic placeholder data**, generated
by `scripts/generate_synthetic_survey.py` to build and test the analysis
pipeline before real responses arrive. The frontend flags this automatically
(`is_synthetic: true` in relevant API responses triggers a warning banner).

**Before this data can be presented as real primary research findings**, it
must be replaced with actual respondent data collected under institutional
ethics approval.

---

## Running tests

```bash
make test
# or:
cd backend && python3 -m pytest tests/ -v
```

## Validating data quality

```bash
make validate-data
# or:
python3 scripts/validate_data.py
```

Checks the market and survey CSVs for missing values, duplicate dates, and
out-of-range values.

---

## Tech stack

- **Backend:** Flask, pandas, numpy, scipy, statsmodels, python-dotenv
- **Frontend:** vanilla HTML/CSS/JavaScript (ES modules), Chart.js (via CDN)
- **Testing:** pytest, GitHub Actions CI
- **Data:** real NEPSE historical trading data (10 companies, 5 sectors);
  synthetic survey data pending real collection

## Further documentation

- [`CONTRIBUTING.md`](CONTRIBUTING.md) — development conventions
- [`SECURITY.md`](SECURITY.md) — project scope and known limitations
- [`CHANGELOG.md`](CHANGELOG.md) — full development history
- [`docs/data_dictionary.md`](docs/data_dictionary.md) — CSV schema reference

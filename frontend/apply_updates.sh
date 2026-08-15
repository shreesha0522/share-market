#!/usr/bin/env bash
set -e
echo "Updating index.html..."
cat > index.html << 'INDEXEOF'
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>New Investor Risk Monitor — NEPSE</title>
<meta name="description" content="A Bachelor's thesis dashboard analysing NEPSE market risk data alongside survey-based research into the challenges new investors face in the Nepali share market.">
<meta name="author" content="Your Name — Your University">
<meta property="og:title" content="New Investor Risk Monitor — NEPSE">
<meta property="og:description" content="Market data & survey-based analysis of challenges faced by new investors in the Nepali share market.">
<meta property="og:type" content="website">
<meta name="theme-color" content="#0F1419">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="css/style.css">
<link rel="icon" type="image/svg+xml" href="favicon.svg">
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
</head>
<body>

  <div class="ticker-strip">
    <div class="ticker-track" id="tickerTrack">
      <span class="ticker-item">Loading NEPSE feed…</span>
    </div>
  </div>

  <header class="site-header">
    <div class="brand">
      <span class="brand-mark" aria-hidden="true">◆</span>
      <div class="brand-text">
        <div class="brand-title">New Investor Risk Monitor</div>
        <div class="brand-sub">NEPSE market behaviour &amp; investor-reported challenges</div>
        <div class="brand-byline">Bachelor's Thesis · <span data-fill="author">Your Name</span> · <span data-fill="university">Your University</span> · 2026</div>
      </div>
    </div>
    <nav class="tabs" id="mainTabs">
      <button class="tab-btn active" data-tab="market">Market Data</button>
      <button class="tab-btn" data-tab="survey">Survey Insights</button>
      <button class="tab-btn" data-tab="about">About This Study</button>
      <button class="tab-btn print-btn" id="printBtn" type="button" title="Print or save this page as PDF">Export PDF</button>
    </nav>
  </header>

  <main>

    <section id="tab-market" class="tab-panel active">

      <div class="layout">
        <aside class="controls-panel">
          <h2 class="panel-title">Controls</h2>

          <label class="field-label" for="tickerSelect">Company</label>
          <select id="tickerSelect" class="field-input"></select>

          <label class="field-label" for="startDate">Start date</label>
          <input type="date" id="startDate" class="field-input" value="2021-01-01">

          <label class="field-label" for="endDate">End date</label>
          <input type="date" id="endDate" class="field-input" value="2026-07-01">

          <button id="loadBtn" class="primary-btn">Update view</button>

          <div class="panel-note">
            Volatility, drawdown, moving averages and volume-spike detection
            are computed live from real NEPSE historical price data — the
            kind of risk signals new investors often can't read.
          </div>
        </aside>

        <div class="content-col">

          <div class="status-banner error-banner" id="marketError" hidden></div>
          <div class="loading-indicator" id="marketLoading" hidden>
            <span class="spinner"></span> Loading market data…
          </div>

          <div class="summary-cards" id="summaryCards">
            <!-- populated by JS -->
          </div>

          <div class="chart-tabs" id="chartTabs">
            <button class="chart-tab-btn active" data-chart="volatility">Volatility</button>
            <button class="chart-tab-btn" data-chart="drawdown">Drawdown</button>
            <button class="chart-tab-btn" data-chart="trend">Trend (MA)</button>
            <button class="chart-tab-btn" data-chart="volume">Volume Spikes</button>
          </div>

          <div class="chart-panel">
            <p class="chart-caption" id="chartCaption"></p>
            <canvas id="mainChart" height="110" role="img" aria-label="Selected market indicator chart for the chosen company and date range"></canvas>
          </div>

        </div>
      </div>

      <div class="section-block">
        <h2 class="section-title">Best &amp; Worst Single-Day Moves</h2>
        <p class="section-sub">
          The single most extreme trading days for the selected company in the chosen date range —
          real examples of the kind of overnight swing a new investor could face without warning.
        </p>
        <div class="two-col">
          <div class="table-scroll">
            <table class="data-table" id="bestDaysTable">
              <thead><tr><th colspan="3" style="color: var(--gain-green);">Best Days</th></tr>
              <tr><th>Date</th><th>Return</th><th>Close</th></tr></thead>
              <tbody></tbody>
            </table>
          </div>
          <div class="table-scroll">
            <table class="data-table" id="worstDaysTable">
              <thead><tr><th colspan="3" style="color: var(--risk-red);">Worst Days</th></tr>
              <tr><th>Date</th><th>Return</th><th>Close</th></tr></thead>
              <tbody></tbody>
            </table>
          </div>
        </div>
      </div>

      <div class="section-block">
        <h2 class="section-title">5-Year Company &amp; Sector Overview</h2>
        <div class="table-scroll">
          <table class="data-table" id="companyTable">
            <thead>
              <tr>
                <th>Ticker</th><th>Sector</th><th>Start Price</th><th>Latest Price</th>
                <th>Total Return</th><th>Volatility</th><th title="Total return divided by volatility — how much reward you got per unit of risk taken, not just raw price movement." class="metric-hint">Risk-Adj. Return</th><th>Avg Daily Volume</th>
              </tr>
            </thead>
            <tbody></tbody>
          </table>
        </div>
      </div>

      <div class="section-block">
        <h2 class="section-title">Compare Companies (Normalized)</h2>
        <p class="section-sub">
          Raw prices can't be compared directly across companies with very different share prices.
          This rebases each selected company to 100 at the start of the date range, so you can see
          which one actually performed better or worse — not just which has a bigger number.
        </p>
        <div class="compare-controls" id="compareControls"></div>
        <button id="compareBtn" class="primary-btn" style="width: auto; margin-top: 0.75rem;">Compare selected</button>
        <div class="chart-panel" style="margin-top: 1rem;">
          <canvas id="compareChart" height="110"></canvas>
        </div>
      </div>

      <div class="section-block">
        <h2 class="section-title">Cross-Company Correlation</h2>
        <p class="section-sub">
          How closely each company's daily returns move together. Values near 1.0 mean holding
          both offers little real diversification — a mistake new investors commonly make when
          they assume more stocks automatically means less risk.
        </p>
        <div class="table-scroll">
          <table class="data-table" id="correlationTable"></table>
        </div>
      </div>

    </section>

    <section id="tab-survey" class="tab-panel">

      <div class="synthetic-banner" id="syntheticBanner" hidden>
        ⚠ This survey data is <strong>synthetic placeholder data</strong>, generated to test the
        analysis pipeline. It should be replaced with real respondent data collected under
        institutional ethics approval before being presented as primary research findings.
      </div>

      <div class="status-banner error-banner" id="surveyError" hidden></div>
      <div class="loading-indicator" id="surveyLoading" hidden>
        <span class="spinner"></span> Loading survey data…
      </div>

      <div class="section-block">
        <h2 class="section-title">Investor-Reported Challenges (Ranked)</h2>
        <p class="section-sub" id="respondentCount"></p>
        <div class="chart-panel">
          <canvas id="challengeChart" height="100" role="img" aria-label="Bar chart ranking investor-reported challenges by average score"></canvas>
        </div>
      </div>

      <div class="two-col">
        <div class="section-block">
          <h2 class="section-title">Challenge Score by Experience</h2>
          <div class="chart-panel">
            <canvas id="experienceChart" height="140" role="img" aria-label="Bar chart showing average challenge score by years of investing experience"></canvas>
          </div>
        </div>
        <div class="section-block">
          <h2 class="section-title">Reported Profitability</h2>
          <div class="chart-panel">
            <canvas id="profitChart" height="140" role="img" aria-label="Doughnut chart showing reported profitability outcomes among survey respondents"></canvas>
          </div>
        </div>
      </div>

      <div class="section-block">
        <h2 class="section-title">Challenge Score by Age Group</h2>
        <p class="section-sub">Average overall challenge score reported by respondents in each age bracket.</p>
        <div class="chart-panel">
          <canvas id="ageChart" height="100" role="img" aria-label="Bar chart showing average challenge score by age group"></canvas>
        </div>
      </div>

      <div class="section-block">
        <h2 class="section-title">Real Risk vs. Perceived Difficulty</h2>
        <p class="section-sub">
          Each sector's actual market volatility, compared to how difficult survey respondents who
          invest in that sector rated it. If perceived difficulty doesn't track real volatility,
          it suggests investors aren't accurately distinguishing higher-risk sectors from lower-risk ones.
        </p>
        <div class="chart-panel">
          <canvas id="linkageChart" height="120"></canvas>
        </div>
      </div>

      <div class="section-block">
        <h2 class="section-title">Statistical Findings</h2>
        <div class="stats-grid" id="statsGrid">
          <!-- populated by JS -->
        </div>
      </div>

      <div class="section-block">
        <h2 class="section-title">Key Findings</h2>
        <p class="section-sub">Plain-language summary of the statistical results above, generated from the current dataset.</p>
        <div class="findings-card" id="keyFindings">
          <!-- populated by JS -->
        </div>
      </div>

    </section>

    <section id="tab-about" class="tab-panel">
      <div class="section-block about-block">
        <h2 class="section-title">About This Study</h2>
        <p>
          This dashboard supports a Bachelor's thesis titled
          <em>"Analysis and Identification of Challenges Faced by New Investors in the
          Share Market Using Survey-Based and Market Data Analysis."</em>
        </p>
        <p>
          The <strong>market data</strong> side draws on real historical trading data for ten
          NEPSE-listed companies across banking, hydropower, insurance, telecom and investment
          sectors, and computes volatility, drawdown, trend, and volume-spike indicators — signals
          that are difficult for inexperienced investors to interpret in real time.
        </p>
        <p>
          The <strong>survey</strong> side is designed to capture self-reported challenges from
          new investors directly, covering financial literacy, platform usability, emotional
          decision-making, regulatory understanding, and access to reliable information.
        </p>
        <p>
          Backend: Flask (Python), serving computed statistics as a JSON API.<br>
          Frontend: static HTML/CSS/JavaScript, charted with Chart.js.
        </p>

        <h2 class="section-title" style="margin-top: 2rem;">Glossary of Metrics</h2>
        <dl class="glossary">
          <dt>Volatility (30-day)</dt>
          <dd>How much a stock's daily price swings over the past 30 trading days. Higher volatility means it's harder to tell whether a price move is meaningful or just noise.</dd>

          <dt>Drawdown</dt>
          <dd>How far the price has fallen from its most recent peak, shown as a percentage. This is the number that actually triggers panic-selling — a 50% drawdown means the price is half of its recent high.</dd>

          <dt>Value at Risk (95%)</dt>
          <dd>The daily loss threshold that historically was exceeded only 5% of the time. A VaR of -2% means that on a bad day (1 in 20), you could realistically lose more than 2% in a single session.</dd>

          <dt>Volume Spike</dt>
          <dd>A day where trading volume was more than double its 20-day average — often a sign of crowd behaviour: FOMO buying or panic selling, rather than considered decision-making.</dd>

          <dt>Risk-Adjusted Return</dt>
          <dd>Total return divided by volatility. This answers "how much reward did you get for the risk you took," not just "how much did the price move." A stock can have a higher raw return but a worse risk-adjusted return if it was far more volatile getting there.</dd>

          <dt>Correlation</dt>
          <dd>How closely two companies' daily returns move together, from -1 (move in opposite directions) to +1 (move identically). Values near +1 mean holding both offers little real diversification, even if they're different companies.</dd>

          <dt>Moving Average (MA)</dt>
          <dd>The average closing price over the last 20 or 50 days. Comparing price to its moving average helps separate a genuine trend from short-term noise.</dd>
        </dl>
        <h2 class="section-title" style="margin-top: 2rem;">Risk Consideration &amp; Research Ethics</h2>
        <p class="section-sub">How risks in this research — to participants, to data validity, and to the findings themselves — were identified and mitigated.</p>

        <div class="table-scroll" style="margin-bottom: 1.5rem;">
          <table class="data-table risk-table">
            <thead>
              <tr><th>Risk</th><th>Level</th><th>Mitigation</th></tr>
            </thead>
            <tbody>
              <tr>
                <td>Survey responses biased or inaccurate</td>
                <td><span class="risk-badge med">Medium</span></td>
                <td>Anonymous, voluntary participation; neutral question wording; Likert-scale items reviewed before distribution.</td>
              </tr>
              <tr>
                <td>Participant data privacy</td>
                <td><span class="risk-badge high">High</span></td>
                <td>No names or contact details collected; responses stored and analysed in aggregate only; formal ethics approval obtained prior to distribution.</td>
              </tr>
              <tr>
                <td>Small or unrepresentative sample</td>
                <td><span class="risk-badge med">Medium</span></td>
                <td>Distributed across multiple investor communities; minimum response threshold set before drawing conclusions; limitation stated explicitly in findings.</td>
              </tr>
              <tr>
                <td>Market data incomplete or outdated</td>
                <td><span class="risk-badge med">Medium</span></td>
                <td>Sourced from a consistent historical archive, cross-checked against trading day counts per company.</td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="ethics-card">
          <h3 class="ethics-title">Ethics &amp; Consent</h3>
          <ul class="ethics-list">
            <li>This study operates under a formal Ethics Approval record submitted prior to data collection.</li>
            <li>Participation in the survey is voluntary and anonymous; no personally identifying information is collected.</li>
            <li>Participants are informed the data is used only for academic analysis, stated on the survey's opening screen.</li>
            <li>The research team commits to suspending data collection and re-seeking approval if the project scope changes.</li>
          </ul>
          <div class="approval-tag"><span class="dot"></span> Ethics approval on file</div>
        </div>

      </div>
    </section>

  </main>

  <footer class="site-footer">
    Built for academic research purposes. Data pipeline: Flask API + NEPSE historical data.
  </footer>

<script type="module" src="js/main.js"></script>
</body>
</html>
INDEXEOF

mkdir -p css js
echo "Updating css/style.css..."
cat > css/style.css << 'CSSEOF'
:root {
  --bg: #0F1419;
  --bg-panel: #161D26;
  --bg-panel-2: #1C242F;
  --border: #2A3441;
  --text: #E8EAED;
  --text-muted: #8B96A3;
  --accent: #D4A24E;
  --accent-soft: rgba(212, 162, 78, 0.14);
  --risk-red: #C4554D;
  --gain-green: #4E9B6E;
  --purple: #8A7CC7;

  --font-display: "IBM Plex Sans", sans-serif;
  --font-body: "IBM Plex Sans", sans-serif;
  --font-mono: "IBM Plex Mono", monospace;
}

* { box-sizing: border-box; }

html, body {
  margin: 0;
  padding: 0;
  background: var(--bg);
  color: var(--text);
  font-family: var(--font-body);
  -webkit-font-smoothing: antialiased;
}

.ticker-strip {
  background: var(--accent);
  color: #14100A;
  overflow: hidden;
  white-space: nowrap;
  font-family: var(--font-mono);
  font-size: 0.78rem;
  font-weight: 500;
  letter-spacing: 0.02em;
}

.ticker-track {
  display: inline-block;
  padding: 6px 0;
  animation: scroll-ticker 40s linear infinite;
}

.ticker-item {
  display: inline-block;
  padding: 0 1.5rem;
}

@keyframes scroll-ticker {
  0%   { transform: translateX(0); }
  100% { transform: translateX(-50%); }
}

@media (prefers-reduced-motion: reduce) {
  .ticker-track { animation: none; }
}

.site-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 1rem;
  padding: 1.1rem 2rem;
  border-bottom: 1px solid var(--border);
}

.brand { display: flex; align-items: center; gap: 0.75rem; }
.brand-mark { color: var(--accent); font-size: 1.5rem; line-height: 1; }
.brand-title {
  font-family: var(--font-display);
  font-weight: 700;
  font-size: 1.15rem;
  letter-spacing: -0.01em;
}
.brand-sub { color: var(--text-muted); font-size: 0.82rem; margin-top: 2px; }
.brand-byline {
  color: var(--text-muted);
  font-size: 0.72rem;
  margin-top: 4px;
  font-family: var(--font-mono);
  letter-spacing: 0.01em;
  opacity: 0.85;
}

.tabs { display: flex; gap: 0.25rem; }
.tab-btn {
  background: transparent;
  border: 1px solid transparent;
  color: var(--text-muted);
  font-family: var(--font-body);
  font-weight: 500;
  font-size: 0.88rem;
  padding: 0.5rem 0.9rem;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.15s ease;
}
.tab-btn:hover { color: var(--text); background: var(--bg-panel); }
.tab-btn.active {
  color: var(--accent);
  background: var(--accent-soft);
  border-color: rgba(212, 162, 78, 0.3);
}

.print-btn {
  margin-left: 0.5rem;
  border-color: var(--border) !important;
  color: var(--text-muted) !important;
  background: transparent !important;
}
.print-btn:hover {
  color: var(--accent) !important;
  border-color: var(--accent) !important;
  background: var(--accent-soft) !important;
}

main { padding: 1.75rem 2rem 3rem; max-width: 1280px; margin: 0 auto; }

.tab-panel { display: none; }
.tab-panel.active { display: block; }

.layout {
  display: grid;
  grid-template-columns: 250px 1fr;
  gap: 1.5rem;
}

@media (max-width: 860px) {
  .layout { grid-template-columns: 1fr; }
}

.controls-panel {
  background: var(--bg-panel);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 1.25rem;
  align-self: start;
  position: sticky;
  top: 1.5rem;
}

.panel-title {
  font-family: var(--font-display);
  font-size: 0.78rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--text-muted);
  margin: 0 0 1rem;
}

.field-label {
  display: block;
  font-size: 0.8rem;
  color: var(--text-muted);
  margin: 0.9rem 0 0.35rem;
}
.field-label:first-of-type { margin-top: 0; }

.field-input {
  width: 100%;
  background: var(--bg-panel-2);
  border: 1px solid var(--border);
  color: var(--text);
  font-family: var(--font-mono);
  font-size: 0.85rem;
  padding: 0.55rem 0.65rem;
  border-radius: 6px;
}
.field-input:focus { outline: 2px solid var(--accent); outline-offset: 1px; }

.primary-btn {
  width: 100%;
  margin-top: 1.1rem;
  background: var(--accent);
  color: #14100A;
  border: none;
  font-family: var(--font-body);
  font-weight: 600;
  font-size: 0.87rem;
  padding: 0.65rem;
  border-radius: 6px;
  cursor: pointer;
  transition: filter 0.15s ease;
}
.primary-btn:hover { filter: brightness(1.08); }
.primary-btn:focus-visible { outline: 2px solid var(--text); outline-offset: 2px; }

.panel-note {
  margin-top: 1.25rem;
  font-size: 0.78rem;
  line-height: 1.5;
  color: var(--text-muted);
  border-top: 1px solid var(--border);
  padding-top: 1rem;
}

.summary-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 0.75rem;
  margin-bottom: 1.5rem;
}

.summary-card {
  background: var(--bg-panel);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 0.9rem 1rem;
  transition: border-color 0.15s ease, transform 0.15s ease;
}
.summary-card:hover {
  border-color: rgba(212, 162, 78, 0.35);
  transform: translateY(-1px);
}

.summary-card .card-label {
  font-size: 0.72rem;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--text-muted);
}

.summary-card .card-value {
  font-family: var(--font-mono);
  font-size: 1.35rem;
  font-weight: 600;
  margin-top: 0.3rem;
}

.card-value.pos { color: var(--gain-green); }
.card-value.neg { color: var(--risk-red); }
.card-value.accent { color: var(--accent); }

.chart-tabs {
  display: flex;
  gap: 0.4rem;
  margin-bottom: 0.75rem;
  flex-wrap: wrap;
}

.chart-tab-btn {
  background: var(--bg-panel);
  border: 1px solid var(--border);
  color: var(--text-muted);
  font-size: 0.82rem;
  padding: 0.4rem 0.8rem;
  border-radius: 20px;
  cursor: pointer;
}
.chart-tab-btn.active { color: var(--accent); border-color: var(--accent); }

.chart-panel {
  background: var(--bg-panel);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 1.25rem;
}

.chart-caption {
  font-size: 0.85rem;
  color: var(--text-muted);
  margin: 0 0 1rem;
  line-height: 1.5;
}

.section-block { margin-top: 2.25rem; }

.section-title {
  font-family: var(--font-display);
  font-size: 1.05rem;
  font-weight: 700;
  margin: 0 0 0.3rem;
}

.section-sub { color: var(--text-muted); font-size: 0.85rem; margin: 0 0 1rem; }

.two-col {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
}
@media (max-width: 860px) { .two-col { grid-template-columns: 1fr; } }

.table-scroll { overflow-x: auto; border: 1px solid var(--border); border-radius: 10px; }

.data-table {
  width: 100%;
  border-collapse: collapse;
  font-family: var(--font-mono);
  font-size: 0.83rem;
}
.data-table th, .data-table td {
  padding: 0.65rem 0.9rem;
  text-align: left;
  white-space: nowrap;
}
.data-table thead th {
  background: var(--bg-panel-2);
  color: var(--text-muted);
  font-weight: 500;
  text-transform: uppercase;
  font-size: 0.7rem;
  letter-spacing: 0.05em;
}
.data-table tbody tr { border-top: 1px solid var(--border); }
.data-table tbody tr:hover { background: var(--bg-panel-2); }

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 1rem;
}
.stat-card {
  background: var(--bg-panel);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 1rem 1.15rem;
  transition: border-color 0.15s ease, transform 0.15s ease;
}
.stat-card:hover {
  border-color: rgba(212, 162, 78, 0.35);
  transform: translateY(-1px);
}
.stat-card .stat-label { font-size: 0.8rem; color: var(--text-muted); }
.stat-card .stat-value {
  font-family: var(--font-mono);
  font-size: 1.3rem;
  font-weight: 600;
  color: var(--accent);
  margin: 0.3rem 0;
}
.stat-card .stat-note { font-size: 0.76rem; color: var(--text-muted); line-height: 1.4; }

.synthetic-banner {
  background: rgba(196, 85, 77, 0.12);
  border: 1px solid rgba(196, 85, 77, 0.4);
  color: #E8A6A0;
  font-size: 0.85rem;
  padding: 0.8rem 1rem;
  border-radius: 8px;
  margin-bottom: 1.5rem;
  line-height: 1.5;
}

.status-banner {
  font-size: 0.85rem;
  padding: 0.8rem 1rem;
  border-radius: 8px;
  margin-bottom: 1.25rem;
  line-height: 1.5;
}

.error-banner {
  background: rgba(196, 85, 77, 0.12);
  border: 1px solid rgba(196, 85, 77, 0.4);
  color: #E8A6A0;
}

.loading-indicator {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  font-size: 0.85rem;
  color: var(--text-muted);
  padding: 0.8rem 0;
  margin-bottom: 1rem;
}
.loading-indicator[hidden] {
  display: none;
}

.spinner {
  width: 14px;
  height: 14px;
  border: 2px solid var(--border);
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
  flex-shrink: 0;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

@media (prefers-reduced-motion: reduce) {
  .spinner { animation: none; border-top-color: var(--border); }
}

.about-block p { line-height: 1.65; color: var(--text); max-width: 680px; }
.about-block em { color: var(--accent); font-style: normal; }

@media (max-width: 600px) {
  .site-header { padding: 1rem 1.25rem; }
  .brand-title { font-size: 1rem; }
  .brand-sub { font-size: 0.75rem; }
  .tabs { width: 100%; justify-content: flex-start; overflow-x: auto; }
  main { padding: 1.25rem 1.25rem 2.5rem; }
  .controls-panel { position: static; }
  .summary-cards { grid-template-columns: repeat(2, 1fr); }
  .chart-panel { padding: 0.9rem; }
  .section-title { font-size: 0.95rem; }
  .ticker-item { padding: 0 1rem; font-size: 0.72rem; }
}

.site-footer {
  border-top: 1px solid var(--border);
  padding: 1.25rem 2rem;
  text-align: center;
  color: var(--text-muted);
  font-size: 0.78rem;
}

/* ===========================================================
   Compare controls (checkbox pills for multi-company selection)
   =========================================================== */
.compare-controls {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.compare-pill {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  background: var(--bg-panel);
  border: 1px solid var(--border);
  border-radius: 20px;
  padding: 0.4rem 0.9rem;
  font-size: 0.82rem;
  cursor: pointer;
  user-select: none;
}

.compare-pill input[type="checkbox"] {
  accent-color: var(--accent);
}

.compare-pill.checked {
  border-color: var(--accent);
  color: var(--accent);
}

/* ===========================================================
   Glossary (About tab)
   =========================================================== */
.glossary dt {
  font-family: var(--font-mono);
  font-weight: 600;
  color: var(--accent);
  margin-top: 1.1rem;
  font-size: 0.92rem;
}
.glossary dd {
  margin: 0.3rem 0 0;
  color: var(--text-muted);
  line-height: 1.55;
  max-width: 640px;
}

/* ===========================================================
   Inline metric tooltips (hover hint on labels)
   =========================================================== */
.metric-hint {
  border-bottom: 1px dotted var(--text-muted);
  cursor: help;
}

/* ===========================================================
   Risk & Ethics (About tab)
   =========================================================== */
.risk-badge {
  display: inline-block;
  padding: 2px 10px;
  font-size: 0.72rem;
  border-radius: 20px;
  font-weight: 600;
  letter-spacing: 0.02em;
}
.risk-badge.high {
  color: var(--risk-red);
  border: 1px solid rgba(196, 85, 77, 0.4);
  background: rgba(196, 85, 77, 0.1);
}
.risk-badge.med {
  color: var(--accent);
  border: 1px solid rgba(212, 162, 78, 0.4);
  background: rgba(212, 162, 78, 0.1);
}

.ethics-card {
  background: var(--bg-panel);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 1.25rem;
  max-width: 640px;
}
.ethics-title {
  font-family: var(--font-display);
  font-size: 0.95rem;
  color: var(--accent);
  margin: 0 0 0.75rem;
}
.ethics-list {
  margin: 0;
  padding-left: 1.1rem;
  color: var(--text-muted);
  font-size: 0.85rem;
  line-height: 1.6;
}
.ethics-list li { margin-bottom: 0.6rem; }

.approval-tag {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  margin-top: 1rem;
  font-size: 0.78rem;
  color: var(--gain-green);
  border: 1px solid rgba(78, 155, 110, 0.4);
  background: rgba(78, 155, 110, 0.1);
  padding: 0.4rem 0.8rem;
  border-radius: 20px;
}
.approval-tag .dot {
  width: 6px; height: 6px; border-radius: 50%;
  background: var(--gain-green);
}

/* ===========================================================
   Key Findings (Survey tab)
   =========================================================== */
.findings-card {
  background: var(--bg-panel);
  border: 1px solid var(--border);
  border-left: 3px solid var(--accent);
  border-radius: 8px;
  padding: 1.1rem 1.35rem;
  max-width: 720px;
}
.findings-card ul {
  margin: 0;
  padding-left: 1.1rem;
  line-height: 1.7;
  color: var(--text);
  font-size: 0.92rem;
}
.findings-card li { margin-bottom: 0.65rem; }
.findings-card li:last-child { margin-bottom: 0; }
.findings-card .finding-empty { color: var(--text-muted); font-size: 0.88rem; }

/* ===========================================================
   Print / PDF export (for thesis appendix)
   =========================================================== */
@media print {
  .ticker-strip, .tabs, .site-footer, .primary-btn, #loadBtn,
  #compareBtn, .print-btn, .controls-panel, .chart-tabs {
    display: none !important;
  }
  body { background: #fff; color: #111; }
  .tab-panel { display: block !important; page-break-after: always; }
  .site-header { border-bottom: 1px solid #ccc; }
  .layout { grid-template-columns: 1fr !important; }
  .chart-panel, .summary-card, .stat-card, .findings-card,
  .ethics-card, .data-table, .table-scroll {
    background: #fff !important;
    border-color: #ccc !important;
    color: #111 !important;
    box-shadow: none !important;
  }
  .card-value, .stat-value, .brand-title, .section-title { color: #111 !important; }
  .card-value.pos { color: #1a6b3c !important; }
  .card-value.neg, .card-value.accent { color: #a3392f !important; }
  canvas { max-width: 100% !important; }
}
CSSEOF

echo "Updating js/main.js..."
cat > js/main.js << 'MAINEOF'
import { CHART_COLORS } from "./utils.js";
import { loadTickerList, loadTickerView, loadMarketSummaryTable, loadCorrelationTable, loadComparisonChart, setupChartTabs } from "./market.js";
import { loadSurveySummary, loadSectorLinkage, loadSurveyStats } from "./survey.js";

Chart.defaults.color = CHART_COLORS.muted;
Chart.defaults.borderColor = CHART_COLORS.grid;
Chart.defaults.font.family = "IBM Plex Mono, monospace";

document.querySelectorAll(".tab-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".tab-btn").forEach((b) => b.classList.remove("active"));
    document.querySelectorAll(".tab-panel").forEach((p) => p.classList.remove("active"));
    btn.classList.add("active");
    document.getElementById(`tab-${btn.dataset.tab}`).classList.add("active");
  });
});

setupChartTabs();

const printBtn = document.getElementById("printBtn");
if (printBtn) {
  printBtn.addEventListener("click", () => window.print());
}

async function init() {
  await loadTickerList();
  await loadTickerView();
  await loadMarketSummaryTable();
  await loadCorrelationTable();
  await loadSurveySummary();
  await loadSurveyStats();
  await loadSectorLinkage();

  document.getElementById("loadBtn").addEventListener("click", loadTickerView);
  document.getElementById("compareBtn").addEventListener("click", loadComparisonChart);
}

init();
MAINEOF

echo "Updating js/survey.js..."
cat > js/survey.js << 'SURVEYEOF'
import { API_BASE, CHART_COLORS, showLoading, showError, friendlyFetchError } from "./utils.js";

let _summary = null;
let _stats = null;
let _linkage = null;

export async function loadSurveySummary() {
  showError("surveyError", null);
  showLoading("surveyLoading", true);

  let data;
  try {
    const res = await fetch(`${API_BASE}/survey/summary`);
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      showError("surveyError", body.error || "Survey data isn't available right now.");
      return;
    }
    data = await res.json();
  } catch (err) {
    showError("surveyError", friendlyFetchError(err));
    return;
  } finally {
    showLoading("surveyLoading", false);
  }

  document.getElementById("syntheticBanner").hidden = !data.is_synthetic;
  document.getElementById("respondentCount").textContent = `Based on ${data.n_respondents} respondents`;

  new Chart(document.getElementById("challengeChart"), {
    type: "bar",
    data: {
      labels: data.ranked_challenges.map((c) => c.challenge),
      datasets: [{ label: "Avg score (1-5)", data: data.ranked_challenges.map((c) => c.avg_score), backgroundColor: CHART_COLORS.accent }],
    },
    options: {
      indexAxis: "y",
      responsive: true,
      scales: { x: { min: 0, max: 5, grid: { color: CHART_COLORS.grid } }, y: { grid: { display: false } } },
      plugins: { legend: { display: false } },
    },
  });

  new Chart(document.getElementById("experienceChart"), {
    type: "bar",
    data: {
      labels: data.by_experience.map((r) => r.experience),
      datasets: [{ label: "Avg challenge score", data: data.by_experience.map((r) => r.avg_challenge_score), backgroundColor: CHART_COLORS.purple }],
    },
    options: {
      responsive: true,
      scales: { y: { min: 0, max: 5, grid: { color: CHART_COLORS.grid } }, x: { grid: { display: false } } },
      plugins: { legend: { display: false } },
    },
  });

  new Chart(document.getElementById("ageChart"), {
    type: "bar",
    data: {
      labels: data.by_age.map((r) => r.segment),
      datasets: [{ label: "Avg challenge score", data: data.by_age.map((r) => r.avg_challenge_score), backgroundColor: CHART_COLORS.green }],
    },
    options: {
      responsive: true,
      scales: { y: { min: 0, max: 5, grid: { color: CHART_COLORS.grid } }, x: { grid: { display: false } } },
      plugins: { legend: { display: false } },
    },
  });

  const profitLabels = Object.keys(data.profitability_pct);
  new Chart(document.getElementById("profitChart"), {
    type: "doughnut",
    data: {
      labels: profitLabels,
      datasets: [{
        data: profitLabels.map((k) => data.profitability_pct[k]),
        backgroundColor: [CHART_COLORS.green, CHART_COLORS.red, CHART_COLORS.accent, CHART_COLORS.muted],
        borderColor: "#161D26",
        borderWidth: 2,
      }],
    },
    options: { responsive: true, plugins: { legend: { position: "bottom", labels: { boxWidth: 12, font: { size: 11 } } } } },
  });

  _summary = data;
  renderKeyFindings();
}

export async function loadSectorLinkage() {
  try {
    const res = await fetch(`${API_BASE}/survey/linkage`);
    if (!res.ok) return;
    const data = await res.json();
    const linkage = data.linkage;

    new Chart(document.getElementById("linkageChart"), {
      type: "bar",
      data: {
        labels: linkage.map((r) => r.sector),
        datasets: [
          {
            label: "Real Volatility (%)",
            data: linkage.map((r) => r.real_volatility_pct),
            backgroundColor: CHART_COLORS.accent,
            yAxisID: "y",
          },
          {
            label: "Perceived Difficulty (1-5)",
            data: linkage.map((r) => r.perceived_difficulty),
            backgroundColor: CHART_COLORS.purple,
            yAxisID: "y1",
          },
        ],
      },
      options: {
        responsive: true,
        scales: {
          y: {
            type: "linear",
            position: "left",
            title: { display: true, text: "Real Volatility (%)", color: CHART_COLORS.accent },
            grid: { color: CHART_COLORS.grid },
          },
          y1: {
            type: "linear",
            position: "right",
            min: 0,
            max: 5,
            title: { display: true, text: "Perceived Difficulty (1-5)", color: CHART_COLORS.purple },
            grid: { drawOnChartArea: false },
          },
          x: { grid: { display: false } },
        },
        plugins: { legend: { labels: { boxWidth: 12, font: { size: 11 } } } },
      },
    });
    _linkage = linkage;
    renderKeyFindings();
  } catch (err) {
    // Silently skip — this is a supplementary chart, not critical path.
  }
}

export async function loadSurveyStats() {
  let data;
  try {
    const res = await fetch(`${API_BASE}/survey/stats`);
    if (!res.ok) return;
    data = await res.json();
  } catch (err) {
    return;
  }

  const expCorr = data.experience_vs_challenge_correlation;
  const volCorr = data.volatility_vs_perceived_difficulty_correlation;
  const reg = data.regression;

  document.getElementById("statsGrid").innerHTML = `
    <div class="stat-card">
      <div class="stat-label">Experience vs. Challenge Score</div>
      <div class="stat-value">r = ${expCorr.r}</div>
      <div class="stat-note">p = ${expCorr.p_value} — ${Math.abs(expCorr.r) > 0.3 ? "meaningful negative correlation: more experience, fewer reported challenges." : "weak relationship."}</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">Sector Volatility vs. Perceived Difficulty</div>
      <div class="stat-value">r = ${volCorr.r}</div>
      <div class="stat-note">p = ${volCorr.p_value}</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">Regression R²</div>
      <div class="stat-value">${reg.r_squared}</div>
      <div class="stat-note">Predictors: experience, portfolio size, trade frequency.</div>
    </div>
  `;

  _stats = data;
  renderKeyFindings();
}

const PREDICTOR_LABELS = {
  experience_ordinal: "investing experience",
  portfolio_ordinal: "portfolio size",
  trade_freq_ordinal: "trade frequency",
};

function renderKeyFindings() {
  const el = document.getElementById("keyFindings");
  if (!el) return;
  if (!_summary || !_stats) {
    el.innerHTML = `<p class="finding-empty">Findings will appear once survey data has loaded.</p>`;
    return;
  }

  const points = [];

  const top = _summary.ranked_challenges[0];
  if (top) {
    points.push(
      `The most widely reported challenge among ${_summary.n_respondents} respondents is <strong>${top.challenge}</strong> (avg score ${top.avg_score}/5).`
    );
  }

  const exp = _stats.experience_vs_challenge_correlation;
  if (exp) {
    const strength = Math.abs(exp.r) > 0.5 ? "strong" : Math.abs(exp.r) > 0.3 ? "moderate" : "weak";
    const direction = exp.r < 0 ? "fewer" : "more";
    const sig = exp.p_value < 0.05 ? "statistically significant" : "not statistically significant at the 0.05 level";
    points.push(
      `Investing experience shows a ${strength} correlation with reported challenges (r = ${exp.r}, ${sig}) — more experienced investors tend to report ${direction} challenges overall.`
    );
  }

  const vol = _stats.volatility_vs_perceived_difficulty_correlation;
  if (vol) {
    const tracks = Math.abs(vol.r) > 0.4;
    points.push(
      tracks
        ? `Perceived difficulty tracks real market volatility reasonably well (r = ${vol.r}), suggesting respondents can broadly distinguish riskier sectors.`
        : `Perceived difficulty only weakly tracks real market volatility (r = ${vol.r}), suggesting many respondents are not accurately distinguishing higher-risk sectors from lower-risk ones.`
    );
  }

  if (_linkage && _linkage.length > 0) {
    const withGap = _linkage.map((r) => ({
      ...r,
      gap: (r.real_volatility_pct / Math.max(...(_linkage.map((x) => x.real_volatility_pct)))) -
           (r.perceived_difficulty / 5),
    }));
    const underrated = withGap.reduce((a, b) => (b.gap > a.gap ? b : a));
    if (underrated.gap > 0.15) {
      points.push(
        `<strong>${underrated.sector}</strong> stands out as a sector where real volatility (${underrated.real_volatility_pct}%) is high relative to how difficult respondents rated it (${underrated.perceived_difficulty}/5) — a potential blind spot for new investors.`
      );
    }
  }

  const reg = _stats.regression;
  if (reg) {
    const sigPredictors = Object.entries(reg.coefficients)
      .filter(([name, c]) => name !== "const" && c.p_value < 0.05)
      .sort((a, b) => Math.abs(b[1].coef) - Math.abs(a[1].coef));
    if (sigPredictors.length > 0) {
      const [name, c] = sigPredictors[0];
      points.push(
        `In the regression model (R² = ${reg.r_squared}), <strong>${PREDICTOR_LABELS[name] || name}</strong> is the strongest significant predictor of overall challenge score (coef = ${c.coef}, p = ${c.p_value}).`
      );
    } else {
      points.push(
        `In the regression model (R² = ${reg.r_squared}), none of the three predictors reached statistical significance at the 0.05 level — overall challenge score may be driven more by factors not captured in this survey.`
      );
    }
  }

  if (_summary.is_synthetic) {
    points.push(
      `<em>Note: these findings are currently based on synthetic placeholder data and should not be cited until real survey responses replace it.</em>`
    );
  }

  el.innerHTML = `<ul>${points.map((p) => `<li>${p}</li>`).join("")}</ul>`;
}
SURVEYEOF

echo "Done. market.js and utils.js were not changed."

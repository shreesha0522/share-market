import { API_BASE, showError, friendlyFetchError } from "./utils.js";

export async function loadMethodologyComparison() {
  showError("methodologyError", null);

  let stats, ml;
  try {
    const [statsRes, mlRes] = await Promise.all([
      fetch(`${API_BASE}/survey/stats`),
      fetch(`${API_BASE}/survey/ml`),
    ]);
    if (!statsRes.ok || !mlRes.ok) throw new Error("Couldn't load methodology comparison data.");
    stats = await statsRes.json();
    ml = await mlRes.json();
  } catch (err) {
    showError("methodologyError", friendlyFetchError(err));
    return;
  }

  const reg = ml.challenge_score_prediction;
  const cls = ml.high_challenge_classification;

  const table = document.getElementById("methodologyTable");
  if (table && !reg.error) {
    table.innerHTML = `
      <thead>
        <tr><th>Model</th><th>Task</th><th>Fit / Accuracy</th><th>Error</th><th>Notes</th></tr>
      </thead>
      <tbody>
        <tr>
          <td>OLS Regression</td>
          <td>Predict challenge score (statsmodels)</td>
          <td>R² = ${stats.regression.r_squared}</td>
          <td>—</td>
          <td>Interpretable coefficients; assumes a linear relationship between traits and challenge score.</td>
        </tr>
        <tr>
          <td>Linear Regression (ML baseline)</td>
          <td>Predict challenge score (scikit-learn)</td>
          <td>R² = ${reg.linear_regression_baseline.r_squared}</td>
          <td>MAE = ${reg.linear_regression_baseline.mae}</td>
          <td>Same linear assumption as OLS, evaluated on a held-out test split rather than full-sample fit.</td>
        </tr>
        <tr>
          <td>Random Forest Regressor</td>
          <td>Predict challenge score</td>
          <td>R² = ${reg.random_forest.r_squared}</td>
          <td>MAE = ${reg.random_forest.mae}</td>
          <td>Captures non-linear interactions between traits; reports feature importance instead of coefficients.</td>
        </tr>
        ${!cls.error ? `
        <tr>
          <td>Random Forest Classifier</td>
          <td>High vs. low challenge (median split)</td>
          <td>Accuracy = ${(cls.accuracy * 100).toFixed(0)}%</td>
          <td>F1 = ${cls.f1}</td>
          <td>Reframes the same question as classification rather than a continuous score.</td>
        </tr>` : ""}
      </tbody>
    `;
  }

  const note = document.getElementById("methodologyLimitations");
  if (note) {
    const n = reg.n_samples ?? stats.n_respondents ?? "an unknown number of";
    const holdoutText = reg.used_holdout_test_set
      ? `a held-out test set of only ${reg.test_set_size} respondents`
      : `no held-out test set at all (the sample was too small to split meaningfully), so the ML metrics above reflect fit on the training data itself`;

    note.innerHTML = `
      <p>
        This study reports both classical statistics (OLS regression, Pearson correlation) and
        machine learning models (Random Forest regression and classification) on the same
        survey data intentionally — not because one is "better," but because they answer
        slightly different questions. OLS gives directly interpretable coefficients and
        p-values, which are appropriate for a small, hypothesis-driven survey. The Random
        Forest models can capture non-linear interactions between traits, but come at the
        cost of interpretability and require more data to generalize reliably.
      </p>
      <p>
        With <strong>${n} respondents</strong> and ${holdoutText}, none of the ML metrics
        above should be read as a validated, generalizable model. They are reported as an
        exploratory comparison to the classical regression, and as a demonstration of the
        analysis pipeline — a direction to strengthen once a larger, real respondent sample
        is collected. This limitation is intentional and disclosed rather than hidden, in
        line with the risk-mitigation approach described above.
      </p>
    `;
  }
}

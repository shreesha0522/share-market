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
          <td>Interpretable coefficients; fit on the full sample, no cross-validation; assumes a linear relationship.</td>
        </tr>
        <tr>
          <td>Linear Regression (ML baseline)</td>
          <td>Predict challenge score (scikit-learn)</td>
          <td>R² = ${reg.linear_regression_baseline.r_squared_mean} ± ${reg.linear_regression_baseline.r_squared_std}</td>
          <td>MAE = ${reg.linear_regression_baseline.mae_mean} ± ${reg.linear_regression_baseline.mae_std}</td>
          <td>${reg.cv_folds}-fold cross-validated (mean ± std across folds) — same linear assumption as OLS, evaluated out-of-sample.</td>
        </tr>
        <tr>
          <td>Random Forest Regressor</td>
          <td>Predict challenge score</td>
          <td>R² = ${reg.random_forest.r_squared_mean} ± ${reg.random_forest.r_squared_std}</td>
          <td>MAE = ${reg.random_forest.mae_mean} ± ${reg.random_forest.mae_std}</td>
          <td>${reg.cv_folds}-fold cross-validated. Captures non-linear interactions between traits; reports feature importance instead of coefficients.</td>
        </tr>
        ${!cls.error ? `
        <tr>
          <td>Random Forest Classifier</td>
          <td>High vs. low challenge (median split)</td>
          <td>Accuracy = ${(cls.accuracy_mean * 100).toFixed(0)}% ± ${(cls.accuracy_std * 100).toFixed(0)}%</td>
          <td>F1 = ${cls.f1_mean} ± ${cls.f1_std}</td>
          <td>${cls.cv_folds}-fold cross-validated. Reframes the same question as classification rather than a continuous score.</td>
        </tr>` : ""}
      </tbody>
    `;
  }

  const note = document.getElementById("methodologyLimitations");
  if (note) {
    const n = reg.n_samples ?? stats.n_respondents ?? "an unknown number of";
    const k = reg.cv_folds;
    const cvText = k
      ? `${k}-fold cross-validation (each fold takes a turn as the test set, and the reported figures are the mean ± standard deviation across all folds)`
      : `no cross-validated evaluation, as the sample was too small`;

    const accBelowChance = !cls.error && cls.accuracy_mean < 0.5
      ? `<p>Notably, the classifier's cross-validated accuracy (${(cls.accuracy_mean * 100).toFixed(0)}%) is <strong>at or below the 50% chance baseline</strong> for a two-class median split. This is reported honestly rather than omitted: with a sample this small and noisy, the model is not currently able to reliably separate high- from low-challenge investors, and this should be read as a negative result pending a larger sample — not evidence that the underlying traits are unrelated to challenge, only that this model, on this data, cannot detect it reliably.</p>`
      : "";

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
        The ML models above use ${cvText}, rather than a single train/test split — a single
        split on only ${n} respondents can swing wildly depending on which few rows happen to
        land in the test set. Cross-validation gives a more stable, honest estimate, at the
        cost of a wider uncertainty range (the ± figures above).
      </p>
      ${accBelowChance}
      <p>
        With only <strong>${n} respondents</strong>, none of the ML metrics above should be
        read as a validated, generalizable model. They are reported as an exploratory
        comparison to the classical regression, and as a demonstration of the analysis
        pipeline — a direction to strengthen once a larger, real respondent sample is
        collected. This limitation is intentional and disclosed rather than hidden.
      </p>
    `;
  }
}

export const API_BASE = "http://127.0.0.1:5000/api";

export const CHART_COLORS = {
  accent: "#D4A24E",
  red: "#C4554D",
  green: "#4E9B6E",
  purple: "#8A7CC7",
  muted: "#8B96A3",
  grid: "#2A3441",
  text: "#E8EAED",
};

export function showLoading(id, isLoading) {
  document.getElementById(id).hidden = !isLoading;
}

export function showError(id, message) {
  const el = document.getElementById(id);
  if (!message) {
    el.hidden = true;
    el.textContent = "";
    return;
  }
  el.hidden = false;
  el.textContent = message;
}

export function friendlyFetchError(err) {
  if (err instanceof TypeError) {
    return "Couldn't reach the server. Make sure the Flask backend is running on http://127.0.0.1:5000.";
  }
  return err.message || "Something went wrong loading this data.";
}

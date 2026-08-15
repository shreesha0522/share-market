# Security Policy

This is an academic thesis project, not a production service. It runs
locally (Flask backend on `127.0.0.1:5000`, static frontend on
`127.0.0.1:8000`) and is not deployed with real user data or authentication.

## Scope

- The Flask development server (`app.run(debug=True)`) is intended for
  local development only and should never be exposed to the public internet
  as-is.
- Survey data used in this project is currently synthetic placeholder data.
  If real survey responses are collected in future, they must be handled
  under the institution's data protection and research ethics policies.

## Reporting an issue

If you notice a security concern in this codebase (e.g. a dependency with a
known vulnerability, or unsafe handling of user input), please open an issue
on the GitHub repository describing the concern.

## Known limitations (by design, for a local academic project)

- No authentication on API endpoints — acceptable since this only runs on
  `127.0.0.1` for local development and demonstration.
- CORS is fully open (`flask-cors` with default settings) — acceptable for
  the same reason.
- Debug mode is enabled by default in local development, which should never
  be the case in a production deployment.

.PHONY: backend frontend test install validate-data clean

# Start the Flask backend (requires venv to be activated)
backend:
	cd backend && python app.py

# Start the frontend static file server
frontend:
	cd frontend && python3 -m http.server 8000

# Run the backend test suite
test:
	cd backend && python3 -m pytest tests/ -v

# Install backend dependencies
install:
	pip install -r backend/requirements.txt

# Run data quality checks on the market and survey CSVs
validate-data:
	python3 scripts/validate_data.py

# Remove generated cache files
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	rm -rf backend/.pytest_cache

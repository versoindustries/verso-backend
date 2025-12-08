# Makefile for Verso-Backend

.PHONY: dev db lint test package clean

# Default target
all: dev

# Run development server
dev:
	@echo "Starting development server..."
	.venv/bin/python run.py

# Initialize/Upgrade database
db:
	@echo "Initializing/Upgrading database..."
	export FLASK_APP=app && .venv/bin/flask db upgrade
	export FLASK_APP=app && .venv/bin/flask create-roles
	export FLASK_APP=app && .venv/bin/flask seed-business-config

# Lint code
lint:
	@echo "Linting code..."
	# Assuming flake8 is installed or will be installed
	.venv/bin/pip install flake8
	.venv/bin/flake8 app run.py

# Run tests
test:
	@echo "Running tests..."
	# Assuming pytest is installed or will be installed
	.venv/bin/pip install pytest
	.venv/bin/pytest

# Package application for offline handoff
package: clean
	@echo "Packaging application..."
	mkdir -p dist
	zip -r dist/verso-backend.zip . -x "*.git*" -x "*.venv*" -x "__pycache__" -x "*.pyc" -x "dist*" -x "verso.sqlite" -x ".env"
	@echo "Package created at dist/verso-backend.zip"

# Clean artifacts
clean:
	@echo "Cleaning artifacts..."
	rm -rf dist
	rm -rf *.pyc
	rm -rf __pycache__

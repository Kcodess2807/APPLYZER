.PHONY: help install dev-install test lint format clean run migrate db-upgrade db-downgrade

help:
	@echo "Available commands:"
	@echo "  make install       - Install production dependencies"
	@echo "  make dev-install   - Install development dependencies"
	@echo "  make test          - Run tests"
	@echo "  make test-cov      - Run tests with coverage"
	@echo "  make lint          - Run linters"
	@echo "  make format        - Format code"
	@echo "  make clean         - Clean up cache files"
	@echo "  make run           - Run development server"
	@echo "  make migrate       - Create new migration"
	@echo "  make db-upgrade    - Apply database migrations"
	@echo "  make db-downgrade  - Rollback database migration"

install:
	pip install -r requirements.txt

dev-install:
	pip install -r requirements.txt
	pip install -e .

test:
	pytest tests/ -v

test-cov:
	pytest tests/ --cov=app --cov-report=html --cov-report=term

test-agents:
	pytest tests/test_agents/ -v

lint:
	flake8 app tests
	mypy app

format:
	black app tests
	isort app tests

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	rm -rf htmlcov/
	rm -rf .coverage

run:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

migrate:
	@read -p "Enter migration message: " msg; \
	alembic revision --autogenerate -m "$$msg"

db-upgrade:
	alembic upgrade head

db-downgrade:
	alembic downgrade -1

docker-build:
	docker build -t applybot:latest .

docker-run:
	docker-compose up -d

docker-stop:
	docker-compose down

setup-dev:
	cp .env.example .env
	make dev-install
	make db-upgrade
	@echo "Development environment setup complete!"
	@echo "Edit .env file with your configuration"

.PHONY: help install dev build test clean docker-up docker-down

help:
	@echo "Available commands:"
	@echo "  make install         - Install dependencies"
	@echo "  make dev             - Run in development mode"
	@echo "  make build           - Build production images"
	@echo "  make test            - Run tests"
	@echo "  make clean           - Clean up temporary files"
	@echo "  make docker-up       - Start Docker containers"
	@echo "  make docker-down     - Stop Docker containers"

install:
	@echo "Installing backend dependencies..."
	cd backend && pip install -r requirements.txt
	@echo "Installing frontend dependencies..."
	cd frontend && npm install

dev:
	@echo "Starting development environment..."
	docker-compose up

dev-backend:
	@echo "Starting backend in development..."
	cd backend && python main.py

dev-frontend:
	@echo "Starting frontend in development..."
	cd frontend && npm start

build:
	@echo "Building Docker images..."
	docker-compose build

test:
	@echo "Running tests..."
	cd backend && pytest

clean:
	@echo "Cleaning up..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name ".pytest_cache" -delete
	find . -type d -name "node_modules" -delete
	find . -type d -name "build" -delete
	find . -type d -name "dist" -delete

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

db-migrate:
	@echo "Running database migrations..."
	cd backend && alembic upgrade head

db-seed:
	@echo "Seeding database with sample data..."
	cd backend && python scripts/seed_database.py

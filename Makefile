# Musharaka Pro - Makefile

.PHONY: help install run test clean deploy health

# Default target
help:
	@echo "Musharaka Pro - Available commands:"
	@echo "  install    - Install dependencies"
	@echo "  run        - Run the application locally"
	@echo "  test       - Run tests"
	@echo "  health     - Check application health"
	@echo "  clean      - Clean up temporary files"
	@echo "  deploy     - Deploy to Render (requires git push)"
	@echo "  docker     - Run with Docker Compose"

# Install dependencies
install:
	pip3 install -r requirements.txt --break-system-packages

# Run locally
run:
	python3 app.py

# Run tests
test:
	python3 test_deployment.py

# Health check
health:
	python3 healthcheck.py

# Clean up
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	rm -rf instance/*.db
	rm -rf .pytest_cache

# Deploy (push to git)
deploy:
	@echo "Pushing to git repository..."
	git add .
	git commit -m "Deploy to Render - $(shell date)"
	git push origin main
	@echo "Deployment initiated. Check Render dashboard for progress."

# Docker commands
docker-build:
	docker-compose build

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

# Development
dev-install:
	pip3 install -r requirements.txt --break-system-packages
	pip3 install pytest requests --break-system-packages

dev-test:
	python3 -m pytest test_deployment.py -v

# Production
prod-install:
	pip install -r requirements.txt

prod-run:
	gunicorn app:app --bind 0.0.0.0:$(PORT) --workers 2
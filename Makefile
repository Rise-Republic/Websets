.PHONY: setup lint test docker-build

# Setup development environment
setup:
		bash scripts/setup.sh

# Run linters for Python and frontend code
lint:
	ruff check .
	npm run lint

# Execute backend and frontend tests
test:
	bash scripts/test.sh

# Build Docker image for deployment
docker-build:
	docker build -t webset-miner .

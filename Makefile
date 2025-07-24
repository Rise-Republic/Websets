.PHONY: setup lint fmt test start stop docker-build

# Setup development environment
setup:
	bash scripts/setup.sh

# Run linters for Python and frontend code
lint:
	ruff check .
	npm run lint

# Format Python and frontend code
fmt:
	ruff format .
	npm run lint -- --fix

# Execute backend and frontend tests
test:
	bash scripts/test.sh

# Start local services
start:
	docker compose up -d

# Stop local services
stop:
	docker compose down

# Build Docker image for deployment
docker-build:
	docker build -t webset-miner .

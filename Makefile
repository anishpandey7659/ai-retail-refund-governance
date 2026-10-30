SERVICES = postgres minio

.PHONY: up check seed down run

up:
	docker compose up -d 

check:
	@for s in $(SERVICES); do \
		docker compose ps --status running --services | grep -qx $$s || { echo "$$s is not running. Run: make up"; exit 1; }; \
	done
	@echo "All services are running"

seed: check
	PYTHONPATH=. uv run python seed/seed.py

down:
	docker compose down 

run: check
	uv run uvicorn backend.main:app --reload
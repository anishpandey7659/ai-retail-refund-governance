SERVICES = postgres minio mailhog redis keycloak qdrant
ONESHOT  = minio-init
.PHONY: up check seed down run worker stop test_worker

up:
	docker compose up -d 

check:
	@for s in $(SERVICES); do \
		docker compose ps --status running --services | grep -qx $$s || { echo "$$s is not running. Run: make up"; exit 1; }; \
	done
	@for s in $(ONESHOT); do \
		docker compose ps -a --status exited --format '{{.Service}} {{.ExitCode}}' | grep -qx "$$s 0" || { echo "$$s did not complete successfully. Run: make up"; exit 1; }; \
	done
	@echo "All services are ready"

seed: check
	PYTHONPATH=. uv run python seed/seed.py

stop:
	docker compose stop

down:
	docker compose down

run: check
	uv run uvicorn backend.main:app --reload

worker: check
	uv run arq worker.pipeline.workers.WorkerSettings

test_worker: check
	uv run python -m scripts.test_worker


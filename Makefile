.PHONY: up down client reset

up:
	docker rm -f hifi_interview-client-1 2>/dev/null || true
	docker compose up --build -d

down:
	docker rm -f hifi_interview-client-1 2>/dev/null || true
	docker compose down -v --remove-orphans

client:
	docker compose up --remove-orphans client

reset:
	docker compose up reset_db

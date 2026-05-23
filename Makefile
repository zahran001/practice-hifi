.PHONY: up down client reset

up:
	docker compose up --build -d

down:
	docker compose down -v --remove-orphans

client:
	docker compose up --remove-orphans client

reset:
	docker compose up reset_db

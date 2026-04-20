.PHONY: up down client reset

up:
	docker ps -aq --filter name=client | xargs -r docker rm -f
	docker compose up --build -d

down:
	docker ps -aq --filter name=client | xargs -r docker rm -f
	docker compose down -v --remove-orphans

client:
	docker compose up --remove-orphans client

reset:
	docker compose up reset_db

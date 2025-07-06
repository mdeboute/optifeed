.PHONY: up down build stop start logs logs-fastapi logs-worker logs-ngrok restart

up:
	docker compose --env-file .env up -d

down:
	docker compose down

build:
	docker compose build

stop:
	docker compose stop

start:
	docker compose start

logs:
	docker compose logs -f

logs-fastapi:
	docker compose logs -f fastapi

logs-worker:
	docker compose logs -f worker

logs-ngrok:
	docker compose logs -f ngrok

restart:
	docker compose down && docker compose --env-file .env up -d

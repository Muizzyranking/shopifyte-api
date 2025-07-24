.PHONY: run migrate shell

run:
	uv run python manage.py runserver

migrate:
	uv run python manage.py makemigrations
	uv run python manage.py migrate

shell:
	uv run python manage.py shell

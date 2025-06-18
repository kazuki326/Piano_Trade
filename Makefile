.PHONY: install test playwright-init

install:
	poetry install

playwright-init:
	poetry run playwright install --with-deps

test:
	poetry run pytest --cov

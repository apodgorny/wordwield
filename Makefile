#!make
include .env

.PHONY: start clear test apitest check install reinstall

check:
	echo $(PROJECT_PATH)

run:
	@clear
	@path="$${PROJECT_PATH:-$$(pwd)}"; \
	echo "Web server removed. Run a project entrypoint directly, e.g.:"; \
	echo "PYTHONPATH=$$path python projects/narrative/main.py"

test:
	clear && PYTHONPATH=$(PROJECT_PATH) pytest

apitest:
	clear && schemathesis run http://127.0.0.1:8000/openapi.json --base-url=http://localhost:8000 --experimental=openapi-3.1 || true && rm "$(PROJECT_PATH)/dapi.db"

clear:
	rm "$(PROJECT_PATH)/dapi.db" && echo "Cleared database"

install:
	pip install -e .

reinstall:
	pip uninstall -y wordwield || true
	pip install -e .

SHELL := /bin/bash

.PHONY: install dev test evaluate run

install:
	python -m pip install -e ".[dev]"

test:
	python -m unittest discover -s tests -v

evaluate:
	python -m support_assistant.evaluate

run:
	uvicorn support_assistant.api:app --reload --host 0.0.0.0 --port 8000
.PHONY: lint lint-fix format format-check test build tag

lint:
	uv run ruff check .

lint-fix:
	uv run ruff check --fix .

format:
	uv run ruff format .

format-check:
	uv run ruff format --check .

test:
	uv run pytest

build:
	uv build

tag:
ifndef VERSION
	$(error VERSION is required, e.g. make tag VERSION=0.1.0)
endif
	git tag -a v$(VERSION) -m "Release v$(VERSION)"
	git push origin v$(VERSION)

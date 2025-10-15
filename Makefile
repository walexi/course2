SHELL = /usr/bin/env bash -o pipefail

default: help

.PHONY: help
help:
	# Usage:
	@sed -n '/^\([a-z][^:]*\).*/s//    make \1/p' $(MAKEFILE_LIST)

.PHONY: install
install:
	python3 -m venv env; \
	source env/bin/activate; \
	pip install -r requirements.txt; \

.PHONY: test
test:
	source env/bin/activate; \
	PROMETHEUS_MULTIPROC_DIR=~/. \
	python -m pytest; \

.PHONY: run
run:
	source env/bin/activate; \
	source .env; \
	PROMETHEUS_MULTIPROC_DIR=~/. \
	python -m app; \


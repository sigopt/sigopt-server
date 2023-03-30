SHELL = /usr/bin/env bash -eo pipefail

.PHONY: clean pytest compile protocompile vulture vulture-allowlist

DIRS = scratch web/static/js

compile: protocompile pytest

dist-compile: compile
	@python -m compileall .

protocompile:
	@./tools/protobuf/compile.sh

docker-protocompile:
	@./scripts/dev/compile_protobuf_in_docker.sh

clean-test-pycache:
	@./scripts/dev/clean_test_pycache.sh

ensure-test-inits:
	@./scripts/dev/ensure_inits.sh test/integration

setup-integration-tests: clean-test-pycache ensure-test-inits protocompile

clean-py:
	@find . -name '*.pyc' -delete
	@./scripts/dev/clean_pycache.sh .

clean: clean-py
	@git clean -fdX src/python/zigopt/protobuf/gen
	@git clean -fdX web/js/zigopt

pytest: clean-test-pycache protocompile
	@./test/unit_tests.sh

test: pytest

computetest:
	@./pp pytest -rw --durations=5 test/python/testcompute

auxtest:
	@./pp pytest -rw --durations=5 test/python/testaux

litetest:
	@cd sigoptlite && make test

vulture:
	@./tools/dead-code/run_vulture.py

vulture-allowlist:
	@./tools/dead-code/run_vulture.py --make-whitelist

web-dead-code:
	@./tools/dead-code/web_resources.py

setup-filestorage:
	@./scripts/launch/compose.sh run --rm init-minio-filestorage

fix-db: docker-protocompile
	@./scripts/dev/createdb_in_docker.sh config/development.json --fake-data --drop-tables

setup-cookiejar:
	@./scripts/launch/compose.sh run --rm init-minio-cookiejar

setup-hooks: python-requirements
	@pre-commit install --install-hooks

mkdirs: $(DIRS)

$(DIRS): %:
	@mkdir -p "$*"

js-requirements:
	@NODE_ENV=development yarn install

python-requirements:
	@pip install --upgrade pip==22.1.2
	@pip install --upgrade -r requirements.txt
	@pip install --upgrade -r requirements-dev.txt
	@pip uninstall -y pytest-rerunfailures

playwright-install: python-requirements
	@playwright install chromium

local-requirements: js-requirements python-requirements

submodules:
	@git submodule init && git submodule update

update: mkdirs submodules docker-protocompile local-requirements playwright-install setup-hooks setup-cookiejar setup-filestorage

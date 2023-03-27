SHELL = /usr/bin/env bash -eo pipefail

.PHONY: clean pytest lint compile protocompile vulture vulture-allowlist

DIRS = scratch web/static/js

DEVELOPMENT_IMAGES = \
	nginx \
	node-development \
	python-development \
	test-runner

RUN_IMAGES = \
	nginx \
	web \
	zigopt

compile: protocompile pytest lint eslint

dist-compile: compile
	@python -m compileall .

protocompile:
	@./tools/protobuf/compile.sh

docker-protocompile: build-debug-images
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
	@cd sigoptcompute && make test

auxtest:
	@cd sigoptaux && make test

litetest:
	@cd sigoptlite && make test

sort-imports:
	@./tools/lint/python/isort_lint.sh --fix

lint: vulture
	@./pp ./lint --isort-args --fix

lint-nofix: vulture
	@./pp ./lint

vulture:
	@./tools/dead-code/run_vulture.py

vulture-allowlist:
	@./tools/dead-code/run_vulture.py --make-whitelist

mypy:
	@./tools/lint/python/mypy.sh

web-dead-code:
	@./tools/dead-code/web_resources.py

eof-lint:
	@./pp ./tools/lint/common/eof_lint.sh

eslint:
	@./tools/lint/javascript/eslint.sh --fix

eslint-nofix:
	@./tools/lint/javascript/eslint.sh

prettier:
	@./scripts/dev/prettier.sh --write .

setup-filestorage:
	@./scripts/launch/compose.sh run --rm init-minio-filestorage

fix-db: docker-protocompile
	@./scripts/dev/createdb_in_docker.sh config/development.json --fake-data --drop-tables

setup-cookiejar:
	@./scripts/launch/compose.sh run --rm init-minio-cookiejar

setup-pre-push:
	@ln -fs $$(pwd)/tools/git/pre-push.sh .git/hooks/pre-push

setup-pre-commit:
	@ln -fs $$(pwd)/tools/git/pre-commit.sh .git/hooks/pre-commit

setup-post-checkout:
	@ln -fs "$$(pwd)/tools/git/post-checkout.sh" .git/hooks/post-checkout

setup-hooks: setup-pre-push setup-post-checkout
	@echo "installed pre-push and post-checkout hooks"
	@echo "pre-commit hooks may be slow; run \`make setup-pre-commit\` if you want them"

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

build-docker-images: mkdirs submodules
	@ python3 docker/image_builder.py \
		--build-tag=latest \
		--threads=2 \
		--clean-intermediate \
		$(RUN_IMAGES)

build-debug-images: mkdirs submodules
	@ python3 docker/image_builder.py \
		--build-tag=latest \
		--threads=2 \
		--clean-intermediate \
		$(DEVELOPMENT_IMAGES)

submodules:
	@git submodule init && git submodule update

update: mkdirs submodules docker-protocompile local-requirements playwright-install build-debug-images setup-hooks setup-cookiejar setup-filestorage

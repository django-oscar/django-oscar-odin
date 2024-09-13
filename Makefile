.PHONY: fail-if-no-virtualenv all install dev lint test black

all: install migrate collectstatic

fail-if-no-virtualenv:
ifndef VIRTUAL_ENV # check for a virtualenv in development environment
ifndef PYENVPIPELINE_VIRTUALENV # check for jenkins pipeline virtualenv
$(error this makefile needs a virtualenv)
endif
endif

ifndef PIP_INDEX_URL
PIP_INDEX_URL=https://pypi.org/simple
endif


dev: install
	pip install .[dev]

install: fail-if-no-virtualenv
	pip install --pre .[test]  --upgrade --upgrade-strategy=eager

migrate:
	./manage.py migrate --no-input

collectstatic:
	./manage.py collectstatic --no-input

lint: fail-if-no-virtualenv
	black --check oscar_odin/
	pylint oscar_odin/

test: fail-if-no-virtualenv install
	@coverage run --source='oscar_odin' ./manage.py test tests/
	@coverage report
	@coverage xml
	@coverage html

black:
	@black oscar_odin/
	@black tests/

clean: ## Remove files not in source control
	find . -type f -name "*.pyc" -delete
	rm -rf nosetests.xml coverage.xml htmlcov *.egg-info *.pdf dist violations.txt

package: clean
	rm -rf src/oscar/static/
	rm -rf dist/
	rm -rf build/
	poetry build

release: package ## Creates release
	twine upload dist/*

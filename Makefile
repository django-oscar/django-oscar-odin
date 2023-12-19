.PHONY: fail-if-no-virtualenv all install dev lint test black

all: install migrate loaddata collectstatic

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
	pip install .[test]

lint: fail-if-no-virtualenv
	black --check oscar_odin/
	pylint oscar_odin/

test: fail-if-no-virtualenv
	python3 manage.py makemigrations --check --dry-run
	@python3 manage.py test tests/

black:
	@black oscar_odin/
	@black tests/

ill:
	rm db.sqlite3
	cp klaas.sqlite3 db.sqlite3
	python3 manage.py migrate
	python3 manage.py test_illshit

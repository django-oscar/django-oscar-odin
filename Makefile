.PHONY: fail-if-no-virtualenv all install lint test black

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


install: fail-if-no-virtualenv
	pip install poetry
	poetry install

lint: fail-if-no-virtualenv
	black --check  oscar_odin/**/*.py
	pylint oscar_odin/

test: fail-if-no-virtualenv
	python3 runtests.py test tests.reverse.test_reallifecase

black:
	@black oscar_odin/
	@black tests/

ill:
	rm db.sqlite3
	cp klaas.sqlite3 db.sqlite3
	python3 runtests.py migrate
	python3 runtests.py test_illshit

PYTHON=python3
PYTHONPATH=./

name=rfc-http-validate
version=`python3 -c 'import importlib;a=importlib.import_module("setup");print(a.version)'`

.PHONY: version
version:
	echo $(version)

.PHONY: lint
lint:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m pylint $(name).py

.PHONY: black
black:
	PYTHONPATH=$(PYTHONPATH) black *.py

.PHONY: clean
clean:
	rm -rf build dist MANIFEST $(name).egg-info
	find . -type f -name \*.pyc -exec rm {} \;
	find . -d -type d -name __pycache__ -exec rm -rf {} \;

.PHONY: dist
dist: clean
	git tag $(name)-$(version)
	git push
	git push --tags origin
	$(PYTHON) setup.py sdist
	$(PYTHON) -m twine upload dist/*

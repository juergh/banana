all: ruff black

PY_FILES = db-cli insert-commit insert-patch-id banana/*.py

pylint:
	pylint --disable R0903,W0511 $(PY_FILES)

ruff:
	pyvenv ruff check $(PY_FILES)

black:
	pyvenv black -l 100 $(PY_FILES)

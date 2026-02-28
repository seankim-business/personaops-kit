PYTHON ?= python3
VENV ?= .venv

.PHONY: setup run test compile clean package

setup:
	$(PYTHON) -m venv $(VENV)
	. $(VENV)/bin/activate && pip install -r requirements.txt
	. $(VENV)/bin/activate && pip install -e .

run:
	. $(VENV)/bin/activate && uvicorn implementation.control_plane:app --reload --port 8081

test:
	. $(VENV)/bin/activate && pytest

compile:
	$(PYTHON) -m compileall implementation src

package:
	. $(VENV)/bin/activate && python -m pip install --upgrade build && python -m build

clean:
	rm -rf $(VENV) .pytest_cache implementation/__pycache__ implementation/tests/__pycache__ src/personaops_kit/__pycache__ tests_kit/__pycache__ build dist *.egg-info src/*.egg-info src/personaops_kit/*.egg-info

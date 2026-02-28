PYTHON ?= python3
VENV ?= .venv

.PHONY: setup run test compile clean

setup:
	$(PYTHON) -m venv $(VENV)
	. $(VENV)/bin/activate && pip install -r requirements.txt

run:
	. $(VENV)/bin/activate && uvicorn implementation.control_plane:app --reload --port 8081

test:
	. $(VENV)/bin/activate && pytest implementation/tests -q

compile:
	$(PYTHON) -m compileall implementation

clean:
	rm -rf $(VENV) .pytest_cache implementation/__pycache__ implementation/tests/__pycache__

PYTHON ?= python
PYTEST ?= pytest

.PHONY: test figures experiments all clean

test:
	PYTHONPATH=src $(PYTEST) -q

figures:
	PYTHONPATH=src $(PYTHON) experiments/generate_core_figures.py

experiments:
	PYTHONPATH=src $(PYTHON) experiments/controlled_benchmark.py
	PYTHONPATH=src $(PYTHON) experiments/tie_benchmark.py
	PYTHONPATH=src $(PYTHON) experiments/calibration_demo.py
	PYTHONPATH=src $(PYTHON) experiments/build_judgment_set.py
	PYTHONPATH=src $(PYTHON) experiments/stability_power_demo.py

all: test figures experiments

clean:
	rm -rf .pytest_cache build dist *.egg-info src/*.egg-info src/nwps.egg-info
	find . -type d -name __pycache__ -prune -exec rm -rf {} +

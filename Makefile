
all:
	@echo Done


test:
	$(info Running groot tests)
	PYTHONPATH=$$(pwd)/lib/groot:$$PYTHONPATH \
		python \
		lib/groot/groot/testing/run_tests.py \
		bin/groot



all:
	@echo Done


test:
	$(info Running groot tests)
	python lib/groot/testing/run_tests.py \
		bin/groot \
		lib/groot/testing/test_cases.yaml


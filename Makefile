.PHONY: build clean

CFLAGS='-w'

build:
	@echo "Building..."
	CFLAGS=$(CFLAGS) python3 setup.py build_ext -j $(shell getconf _NPROCESSORS_ONLN) --inplace

clean:
	@echo "Cleaning..."
	rm -rf pyboy_advance.egg-info
	rm -rf build
	rm -rf dist
	find pyboy_advance/ -type f -name "*.pyo" -delete
	find pyboy_advance/ -type f -name "*.pyc" -delete
	find pyboy_advance/ -type f -name "*.pyd" -delete
	find pyboy_advance/ -type f -name "*.so" -delete
	find pyboy_advance/ -type f -name "*.c" -delete
	find pyboy_advance/ -type f -name "*.h" -delete
	find pyboy_advance/ -type f -name "*.dll" -delete
	find pyboy_advance/ -type f -name "*.lib" -delete
	find pyboy_advance/ -type f -name "*.exp" -delete
	find pyboy_advance/ -type f -name "*.html" -delete
	find pyboy_advance/ -type f -name "*.build.py" -delete
	find pyboy_advance/ -type f -name "*.build.pyx" -delete
	find pyboy_advance/ -type f -name "*.build.pxd" -delete
	find pyboy_advance/ -type f -name "constants.pyx" -delete
	find pyboy_advance/ -type f -name "constants.pxd" -delete
	find pyboy_advance/ -type d -name "__pycache__" -delete

install:
	python3 -m pip install .

uninstall:
	python3 -m pip uninstall pyboy-advance

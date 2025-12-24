.PHONY: clean build check upload upload-test install-dev test lint format help

help:
	@echo "Yambot Development Commands:"
	@echo ""
	@echo "  make clean        - Remove build artifacts"
	@echo "  make build        - Build distribution packages"
	@echo "  make check        - Check package with twine"
	@echo "  make upload-test  - Upload to TestPyPI"
	@echo "  make upload       - Upload to PyPI"
	@echo "  make install-dev  - Install in development mode"
	@echo "  make test         - Run tests"
	@echo "  make lint         - Run linters"
	@echo "  make format       - Format code with black"
	@echo ""

clean:
	@echo "Cleaning build artifacts..."
	rm -rf build/ dist/ *.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	@echo "Done!"

build: clean
	@echo "Building package..."
	python -m build
	@echo "Done!"

check: build
	@echo "Checking package..."
	twine check dist/*
	@echo "Done!"

upload-test: check
	@echo "Uploading to TestPyPI..."
	twine upload --repository testpypi dist/*
	@echo "Done!"
	@echo ""
	@echo "Test installation:"
	@echo "pip install --index-url https://test.pypi.org/simple/ yambot-client"

upload: check
	@echo "Uploading to PyPI..."
	twine upload dist/*
	@echo "Done!"
	@echo ""
	@echo "Package published at: https://pypi.org/project/yambot-client/"

install-dev:
	@echo "Installing in development mode..."
	pip install -e .
	pip install -r requirements-dev.txt
	@echo "Done!"

test:
	@echo "Running tests..."
	pytest -v --cov=yambot --cov-report=term-missing
	@echo "Done!"

lint:
	@echo "Running linters..."
	flake8 yambot/ --max-line-length=100
	mypy yambot/ --ignore-missing-imports
	@echo "Done!"

format:
	@echo "Formatting code..."
	black yambot/ tests/
	@echo "Done!"

version:
	@echo "Current version:"
	@python -c "import tomli; print(tomli.load(open('pyproject.toml', 'rb'))['project']['version'])" 2>/dev/null || \
	@python -c "import toml; print(toml.load('pyproject.toml')['project']['version'])" 2>/dev/null || \
	@grep "version=" setup.py | head -1 | cut -d'"' -f2


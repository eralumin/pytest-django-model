help:
	@echo "Usage:"
	@echo "    make help        show this message"
	@echo "    make setup       create virtual environment and install dependencies"
	@echo "    make test        run the test suite"
	@echo "    make reformat    reformat python code"

setup:
	pip install pipenv
	pipenv install --dev --three

test:
	pipenv run -- pytest

reformat:
	black .
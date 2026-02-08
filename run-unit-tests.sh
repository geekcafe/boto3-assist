#!/bin/bash

python --version
python -m venv .unittest
source ./.unittest/bin/activate
which python


pip install --upgrade pip
pip install -r ./requirements.txt
pip install -r ./requirements.dev.txt
pip install -e .


echo "running unit tests with pytest"
pytest tests/unit/ -v --cov=src/boto3_assist --cov-report=term

if [ $? -eq 0 ]; then
    echo "Tests passed successfully"
else
    echo "Tests failed"
    exit 1
fi

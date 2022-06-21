#!/bin/bash
pip install --upgrade setuptools
pip install --upgrade wheel
pip install --upgrade twine
if ["$1" != "--upload"]; then
  python setup.py sdist bdist_wheel
fi
# Test PyPi
#twine upload --repository-url https://test.pypi.org/legacy/ dist/*
# Prod PyPi
twine upload dist/*

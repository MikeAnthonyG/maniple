#!/bin/bash

# Test Dlib: run on Docker container.

set -o pipefail

BASE_PATH=/app

# Get Python version (either 2.7 or 3.6).
PYTHON_VERSION=$(python -c "import sys;t='{v[0]}.{v[1]}'.format(v=list(sys.version_info[:2]));sys.stdout.write(t)";)

cd $BASE_PATH

tar -xzvf "${BASE_PATH}/python${PYTHON_VERSION}-dlib-19.8.tar.gz"

pip install scikit-image

LD_LIBRARY_PATH=$BASE_PATH/lib:$LD_LIBRARY_PATH \
PYTHONPATH=$BASE_PATH:$PYTHONPATH \
python "${BASE_PATH}/test/test_dlib.py"

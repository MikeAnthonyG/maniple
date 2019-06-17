#!/bin/bash

if [ $# -eq 0 ] || ([ ${1} != "2.7" ] && [ ${1} != "3.6" ]); then
  echo "Python version required (either 2.7 or 3.6)"
  exit 1
fi

PYTHON_VERSION=${1}

docker run -v$(pwd):/app -it --rm "lambci/lambda:build-python${PYTHON_VERSION}" /app/_test_dlib.sh

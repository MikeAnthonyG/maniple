#!/bin/bash

set -o pipefail

BASE_PATH=/app

BUILD_PATH="$BASE_PATH/_build"

VERSION=19.8

# Note: Boost 1.66 doesn't work with cmake's FindBoost. https://gitlab.kitware.com/cmake/cmake/issues/17575
BOOST_MINOR_VERSION=65

# Get Python version (either 2.7 or 3.6).
PYTHON_VERSION=$(python -c "import sys;t='{v[0]}.{v[1]}'.format(v=list(sys.version_info[:2]));sys.stdout.write(t)";)

BOOST_PYTHON_DIR="$BUILD_PATH/boost_python${PYTHON_VERSION}"

# Lambda docker puts Python libraries in a weird place.
if [[ $PYTHON_VERSION == 3* ]]; then
    PYTHON_LIBRARY_DIR="/var/lang/include/python${PYTHON_VERSION}m"
else
    PYTHON_LIBRARY_DIR="/usr/include/python2.7"
fi

function install_deps {
    echo "Installing dependancies."

    pip install numpy scikit-image
    # Have to run it twice to ensure it always works.
    for run in {1..2}
    do
        yum install -y cmake gcc-c++ wget blas-devel lapack-devel git openblas.x86_64 openblas-devel.x86_64
    done
     
    # Scikit image for testing and Numpy for the Dlib installation.
    pip install scikit-image numpy
}

function create_build_path {
    echo "Creating build path."

    if [ ! -d "$BUILD_PATH" ]; then
        mkdir "$BUILD_PATH"
    fi
}

function install_patchelf {
    echo "Configuring Patchelf."

    if [  -f "$BUILD_PATH/patchelf-0.8.tar.gz" ]; then
        wget --no-check-certificate -P "$BUILD_PATH" http://flydata-rpm.s3-website-us-east-1.amazonaws.com/patchelf-0.8.tar.gz
        tar xxvf "$BUILD_PATH/patchelf-0.8.tar.gz" -C "$BUILD_PATH"
    fi
    
    cd "$BUILD_PATH/patchelf-0.8" && ./configure && make && make install
}

function build_boost_python {
    if [ -f "$BOOST_PYTHON_DIR/lib/*so" ]; then
	echo "Boost Python seems to exist. Not building it."
        return
    fi

    echo "Building Boost.Python."

    if [ ! -f "$BUILD_PATH/boost_1_${BOOST_MINOR_VERSION}_0.tar.bz2" ]; then
        wget --no-check-certificate -P "$BUILD_PATH" \
             https://dl.bintray.com/boostorg/release/1.${BOOST_MINOR_VERSION}.0/source/boost_1_${BOOST_MINOR_VERSION}_0.tar.bz2
    fi
    
    if [ -d "$BUILD_PATH/boost_1_${BOOST_MINOR_VERSION}_0" ]; then
        rm -r "$BUILD_PATH/boost_1_${BOOST_MINOR_VERSION}_0"
    fi

    tar xvf "$BUILD_PATH/boost_1_${BOOST_MINOR_VERSION}_0.tar.bz2" -C "$BUILD_PATH"
    
    if [ ! -d "$BOOST_PYTHON_DIR" ]; then
        mkdir $BOOST_PYTHON_DIR
    fi

    # Hack to work around https://svn.boost.org/trac10/ticket/11120#comment:21
    if [[ $PYTHON_LIBRARY_DIR == *m ]]; then
        ln -s ${PYTHON_LIBRARY_DIR} ${PYTHON_LIBRARY_DIR%?}
    fi
    
    CPLUS_INCLUDE_PATH="$CPLUS_INCLUDE_PATH:$PYTHON_LIBRARY_DIR"
    
    cd $BUILD_PATH/boost_1_${BOOST_MINOR_VERSION}_0/
    ./bootstrap.sh --with-libraries=python --prefix=$BOOST_PYTHON_DIR
    ./b2 install
}

function build_dlib {
    echo "Building Dlib."

    if [ ! -d "${BUILD_PATH}/dlib" ]; then
        cd  "${BUILD_PATH}" && git clone https://github.com/davisking/dlib.git
    fi
    
    cd "${BUILD_PATH}/dlib"
    git pull
    git checkout -f "v${VERSION}"
    
    if [ -d "${BUILD_PATH}/dlib/build" ]; then
        rm -r "${BUILD_PATH}/dlib/build"
    fi

    mkdir "${BUILD_PATH}/dlib/build"
    
    cd "${BUILD_PATH}/dlib/build"

    PYTHON3_BOOL="OFF"
    if [[ $PYTHON_VERSION == 3* ]]; then
      PYTHON3_BOOL="ON"
    fi

    CPLUS_INCLUDE_PATH="$CPLUS_INCLUDE_PATH:$PYTHON_LIBRARY_DIR"

    cmake -DPYTHON3:BOOL=$PYTHON3_BOOL \
          -DBOOST_ROOT=/app/_build/boost_1_${BOOST_MINOR_VERSION}_0 \
          -DBOOST_LIBRARYDIR=$BOOST_PYTHON_DIR/lib \
          -DUSE_SSE4_INSTRUCTIONS:BOOL=ON ../tools/python
    cmake --build . --config Release --target install
}

function package_dlib {
    echo "Packaging Dlib."

    if [ -d "$BASE_PATH/dlib" ]; then
        rm -r $BASE_PATH/dlib
    fi


    if [ -d "$BASE_PATH/lib" ]; then
        rm -r $BASE_PATH/lib
    fi

    mkdir $BASE_PATH/dlib
    mkdir $BASE_PATH/lib
    
    cp -v $BUILD_PATH/dlib/build/dlib.so $BASE_PATH/dlib/__init__.so
    cp -v $BOOST_PYTHON_DIR/lib/libboost_python*.so.*.0 $BASE_PATH/dlib/
    
    touch $BASE_PATH/dlib/__init__.py
    patchelf --set-rpath '$ORIGIN' $BASE_PATH/dlib/__init__.so

    cp -v /usr/lib64/libopenblas.so.0 $BASE_PATH/lib/
    cp -v /usr/lib64/libgfortran.so.3 $BASE_PATH/lib/
    cp -v /usr/lib64/libquadmath.so.0 $BASE_PATH/lib/
}

function test_dlib {
    echo "Testing Dlib."

    LD_LIBRARY_PATH=$BASE_PATH/lib:$LD_LIBRARY_PATH \
    PYTHONPATH=$BASE_PATH:$PYTHONPATH \
    python "${BASE_PATH}/test/test_dlib.py"
    
    if [ ! $? -eq 0 ]; then
        echo "Tests failing. Not creating archive."
        exit 1
    fi
}

function archive_dlib {
    echo "Creating archive."

     if [ -f "$BASE_PATH/python${PYTHON_VERSION}-dlib-${VERSION}.tar.gz" ]; then
       rm $BASE_PATH/python${PYTHON_VERSION}-dlib-${VERSION}.tar.gz
     fi
     
     cd $BASE_PATH && tar -zcvf python${PYTHON_VERSION}-dlib-${VERSION}.tar.gz dlib lib
}

create_build_path
install_deps
install_patchelf
build_boost_python
build_dlib
package_dlib
test_dlib
archive_dlib

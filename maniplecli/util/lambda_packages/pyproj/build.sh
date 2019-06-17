#!/bin/bash

sudo yum -y update
sudo yum -y install python27-devel python27-pip gcc gcc-c++

sudo pip install virtualenv

# proj.4 4.9.2
wget https://github.com/OSGeo/proj.4/archive/4.9.2.tar.gz
tar xzvf 4.9.2.tar.gz && cd proj.4-4.9.2/
./configure
make
make install

cd $HOME

virtualenv env
source env/bin/activate
pip install --upgrade pip

pip install pyproj
TARGET_DIR=$HOME/packaged
mkdir -p ${TARGET_DIR}
cd $HOME/env/lib64/python2.7/site-packages
tar -zcvf ${TARGET_DIR}/pyproj.4-4.9.2.tar.gz *
deactivate

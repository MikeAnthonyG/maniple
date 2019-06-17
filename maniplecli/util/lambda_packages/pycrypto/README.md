# pycrypto

    sudo yum groupinstall "Development Tools"
    wget https://pypi.python.org/packages/60/db/645aa9af249f059cc3a368b118de33889219e0362141e75d4eaf6f80f163/pycrypto-2.6.1.tar.gz
    tar xvf pycrypto-2.6.1.tar.gz
    cd pycrypto-2.6.1
    python setup.py build
    cd build/lib.linux-x86_64-2.7
    tar -czvf pycrypto-2.6.1.tar.gz ./*

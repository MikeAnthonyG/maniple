    
#!/usr/bin/env python

import io
import re
import os
from setuptools import setup, find_packages


def read(*filenames, **kwargs):
    encoding = kwargs.get('encoding', 'utf-8')
    sep = kwargs.get('sep', os.linesep)
    buf = []
    for filename in filenames:
        with io.open(filename, encoding=encoding) as f:
            buf.append(f.read())
    return sep.join(buf)


def read_requirements(req='base.txt'):
    content = read(os.path.join('requirements', req))
    return [line for line in content.split(os.linesep)
            if not line.strip().startswith('#')]

cmd_name = "maniple"

setup(
    name='maniple',
    version=1.0,
    description='Maniple: Serverless framework for Terraform ',
    long_description=read('README.md'),
    long_description_content_type='text/markdown',
    author='Mike',
    install_package_data=True,
    packages=find_packages(),
    keywords="maniple",
    # Support Python 2.7 and 3.6 or greater
    python_requires='>=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*, !=3.4.*, !=3.5.*',
    entry_points={
        'console_scripts':[
            'maniple=maniplecli.cli.main:cli'
        ]
    },
    install_requires=read_requirements('base.txt'),
    include_package_data=True,
    test_suite="tests",
)
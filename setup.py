from __future__ import division, print_function
import os
import sys
from setuptools import setup, find_packages


PKG_NAME = 'limix_ext'
VERSION  = '0.1.2'

try:
    import numpy as np
except ImportError:
    print("Error: numpy package couldn't be found." +
          " Please, install it so I can proceed.")
    sys.exit(1)

try:
    import scipy
except ImportError:
    print("Error: scipy package couldn't be found."+
          " Please, install it so I can proceed.")
    sys.exit(1)

try:
    import cython
except ImportError:
    print("Error: cython package couldn't be found."+
          " Please, install it so I can proceed.")
    sys.exit(1)

try:
    import rpy2
except ImportError:
    print("Error: rpy2 package couldn't be found."+
          " Please, install it so I can proceed.")
    sys.exit(1)

def get_test_suite():
    from unittest import TestLoader
    return TestLoader().discover(PKG_NAME)

def write_version():
    cnt = """
# THIS FILE IS GENERATED FROM %(package_name)s SETUP.PY
version = '%(version)s'
"""
    filename = os.path.join(PKG_NAME, 'version.py')
    a = open(filename, 'w')
    try:
        a.write(cnt % {'version': VERSION,
                       'package_name': PKG_NAME.upper()})
    finally:
        a.close()

def get_version_filename(package_name):
    filename = os.path.join(package_name, 'version.py')
    return filename

def setup_package():
    src_path = os.path.dirname(os.path.abspath(sys.argv[0]))
    old_path = os.getcwd()
    os.chdir(src_path)
    sys.path.insert(0, src_path)

    write_version()

    install_requires = ['limix_util', 'limix_tool', 'fastlmm']
    setup_requires = []

    metadata = dict(
        name=PKG_NAME,
        maintainer = "Limix Developers",
        version=VERSION,
        maintainer_email="horta@ebi.ac.uk",
        test_suite='setup.get_test_suite',
        packages=find_packages(),
        license="BSD",
        url='http://pmbio.github.io/limix/',
        install_requires=install_requires,
        setup_requires=setup_requires,
        zip_safe=False
    )

    try:
        setup(**metadata)
    finally:
        del sys.path[0]
        os.chdir(old_path)

if __name__ == '__main__':
    setup_package()

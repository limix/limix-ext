from __future__ import absolute_import

from pkg_resources import get_distribution

__version__ = get_distribution('limix-ext').version

from . import macau

def test():
    import os
    p = __import__('limix_ext').__path__[0]
    src_path = os.path.abspath(p)
    old_path = os.getcwd()
    os.chdir(src_path)

    try:
        return_code = __import__('pytest').main(['-q'])
    finally:
        os.chdir(old_path)

    if return_code == 0:
        print("Congratulations. All tests have passed!")

    return return_code

# -*- coding: utf-8 -*-
"""
    Setup file for snakehelper.
    Use setup.cfg to configure your project.

    This file was generated with PyScaffold 3.2.3.
    PyScaffold helps you to put up the scaffold of your new Python project.
    Learn more under: https://pyscaffold.org/
"""
import sys

from packaging.version import Version, InvalidVersion
from setuptools import setup

try:
    from setuptools import __version__ as setuptools_version
    if Version(setuptools_version) < Version("38.3"):
        raise InvalidVersion
except InvalidVersion:
    print("Error: version of setuptools is too old (<38.3)!")
    sys.exit(1)


if __name__ == "__main__":
    setup(use_pyscaffold=True)

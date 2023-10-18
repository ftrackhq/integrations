# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import os


def get_version():
    '''Return version string for this package'''
    package_name = os.path.basename(os.path.dirname(__file__))
    try:
        from importlib.metadata import version

        return version(package_name)
    except ImportError:
        # Running on pre-3.8 Python; use importlib-metadata package
        from pkg_resources import get_distribution

        return get_distribution(package_name).version


__version__ = get_version()

# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import os


def get_version():
    '''Return version string for this package'''
    package_name = os.path.basename(os.path.dirname(__file__))
    try:
        from importlib.metadata import version

        result = version(package_name)
    except ImportError:
        # Running on pre-3.8 Python; use importlib-metadata package
        from pkg_resources import get_distribution

        result = get_distribution(package_name).version
    if result == "0.0.0":
        # Running from sources, fetch version from pyproject.toml
        import toml

        path_package = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "pyproject.toml",
        )
        version = toml.load(path_package)["tool"]["poetry"]["version"]
    return version


__version__ = get_version()

# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack
import os


def get_version(package_name, package_path):
    '''Return version string for *package_name* at *package_path*'''
    result = '0.0.0'
    try:
        from importlib.metadata import version

        result = version(package_name)
    except ImportError:
        try:
            # Running on pre 3.8 Python; use importlib-metadata package
            from pkg_resources import get_distribution

            result = get_distribution(package_name).version
        except:
            pass
    if result == '0.0.0':
        # Probably running from sources or not able to resolv, fetch version
        # from pyproject.toml
        import toml

        path_toml = os.path.join(
            package_path,
            "pyproject.toml",
        )
        if os.path.exists(path_toml):
            result = toml.load(path_toml)["tool"]["poetry"]["version"]

    return result

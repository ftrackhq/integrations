# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import os


def get_version(package_name, package_path):
    '''Return version string for *package_name* at *package_path*'''
    result = None
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
    if not result:
        # Probably running as Connect plugin not properly detected in sys path
        result = get_connect_plugin_version(package_path)

    if not result:
        # Probably running from sources or not able to resolv, fetch version
        # from pyproject.toml
        import toml

        path_toml = os.path.join(
            package_path,
            "pyproject.toml",
        )
        if os.path.exists(path_toml):
            result = toml.load(path_toml)["tool"]["poetry"]["version"]

    return result or '0.0.0'


def get_connect_plugin_version(connect_plugin_path):
    '''Return Connect plugin version string for *connect_plugin_path*'''
    __version__ = None
    path_version_file = os.path.join(connect_plugin_path, '__version__.py')
    if os.path.isfile(path_version_file):
        with open(path_version_file) as f:
            exec(f.read())
    return __version__

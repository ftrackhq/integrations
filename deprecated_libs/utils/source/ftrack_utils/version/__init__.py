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


def get_connect_plugin_version(connect_plugin_path):
    '''Return Connect plugin version string for *connect_plugin_path*'''
    result = None
    path_version_file = os.path.join(connect_plugin_path, '__version__.py')
    if not os.path.isfile(path_version_file):
        raise FileNotFoundError
    with open(path_version_file) as f:
        for line in f.readlines():
            if line.startswith('__version__'):
                result = line.split('=')[1].strip().strip("'")
                break
    if not result:
        raise Exception(
            "Can't extract version number from {}. "
            "\n Make sure file is valid.".format(path_version_file)
        )
    return result

# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack
import os
import re
import tomllib

from packaging.version import InvalidVersion, Version


#: Default expression to match version component of executable path.
#: Will match last set of numbers in string where numbers may contain a digit
#: followed by zero or more digits, periods, or the letters 'a', 'b', 'c' or 'v'
#: E.g. /path/to/x86/some/application/folder/v1.8v2b1/app.exe -> 1.8v2b1
DEFAULT_VERSION_EXPRESSION = re.compile(r"(?P<version>\d[\d.vabc]*?)[^\d]*$")


def parse_application_version(value):
    """Parse application version into a comparable Version instance.

    Some discovered app paths include non-standard markers such as "v"
    inside the version string (for example: "1.8v2b1").
    """
    candidates = [value, value.replace("v", ".")]
    for candidate in candidates:
        try:
            return Version(candidate)
        except InvalidVersion:
            continue

    return Version("0")


def resolve_marketing_version(loose_version, version_year_offset, path):
    """Resolve a marketing version from an internal version.

    If *version_year_offset* is set, converts the major component of
    *loose_version* to a marketing year (e.g. major 27 + 1999 = 2026).

    If *path* contains "(Beta)", returns a " (beta)" suffix.

    Returns a tuple of (*resolved_version*, *beta_suffix*) where
    *beta_suffix* is either " (beta)" or "".
    """
    if version_year_offset is not None and loose_version > Version("0"):
        year = loose_version.major + version_year_offset
        loose_version = Version(str(year))

    beta_suffix = " (beta)" if "(Beta)" in path else ""

    return loose_version, beta_suffix


def get_version(package_name, package_path):
    """Return version string for *package_name* at *package_path*"""
    result = "0.0.0"
    try:
        from importlib.metadata import version

        result = version(package_name)
    except Exception:
        path_toml = os.path.join(package_path, "pyproject.toml")
        if os.path.exists(path_toml):
            with open(path_toml, "rb") as stream:
                result = tomllib.load(stream)["project"]["version"]

    return result


def get_connect_plugin_version(connect_plugin_path):
    """Return Connect plugin version string for *connect_plugin_path*"""
    result = None
    path_version_file = os.path.join(connect_plugin_path, "__version__.py")
    if not os.path.isfile(path_version_file):
        raise FileNotFoundError
    with open(path_version_file) as f:
        for line in f.readlines():
            if line.startswith("__version__"):
                result = line.split("=")[1].strip().strip("'")
                break
    if not result:
        raise Exception(
            "Can't extract version number from {}. "
            "\n Make sure file is valid.".format(path_version_file)
        )
    return result

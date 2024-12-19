# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import os
import logging
import re
import sys
import requests
import glob

import platformdirs
from packaging.version import parse
from packaging.specifiers import SpecifierSet


from ftrack_connect import (
    INCOMPATIBLE_PLUGINS,
    DEPRECATED_PLUGINS,
)

logger = logging.getLogger(__name__)


def get_default_plugin_directory():
    return platformdirs.user_data_dir('ftrack-connect-plugins', 'ftrack')


PLUGIN_DIRECTORIES = [
    os.path.expandvars(p)
    for p in os.getenv(
        'FTRACK_CONNECT_PLUGIN_PATH', get_default_plugin_directory()
    ).split(os.pathsep)
]


def get_plugins_from_path(plugin_directory):
    '''Return folders from the given *connect_plugin_path* directory'''
    # Filter out files and hidden items.
    plugins = [
        f
        for f in os.listdir(plugin_directory)
        if not f.startswith('.')
        and os.path.isdir(os.path.join(plugin_directory, f))
    ]
    return plugins


def get_plugin_data(plugin_path):
    '''
    Return data from the provided *plugin_path*.

    Valid Plugin names:
    "plugin-24.0.0",
    "my-plugin-24.0.0rc1",  # or b, a etc...
    "ftrack-my-plugin-24.0.0",
    "ftrack-my-plugin-something-else-24.0.0",
    "ftrack-my-plugin-24.4.1-mac.zip",
    "ftrack-my-plugin-24.4.1-custom_platform.zip",
    "ftrack-my-plugin-24.4.1.zip",
    "ftrack-my-plugin-24.4.1.tar.gz",
    "ftrack-my-plugin-24.4.1-linux.tar.gz",
    "plugin-24.4.1.zip",
    "plugin-24.0.zip",

    Deprecated Names:
    "my_plugin"
    "my-plugin"
    '''
    plugin_re = re.compile(
        r'(?P<name>.+?)-(?P<version>\d+\.\d+(?:\.\d+)?(?:[a-zA-Z]+\d+)?)(?:-(?P<platform>\w+))?(?P<extension>(?:\.\w+)+)?$'
    )

    plugin_name = os.path.basename(plugin_path)
    match = plugin_re.match(plugin_name)
    if match:
        data = match.groupdict()
    else:
        # Check if it's a legacy action or custom plugin
        deprecated_plugin_re = re.compile(r'^(?P<name>[a-zA-Z0-9_\-]+)$')
        deprecated_match = deprecated_plugin_re.match(plugin_name)

        suggested_valid_name = suggest_valid_name(plugin_name)

        if not deprecated_match:
            logger.warning(
                f"The provided plugin path can't be recognized: {plugin_path}. "
                f"Please make sure that plugin name matches the following format: "
                f"my-plugin-1.0.0. "
                f"\n Current plugin name: {plugin_name}, "
                f"suggested plugin name:{suggested_valid_name}"
            )
            return False
        logger.warning(
            f"The provided plugin name would be deprecated soon, please use "
            f"dash instead of underscore and version the plugin for further "
            f"compatibility. "
            f"Example of a valid plugin name: my-custom-plugin-1.0.0. \n "
            f"Current name: {plugin_name}, "
            f"suggested plugin name:{suggested_valid_name}"
        )
        data = deprecated_match.groupdict()
        data['version'] = "0.0.0"

    data['path'] = plugin_path
    if not data.get('platform'):
        data['platform'] = 'noarch'
    if data.get('extension'):
        if data['extension'] != '.zip':
            logger.warning(
                f"Sorry, we only support .zip extensions for now, ignoring plugin: {plugin_path}"
            )
            return False
    data['incompatible'] = is_incompatible_plugin(data)
    data['deprecated'] = is_deprecated_plugin(data)
    return data


def suggest_valid_name(input_name):
    '''
    Suggest valid plugin name
    '''
    # Normalize underscores to hyphens
    normalized_name = re.sub(r'[_]+', '-', input_name)
    normalized_name = re.sub(r'[-]+', '-', normalized_name)

    # Check if the version and possibly platform/extension are already correct
    if not re.search(
        r'\d+\.\d+(\.\d+)?([a-zA-Z]+\d+)?(-\w+)?(\.\w+)?$', normalized_name
    ):
        # Append '-0.0.0' if no version pattern is found
        normalized_name = re.sub(r'(\.\w+)?$', r'-0.0.0\1', normalized_name)

    return normalized_name


def is_incompatible_plugin(plugin_data):
    '''Return true if plugin from *plugin_data* is incompatible with Connect
    and cannot be loaded'''
    for incompatible_plugin in INCOMPATIBLE_PLUGINS:
        if plugin_data['name'].lower() == incompatible_plugin['name']:
            parsed_plugin_version = parse(plugin_data['version'])

            # Create the specifier compatible with pre-releases
            incompatible_specifier = SpecifierSet(
                incompatible_plugin['version'], prereleases=True
            )

            if parsed_plugin_version not in incompatible_specifier:
                logger.debug(
                    f"Version {plugin_data['version']} is compatible."
                )
                break
            logger.debug(
                f"{plugin_data['name']} version {plugin_data['version']} is "
                f"incompatible"
            )
            return True
    # Don't check anything else if path is zip file.
    if plugin_data['path'].endswith('.zip'):
        return False
    # Check hook folder exists
    connect_hook = os.path.join(plugin_data['path'], 'hook')
    if not os.path.exists(connect_hook) or not glob.glob(
        f'{connect_hook}/*.py'
    ):
        logger.debug(
            f"{plugin_data['name']} version {plugin_data['version']} is "
            f"incompatible, hook folder or hook python file is missing"
        )
        return True

    return False


def is_deprecated_plugin(plugin_data):
    '''Return true if plugin from *plugin_data* is deprecated within Connect,
    but still can be loaded'''
    for deprecated_plugin in DEPRECATED_PLUGINS:
        if plugin_data['name'].lower() == deprecated_plugin['name']:
            parsed_plugin_version = parse(plugin_data['version'])

            # Create the specifier compatible with pre-releases
            deprecated_specifier = SpecifierSet(
                deprecated_plugin['version'], prereleases=True
            )

            if parsed_plugin_version not in deprecated_specifier:
                logger.debug(
                    f"Version {plugin_data['version']} is compatible."
                )
                return False
            logger.debug(
                f"{plugin_data['name']} version {plugin_data['version']} is "
                f"deprecated"
            )
            return True
    return False


def get_plugin_json_url_from_environment():
    '''Return plugin json url from environment variable'''
    return os.environ.get('FTRACK_CONNECT_JSON_PLUGINS_URL')


def check_major_version(version, major_version_start=24):
    match = re.match(r'v(\d+)\.\d+\.\d+.*', version)
    no_path_match = re.match(r'v(\d+)\.\d+\.*', version)
    if match:
        major_version = int(match.group(1))
        return major_version >= major_version_start
    elif no_path_match:
        # Without patch
        major_version = int(no_path_match.group(1))
        return major_version >= major_version_start
    else:
        return False


def fetch_github_releases(url, latest=True, prereleases=False):
    '''Read github releases and return a list of releases, and
    list of assets as value. If *latest* is True, only the latest
    version of each plugin is returned. If *prereleases* is True,
    prereleases are included in the result.'''

    logger.debug(
        f'Fetching releases from: {url} (pre-releases: {prereleases})'
    )

    response = requests.get(f"{url}/releases")
    if response.status_code != 200:
        logger.error(f'Failed to fetch releases from {url}')
        return []

    data = {}

    # Expect list of releases
    for release in response.json():
        tag_name = release.get('tag_name')
        if not tag_name:
            continue
        if release.get('draft') is True:
            logger.debug(f'   Skipping draft release: {tag_name}')
            continue

        logger.debug(f'Found release: {tag_name}')

        # Check if it is a Connect release
        package = tag_name.split('/')[0]
        version = tag_name.split('/')[-1]
        if not check_major_version(version):
            # TODO: solve the issue when library major version is catching up to
            #  Connect major version
            logger.debug(
                f'   Not a Connect release on YY.m.p|YY.mp format: {tag_name} \n '
                f'Minimum compatible major version is 24.X.X'
            )
            continue

        if not prereleases and release.get('prerelease') is True:
            logger.debug(f'   Skipping pre-release: {tag_name}')
            continue
        elif prereleases and not release.get('prerelease'):
            logger.debug(f'   Skipping release: {tag_name}')
            continue
        release_data = {
            'id': release['id'],
            'url': release['html_url'],
            'tag': tag_name,
            'package': package,
            'version': version,
            'prerelease': release.get("prerelease"),
            'body': release["body"] or "",
            'assets': [],
        }
        assets = release.get('assets', [])
        url = None
        for asset in assets:
            logger.debug(
                f"   Found asset: {asset['name']}, {asset['browser_download_url']}"
            )

            release_data['assets'].append(
                {'name': asset['name'], 'url': asset['browser_download_url']}
            )

            # Evaluate if we can use this asset

            base, ext = os.path.splitext(asset['name'])

            if ext.lower() != '.zip':
                continue

            # Check platform
            parts = base.split('-')
            if parts[-1].lower() in ['windows', 'mac', 'linux']:
                # Platform dependent plugin, have to match our platform
                platform = get_platform_identifier()
                if parts[-1].lower() != platform:
                    # Not our platform
                    continue

            logger.debug(
                f"   Supplying asset: {asset['name']}, {asset['browser_download_url']}"
            )
            url = asset['browser_download_url']

        if url:
            logger.debug(f'Supplying release: {tag_name}')
            release_data['url'] = url
            if not latest or package not in data:
                data[package] = release_data
            else:
                current_version = data[package]['tag'].rsplit('/', 1)[1][1:]
                if parse(current_version) < parse(version):
                    # This version is higher
                    data[package] = release_data

    result = []
    for release in list(data.values()):
        result.append(release)

    return result


def get_platform_identifier():
    '''Return platform identifier for current platform, used in plugin package
    filenames'''
    if sys.platform.startswith('win'):
        platform = 'windows'
    elif sys.platform.startswith('darwin'):
        platform = 'mac'
    elif sys.platform.startswith('linux'):
        platform = 'linux'
    else:
        platform = sys.platform
    return platform


def create_target_plugin_directory(directory):
    if not os.path.exists(directory):
        # Create directory if not existing.
        try:
            os.makedirs(directory)
        except Exception as e:
            raise Exception(
                f"Couldn't create the target plugin directory: {e}"
            )

    return directory

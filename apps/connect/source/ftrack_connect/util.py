# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import os
import subprocess
import sys
import logging
import re
import requests
import glob

import platformdirs
from packaging.version import parse
from packaging.specifiers import SpecifierSet

from ftrack_connect.qt import QtCore
from ftrack_connect import INTEGRATIONS_REPO

from ftrack_connect import (
    INCOMPATIBLE_PLUGINS,
    DEPRECATED_PLUGINS,
)

from ftrack_utils.json import read_json_file, write_json_file

logger = logging.getLogger(__name__)

# Default plugin directory


def get_default_plugin_directory():
    return platformdirs.user_data_dir('ftrack-connect-plugins', 'ftrack')


PLUGIN_DIRECTORIES = [
    os.path.expandvars(p)
    for p in os.getenv(
        'FTRACK_CONNECT_PLUGIN_PATH', get_default_plugin_directory()
    ).split(os.pathsep)
]


def open_directory(path):
    '''Open a filesystem directory from *path* in the OS file browser.

    If *path* is a file, the parent directory will be opened. Depending on OS
    support the file will be pre-selected.

    .. note::

        This function does not support file sequence expressions. The path must
        be either an existing file or directory that is valid on the current
        platform.

    '''
    if os.path.isfile(path):
        directory = os.path.dirname(path)
    else:
        directory = path

    if sys.platform == 'win32':
        # In order to support directories with spaces, the start command
        # requires two quoted args, the first is the shell title, and
        # the second is the directory to open in. Using string formatting
        # here avoids the auto-escaping that python introduces, which
        # seems to fail...
        subprocess.Popen('start "" "{0}"'.format(directory), shell=True)

    elif sys.platform == 'darwin':
        if os.path.isfile(path):
            # File exists and can be opened with a selection.
            subprocess.Popen(['open', '-R', path])

        else:
            subprocess.Popen(['open', directory])

    else:
        subprocess.Popen(['xdg-open', directory])


# Invoke function in main UI thread.
# Taken from:
# http://stackoverflow.com/questions/10991991/pyside-easier-way-of-updating-gui-from-another-thread/12127115#12127115


class InvokeEvent(QtCore.QEvent):
    '''Event.'''

    EVENT_TYPE = QtCore.QEvent.Type(QtCore.QEvent.registerEventType())

    def __init__(self, fn, *args, **kwargs):
        '''Invoke *fn* in main thread.'''
        QtCore.QEvent.__init__(self, InvokeEvent.EVENT_TYPE)
        self.fn = fn
        self.args = args
        self.kwargs = kwargs


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


def get_plugin_data(plugin_path):
    '''Return data from the provided *plugin_path*.'''
    plugin_re = re.compile('(?P<name>(([A-Za-z-3-4]+)))-(?P<version>(\w.+))')

    plugin_name = os.path.basename(plugin_path)
    match = plugin_re.match(plugin_name)
    if match:
        data = match.groupdict()
    else:
        logger.warning(
            f"The provided plugin path can't be recognized: {plugin_path}"
        )
        return False

    data['path'] = plugin_path
    data['platform'] = 'noarch'
    if data['version'].lower().endswith('.zip'):
        # pop zip extension from the version.
        # TODO: refine regex to catch extension
        data['version'] = data['version'][:-4]
        parts = data['version'].split('-')
        if len(parts) > 1:
            data['version'] = parts[0]
            data['platform'] = parts[-1]
    data['incompatible'] = is_incompatible_plugin(data)
    data['deprecated'] = is_deprecated_plugin(data)
    return data


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


class Invoker(QtCore.QObject):
    '''Invoker.'''

    def event(self, event):
        '''Call function on *event*.'''
        event.fn(*event.args, **event.kwargs)

        return True


_invoker = Invoker(None)


def invoke_in_qt_main_thread(fn, *args, **kwargs):
    '''
    Invoke function *fn* with arguments, if not running in the main thread.

    TODO: Use ftrack QT util instead
    '''
    if QtCore.QThread.currentThread() is _invoker.thread():
        fn(*args, **kwargs)
    else:
        QtCore.QCoreApplication.postEvent(
            _invoker, InvokeEvent(fn, *args, **kwargs)
        )


def qt_main_thread(func):
    '''Decorator to ensure the function runs in the QT main thread.
    TODO: Use ftrack QT util instead
    '''

    def wrapper(*args, **kwargs):
        return invoke_in_qt_main_thread(func, *args, **kwargs)

    return wrapper


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


def fetch_github_releases(latest=True, prereleases=False):
    '''Read github releases and return a list of releases, and
    list of assets as value. If *latest* is True, only the latest
    version of each plugin is returned. If *prereleases* is True,
    prereleases are included in the result.'''

    logger.debug(f'Fetching releases from: {INTEGRATIONS_REPO}')

    response = requests.get(f"{INTEGRATIONS_REPO}/releases")
    if response.status_code != 200:
        logger.error(f'Failed to fetch releases from {INTEGRATIONS_REPO}')
        return []

    data = []

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
            logger.debug(f'   Skipping prerelease: {tag_name}')
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
            data.append(release_data)

    if latest:
        # Only provide the latest version

        data.sort(key=lambda x: x['tag'], reverse=True)

        result = []
        for item in data:
            if (
                not result
                or item['tag'].rsplit('/', 1)[0]
                != result[-1]['tag'].rsplit('/', 1)[0]
            ):
                result.append(item)
    else:
        result = data

    return result


def get_connect_prefs_file_path():
    '''Return Path of the prefs.json file'''
    prefs_file = os.path.join(
        platformdirs.user_data_dir('ftrack-connect', 'ftrack'),
        'prefs.json',
    )
    return prefs_file


def get_connect_preferences():
    '''Return the content of the prefs.json file'''
    prefs_file = get_connect_prefs_file_path()

    return read_json_file(prefs_file)


def write_connect_prefs_file_path(content):
    '''Write the content of of the prefs.json file'''
    prefs_file = get_connect_prefs_file_path()

    return write_json_file(prefs_file, content)

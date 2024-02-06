# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import os
import subprocess
import sys
import logging
import re
import requests

import platformdirs
import json

from ftrack_connect.qt import QtCore
from ftrack_connect import INTEGRATIONS_REPO

from ftrack_connect import (
    INCOMPATIBLE_PLUGINS,
    CONFLICTING_PLUGINS,
    DEPRECATED_PLUGINS,
)

from ftrack_utils.json import read_json_file, write_json_file

logger = logging.getLogger(__name__)


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


def is_loadable_plugin(plugin_path):
    '''Return True if plugin @ *plugin_path* is able to load in current version
    of Connect'''
    return not (
        is_conflicting_plugin(plugin_path)
        or is_incompatible_plugin(plugin_path)
    )


def is_conflicting_plugin(plugin_path):
    '''Return true if plugin @ *plugin_path* is conflicting with Connect'''
    dirname = os.path.basename(plugin_path)
    for conflicting_plugin in CONFLICTING_PLUGINS:
        if dirname.lower().find(conflicting_plugin) > -1:
            return True
    return False


def is_incompatible_plugin(plugin_path):
    '''Return true if plugin @ *plugin_path* is incompatible with Connect
    and cannot be loaded'''
    dirname = os.path.basename(plugin_path)
    for incompatible_plugin in INCOMPATIBLE_PLUGINS:
        if dirname.lower().find(incompatible_plugin) > -1:
            # Check if it is a new-style plugin
            version_path = os.path.join(plugin_path, '__version__.py')
            return not os.path.exists(version_path)
    return False


def is_deprecated_plugin(plugin_path):
    '''Return true if plugin @ *plugin_path* is deprecated within Connect,
    but still can be loaded'''
    dirname = os.path.basename(plugin_path)
    for deprecated_plugin in DEPRECATED_PLUGINS:
        if dirname.lower().find(deprecated_plugin) > -1:
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
    if match:
        major_version = int(match.group(1))
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
                f'   Not a Connect release on YY.m.p format: {tag_name}'
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

# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import os
import subprocess
import sys

from ftrack_connect.qt import QtCore

from ftrack_connect import (
    INCOMPATIBLE_PLUGINS,
    CONFLICTING_PLUGINS,
    DEPRECATED_PLUGINS,
)


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
            # Check if it has the launch extension
            launch_path = os.path.join(plugin_path, 'launch')
            return not os.path.exists(launch_path)
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
        platform = 'win'
    elif sys.platform.startswith('linux'):
        platform = 'linux'
    elif sys.platform.startswith('darwin'):
        platform = 'mac'
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

    TODO: Align this with DCC utility functions to run in main thread, and use them
    instead as their QT implementation might differ and this solution might not apply
    or cause instabilities.
    '''
    if QtCore.QThread.currentThread() is _invoker.thread():
        fn(*args, **kwargs)
    else:
        QtCore.QCoreApplication.postEvent(
            _invoker, InvokeEvent(fn, *args, **kwargs)
        )


def qt_main_thread(func):
    '''Decorator to ensure the function runs in the QT main thread.'''

    def wrapper(*args, **kwargs):
        return invoke_in_qt_main_thread(func, *args, **kwargs)

    return wrapper

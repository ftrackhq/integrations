# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import os
import subprocess
import sys

from ftrack_connect.qt import QtCore


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


class Invoker(QtCore.QObject):
    '''Invoker.'''

    def event(self, event):
        '''Call function on *event*.'''
        event.fn(*event.args, **event.kwargs)

        return True


_invoker = Invoker()


def invoke_in_main_thread(fn, *args, **kwargs):
    '''Invoke function *fn* with arguments.'''
    QtCore.QCoreApplication.postEvent(
        _invoker, InvokeEvent(fn, *args, **kwargs)
    )


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

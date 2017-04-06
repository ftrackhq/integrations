# :coding: utf-8
# :copyright: Copyright (c) 2016 ftrack

import threading
import sys
import os
import subprocess

from QtExt import QtCore

import ftrack_api
import ftrack_api.exception


def asynchronous(method):
    '''Decorator to make a method asynchronous using its own thread.'''

    def wrapper(*args, **kwargs):
        '''Thread wrapped method.'''

        def exceptHookWrapper(*args, **kwargs):
            '''Wrapp method and pass exceptions to global excepthook.

            This is needed in threads because of
            https://sourceforge.net/tracker/?func=detail&atid=105470&aid=1230540&group_id=5470
            '''
            try:
                method(*args, **kwargs)
            except (KeyboardInterrupt, SystemExit):
                raise
            except:
                sys.excepthook(*sys.exc_info())

        thread = threading.Thread(
            target=exceptHookWrapper,
            args=args,
            kwargs=kwargs
        )
        thread.start()

    return wrapper


class Worker(QtCore.QThread):
    '''Perform work in a background thread.'''

    def __init__(self, function, args=None, kwargs=None, parent=None):
        '''Execute *function* in separate thread.

        *args* should be a list of positional arguments and *kwargs* a
        mapping of keyword arguments to pass to the function on execution.

        Store function call as self.result. If an exception occurs
        store as self.error.

        Example::

            try:
                worker = Worker(theQuestion, [42])
                worker.start()

                while worker.isRunning():
                    app = QtGui.QApplication.instance()
                    app.processEvents()

                if worker.error:
                    raise worker.error[1], None, worker.error[2]

            except Exception as error:
                traceback.print_exc()
                QtGui.QMessageBox.critical(
                    None,
                    'Error',
                    'An unhandled error occurred:'
                    '{0}'.format(error)
                )

        '''
        super(Worker, self).__init__(parent=parent)
        self.function = function
        self.args = args or []
        self.kwargs = kwargs or {}
        self.result = None
        self.error = None

    def run(self):
        '''Execute function and store result.'''
        try:
            self.result = self.function(*self.args, **self.kwargs)
        except Exception:
            self.error = sys.exc_info()


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
        _invoker,
        InvokeEvent(fn, *args, **kwargs)
    )


def get_session():
    '''Return new ftrack_api session configure without plugins or events.'''
    # Create API session using credentials as stored by the application
    # when logging in.
    # TODO: Once API is thread-safe, consider switching to a shared session.
    return ftrack_api.Session(
        server_url=os.environ['FTRACK_SERVER'],
        api_key=os.environ['FTRACK_APIKEY'],
        api_user=os.environ['LOGNAME'],
        auto_connect_event_hub=False
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
        subprocess.Popen(['start', directory], shell=True)

    elif sys.platform == 'darwin':
        if os.path.isfile(path):
            # File exists and can be opened with a selection.
            subprocess.Popen(['open', '-R', path])

        else:
            subprocess.Popen(['open', directory])

    else:
        subprocess.Popen(['xdg-open', directory])


def asset_type_exists(session, asset_type_short):
    '''Return true if *asset_type_short* exists.'''
    asset_type_found = session.query(
        'select name, short from AssetType'
        ' where short is "{0}"'.format(
            asset_type_short
        )
    ).first()
    return asset_type_found is not None


def create_asset_type(session, asset_type, asset_type_short):
    '''Ensure *asset_type* with *asset_type_short* exist.'''

    # If does not exist, we are free to create one with the given label
    try:
        session.ensure(
            'AssetType',
            {
                'short': asset_type_short,
                'name': asset_type
            },
            identifying_keys=['short']
        )
    except (
        ftrack_api.exception.PermissionDeniedError,
        ftrack_api.exception.MultipleResultsFoundError,
        ftrack_api.exception.ServerError
    ) as error:
        session.logger.warning(error)
        session.rollback()
        return {
            'status': False,
            'message': (
                'Could not create asset type {0} ({1}). This may be '
                'caused by insufficient permissions. <br />Contact your system '
                'administrator or ftrack support.'.format(
                    asset_type, asset_type_short
                )
            )
        }

    return {
        'status': True,
        'message': (
            'Asset type {0} ({1}) has been succesfully created.'
            .format(
                asset_type, asset_type_short
            )
        )
    }


def extract_plugin_name_from_record(record):
    '''Return plugin name from pyblish *record*.'''
    # The default label is '', so doing getattr(label, plugin.__name__)
    # returns an empty string if label is not defined.
    # Instead, we need to test if the plugin_name is empty after getattr.
    plugin_name = getattr(record['plugin'], 'label', None)

    if not plugin_name:
        plugin_name = record['plugin'].__name__

    return plugin_name


def extract_error_message_from_record(record):
    '''Return error message from pyblish *record*.'''

    # Default to formatting the exception as a string.
    return unicode(record['error'])

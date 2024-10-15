# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import sys
import platformdirs
import argparse
import logging
import signal
import os
import importlib

from ftrack_connect.utils.plugin import (
    create_target_plugin_directory,
    PLUGIN_DIRECTORIES,
)


def main_connect(arguments=None):
    '''Launch ftrack connect.'''

    bindings = ['PySide2']
    os.environ.setdefault('QT_PREFERRED_BINDING', os.pathsep.join(bindings))

    try:
        from PySide6 import QtWidgets, QtCore

        is_pyside2 = False
    except ImportError:
        from PySide2 import QtWidgets, QtCore

        is_pyside2 = True

    from ftrack_connect import load_fonts_resource
    import ftrack_connect.utils.log
    import ftrack_connect.singleton

    # Bootstrap hooks
    import ftrack_connect.hook

    import ftrack_connect.ui.application
    import ftrack_connect.ui.theme

    parser = argparse.ArgumentParser(prog='ftrack-connect')

    # Allow setting of logging level from arguments.
    loggingLevels = {}

    for level in (
        logging.NOTSET,
        logging.DEBUG,
        logging.INFO,
        logging.WARNING,
        logging.ERROR,
        logging.CRITICAL,
    ):
        loggingLevels[logging.getLevelName(level).lower()] = level

    parser.add_argument(
        '-v',
        '--verbosity',
        help='Set the logging output verbosity.',
        choices=loggingLevels.keys(),
        default='warning',
    )

    parser.add_argument(
        '-t',
        '--theme',
        help='Set the theme to use.',
        choices=['light', 'dark', 'system'],
        default='system',
    )

    parser.add_argument(
        '-s',
        '--silent',
        help='Set the initial visibility of the connect window.',
        action='store_true',
    )

    parser.add_argument(
        '-a',
        '--allow-multiple',
        help='Skip lockfile to allow new instance of connect.',
        action='store_true',
    )

    namespace = parser.parse_args(arguments)

    ftrack_connect.utils.log.configure_logging(
        'ftrack_connect', level=loggingLevels[namespace.verbosity]
    )

    # Make sure plugin directory is created
    create_target_plugin_directory(PLUGIN_DIRECTORIES[0])

    single_instance = None
    if not namespace.allow_multiple:
        lockfile = os.path.join(
            platformdirs.user_data_dir('ftrack-connect', 'ftrack'), 'lock'
        )
        logger = logging.getLogger('ftrack_connect')
        try:
            single_instance = ftrack_connect.singleton.SingleInstance(
                '', lockfile
            )
        except ftrack_connect.singleton.SingleInstanceException:
            logger.error(
                'Lockfile found: {}\nIs Connect already running?\nClose Connect,'
                ' remove lockfile or pass --allow-multiple and retry.'.format(
                    lockfile
                )
            )
            raise SystemExit(1)

    if is_pyside2:
        # These HighDPI settings are deprecated and enabled by default in PySide6.
        QtCore.QCoreApplication.setAttribute(
            QtCore.Qt.AA_EnableHighDpiScaling, True
        )
        QtCore.QCoreApplication.setAttribute(
            QtCore.Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True
        )
        # If under X11, make Xlib calls thread-safe.
        # http://stackoverflow.com/questions/31952711/threading-pyqt-crashes-with-unknown-request-in-queue-while-dequeuing
        if os.name == 'posix':
            QtCore.QCoreApplication.setAttribute(
                QtCore.Qt.ApplicationAttribute.AA_X11InitThreads
            )

    # Construct global application.

    application = QtWidgets.QApplication([])

    application.setOrganizationName('ftrack')
    application.setOrganizationDomain('ftrack.com')
    application.setQuitOnLastWindowClosed(False)

    # Handle Ctrl+C (SIGINT) for both Windows and Unix-like systems
    # Use a timer to allow Python interpreter to run and handle signals
    timer = QtCore.QTimer()
    timer.start(500)
    timer.timeout.connect(lambda: None)

    class SignalHandler(QtCore.QObject):
        signal_received = QtCore.Signal()

    signal_handler = SignalHandler()
    signal_handler.signal_received.connect(application.quit)

    signal.signal(
        signal.SIGINT, lambda *_: signal_handler.signal_received.emit()
    )

    # Construct main connect window and apply theme.
    connectWindow = ftrack_connect.ui.application.Application(
        theme=str(namespace.theme),
        instance=single_instance,
        log_level=loggingLevels[namespace.verbosity],
    )

    if namespace.silent:
        connectWindow.hide()

    # Fix for Windows where font size is incorrect for some widgets. For some
    # reason, resetting the font here solves the sizing issue.
    font = application.font()
    application.setFont(font)
    application.aboutToQuit.connect(connectWindow.emitConnectUsage)

    load_fonts_resource()

    return application.exec_()


def main(arguments=None):
    '''Main app entry point.'''
    # Pre-parse arguments to check if we should run a framework standalone process
    framework_standalone_module = None
    script = None
    for index, arg in enumerate(sys.argv):
        if arg == '--run-framework-standalone':
            # (Unofficial feature) Run framework standalone process using Connect Python interpreter
            framework_standalone_module = sys.argv[index + 1]
            break
        elif index == 1 and arg.endswith('.py'):
            # Run a script
            script = sys.argv[index]
            break
    if framework_standalone_module:
        # Run the framework standalone module using Connect

        # Connect installer built executable does not bootstrap PYTHONPATH,
        # make sure it is done properly.
        dependencies_path = None
        for path in os.environ.get('PYTHONPATH', []).split(os.pathsep):
            if path.find('dependencies') > -1:
                dependencies_path = path
            elif path not in sys.path:
                sys.path.append(path)
        # Put plugin deps first in sys.path to have priority over Connect packages, does not really
        # work since pyinstaller since its python interpreter deps seems locked to the executable
        sys.path.insert(0, dependencies_path)

        # Adding dependencies folder on top does not make the imports work as expected,
        # libs (utils & framework core) are still loaded and used from Connect.
        # TODO: Provide a better way to do this, for example by running through a separate
        # clean framework Python interpreter.

        importlib.import_module(framework_standalone_module, package=None)
    elif script:
        # Ported from Connect 2 installer main
        # If first argument is an executable python script, execute the file.
        exec(open(script).read())
        raise SystemExit()
    else:
        return main_connect(arguments)


if __name__ == '__main__':
    raise SystemExit(main())

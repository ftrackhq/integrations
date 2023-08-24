# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import os
import logging
from pathlib import Path
import sys
import argparse

logger = logging.getLogger(__name__)


class DummyStream:
    '''dummyStream behaves like a stream but does nothing.'''

    def __init__(self):
        pass

    def write(self, data):
        pass

    def read(self, data):
        pass

    def flush(self):
        pass

    def close(self):
        pass


'''
Fix for missing sys.stderr when building Win32GUI cx_freeze
see: https://github.com/marcelotduarte/cx_Freeze/issues/60
'''

try:
    sys.stderr.write("\n")
    sys.stderr.flush()
except Exception:
    import sys
    import http.server

    class SysWrapper(object):
        def __getattribute__(self, item):
            if item is 'stderr':
                return DummyStream()
            return getattr(sys, item)

    http.server.sys = SysWrapper()

    # and now redirect all default streams to this dummyStream:
    sys.stdout = DummyStream()
    sys.stderr = DummyStream()
    sys.stdin = DummyStream()
    sys.__stdout__ = DummyStream()
    sys.__stderr__ = DummyStream()
    sys.__stdin__ = DummyStream()


def set_environ_default(name, value):
    '''Set environment variable *name* and *value* as default.'''
    if name in os.environ:
        logger.debug(
            u'{0} already configured in environment: {1}'.format(name, value)
        )

    os.environ.setdefault(name, value)


resource_path = os.path.abspath(
    os.path.join(os.path.dirname(sys.executable), 'resource')
)

if sys.platform == "darwin":
    exec_path = Path(os.path.dirname(sys.executable))
    resource_path = os.path.abspath(
        os.path.join(str(exec_path.parent), 'Resources', 'resource')
    )

set_environ_default(
    'FTRACK_EVENT_PLUGIN_PATH',
    os.path.abspath(os.path.join(resource_path, 'hook')),
)

# Set the path to certificate file in resource folder. This allows requests
# module to read it outside frozen zip file.
set_environ_default(
    'REQUESTS_CA_BUNDLE',
    os.path.abspath(os.path.join(resource_path, 'cacert.pem')),
)

# Websocket-client ships with its own cacert file, we however default
# to the one shipped with the requests library.
set_environ_default(
    'WEBSOCKET_CLIENT_CA_BUNDLE', os.environ.get('REQUESTS_CA_BUNDLE')
)

# The httplib in python +2.7.9 requires a cacert file.
set_environ_default('SSL_CERT_FILE', os.environ.get('REQUESTS_CA_BUNDLE'))

# handle default connect and event plugin paths
ftrack_connect_plugin_paths = [
    os.path.abspath(os.path.join(resource_path, 'connect-standard-plugins'))
]

if 'FTRACK_CONNECT_PLUGIN_PATH' in os.environ:
    ftrack_connect_plugin_paths.append(
        os.environ['FTRACK_CONNECT_PLUGIN_PATH']
    )

os.environ['FTRACK_CONNECT_PLUGIN_PATH'] = os.path.pathsep.join(
    ftrack_connect_plugin_paths
)

# handle default event plugin paths
ftrack_event_plugin_paths = [
    os.path.abspath(os.path.join(resource_path, 'hook'))
]

if 'FTRACK_EVENT_PLUGIN_PATH' in os.environ:
    ftrack_event_plugin_paths.append(os.environ['FTRACK_EVENT_PLUGIN_PATH'])

os.environ['FTRACK_EVENT_PLUGIN_PATH'] = os.path.pathsep.join(
    ftrack_event_plugin_paths
)

set_environ_default('FTRACK_CONNECT_INSTALLER_RESOURCE_PATH', resource_path)

import ftrack_connect.__main__


def _validatePythonScript(path):
    '''Validate if *path* is a valid python script.'''
    return path and path.endswith('.py') and os.path.exists(path)


if __name__ == '__main__':
    arguments = sys.argv[1:]

    if sys.platform == "darwin" and getattr(sys, 'frozen', False):
        # Filter out PSN (process serial number) argument passed by OSX.
        arguments = [
            argument for argument in arguments if '-psn_0_' not in argument
        ]

    parser = argparse.ArgumentParser()

    parser.add_argument(
        'script',
        help='Path to python script to execute.',
        default='',
        nargs='?',
    )

    parser.add_argument(
        '-s',
        '--silent',
        help='Start connect window in hidden mode.',
        action='store_true',
    )

    parsedArguments, unknownArguments = parser.parse_known_args(arguments)

    # If first argument is an executable python script, execute the file.
    if parsedArguments.script and _validatePythonScript(
        parsedArguments.script
    ):
        exec(open(parsedArguments.script).read())
        raise SystemExit()

    raise SystemExit(ftrack_connect.__main__.main(arguments=arguments))

# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import os
import ftrack_api
import logging
import functools
import sys
import re
import shutil
import random
import socket
import uuid

from ftrack_utils.version import get_connect_plugin_version
from ftrack_utils.paths import get_temp_path

from ftrack_framework_core import registry

# The name of the integration, should match name in launcher.
NAME = 'framework-harmony'


logger = logging.getLogger(__name__)

cwd = os.path.dirname(__file__)
connect_plugin_path = os.path.abspath(os.path.join(cwd, '..'))

# Read version number from __version__.py
__version__ = get_connect_plugin_version(connect_plugin_path)

python_dependencies = os.path.join(connect_plugin_path, 'dependencies')


def on_discover_integration(session, event):
    data = {
        'integration': {
            'name': NAME,
            'version': __version__,
        }
    }

    return data


def check_port(port, host='localhost'):
    """
    Check if a port is free to use or not.

    :param port: The port to check.
    :param host: The host to check the port on.
    :return: True if the port is in use, False if it is free.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(2)  # Timeout in case the socket server does not respond

    try:
        sock.connect((host, port))
        sock.close()
        return False
    except (socket.timeout, ConnectionRefusedError, OSError):
        return True


def sync_js_plugin(app_path, framework_extensions_paths):
    '''
    Sync the JS plugin to the user's Harmony scripts folder, removing any existing files.

    :param app_path: The full path to DCC executable.
    :param framework_extensions_paths: List of paths to scan for extensions.
    :return:
    '''
    version_nr = None
    variant = None
    for part in app_path.split(os.sep):
        if part.lower().startswith('toon boom'):
            for s in re.findall(r'\d+', part):
                version_nr = s
                variant = part.split(' ')[-1]
                break
            if variant:
                break
    logger.info(
        f'Deploying scripts, variant: {variant}, version: {version_nr}, app_path: {app_path}'
    )

    assert (
        variant
    ), f'Could not determine Harmony variant from executable path: {app_path}'
    assert (
        version_nr
    ), f'Could not determine Harmony version from executable path: {app_path}'

    path_scripts = None
    if sys.platform == 'win32':
        path_scripts = os.path.expandvars('%APPDATA%')
    elif sys.platform == 'linux':
        path_scripts = os.path.expandvars('$HOME')
    elif sys.platform == 'darwin':
        path_scripts = os.path.expandvars('$HOME/Library/Preferences')

    if not path_scripts:
        raise Exception('Could not determine user prefs folder!')

    path_scripts = os.path.realpath(path_scripts)

    path_scripts = os.path.join(
        path_scripts,
        'Toon Boom Animation',
        'Toon Boom Harmony {}'.format(variant),
    )

    if not path_scripts:
        raise Exception('Could not determine Harmony prefs folder!')

    path_scripts = os.path.join(
        path_scripts, '{}00-scripts'.format(version_nr), 'packages', 'ftrack'
    )

    if not os.path.exists(path_scripts):
        logger.warning('Creating: {}'.format(path_scripts))
        os.makedirs(path_scripts)
    else:
        # Clean up the folder
        logger.debug('Removing files at: {}'.format(path_scripts))
        for fn in os.listdir(path_scripts):
            file_path = os.path.join(path_scripts, fn)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
                logger.debug(f'Removed: {fn}')
            except Exception as e:
                logger.error(f'Failed to delete {file_path}. Reason: {e}')

    bootstrap_folder = os.path.join(
        connect_plugin_path, 'resource', 'bootstrap'
    )

    # Copy the library and bootstrap
    for fn in ['utils.js', 'configure.js', 'harmony_commands.js']:
        src = os.path.join(bootstrap_folder, 'js', fn)
        dst = os.path.join(path_scripts, fn)
        shutil.copy(src, dst)
        logger.debug(f'Copied: {fn}')

    # Copy icons folder
    src = os.path.join(bootstrap_folder, 'icons')
    dst = os.path.join(path_scripts, 'icons')
    shutil.copytree(src, dst)
    logger.debug(f'Copied: icons')


def on_launch_integration(session, event):
    '''Handle application launch and add environment to *event*.'''

    launch_data = {'integration': event['data']['integration']}

    discover_data = on_discover_integration(session, event)
    for key in discover_data['integration']:
        launch_data['integration'][key] = discover_data['integration'][key]

    integration_version = event['data']['application']['version'].version[0]
    logger.info('Launching integration v{}'.format(integration_version))

    if not launch_data['integration'].get('env'):
        launch_data['integration']['env'] = {}

    bootstrap_path = os.path.join(connect_plugin_path, 'resource', 'bootstrap')
    logger.info('Adding {} to PYTHONPATH'.format(bootstrap_path))

    launch_data['integration']['env'][
        'PYTHONPATH.prepend'
    ] = os.path.pathsep.join([python_dependencies, bootstrap_path])

    while True:
        # Use a random port for the integration server
        port = random.randint(50000, 65000)
        if check_port(port):
            break
        else:
            logger.warning(
                f'Port {port} is already in use, trying another one.'
            )

    # Re-create the Harmony plugin taking extension into account
    sync_js_plugin(
        event['data']['application']['path'],
        event['data']['application']['environment_variables'][
            'FTRACK_FRAMEWORK_EXTENSIONS_PATH'
        ].split(os.pathsep),
    )

    launch_data['integration']['env'][
        'FTRACK_INTEGRATION_LISTEN_PORT.set'
    ] = str(port)
    launch_data['integration']['env'][
        'FTRACK_REMOTE_INTEGRATION_SESSION_ID'
    ] = str(uuid.uuid4())
    launch_data['integration']['env']['FTRACK_HARMONY_VERSION'] = str(
        integration_version
    )

    selection = event['data'].get('context', {}).get('selection', [])

    if selection:
        task = session.get('Context', selection[0]['entityId'])
        launch_data['integration']['env']['FTRACK_CONTEXTID.set'] = task['id']

    return launch_data


def register(session):
    '''Subscribe to application launch events on *registry*.'''
    if not isinstance(session, ftrack_api.session.Session):
        return

    handle_discovery_event = functools.partial(
        on_discover_integration, session
    )

    session.event_hub.subscribe(
        'topic=ftrack.connect.application.discover and '
        'data.application.identifier=harmony*'
        ' and data.application.version >= 22',
        handle_discovery_event,
        priority=40,
    )

    handle_launch_event = functools.partial(on_launch_integration, session)

    session.event_hub.subscribe(
        'topic=ftrack.connect.application.launch and '
        'data.application.identifier=harmony*'
        ' and data.application.version >= 22',
        handle_launch_event,
        priority=40,
    )

    logger.info(
        'Registered {} integration v{} discovery and launch.'.format(
            NAME, __version__
        )
    )

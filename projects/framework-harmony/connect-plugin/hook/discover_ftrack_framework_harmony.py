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


def sync_scripts(app_path):
    '''Sync scripts to Harmony user scripts folder.'''
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
        "Deploying scripts, variant: "
        + str(variant)
        + "version: "
        + str(version_nr)
        + ", app_path: "
        + str(app_path)
    )

    assert (
        variant
    ), "Could not determine Harmony variant from executable path: {}".format(
        app_path
    )
    assert (
        version_nr
    ), "Could not determine Harmony version from executable path: {}".format(
        app_path
    )

    path_scripts = None
    if sys.platform == "win32":
        path_scripts = os.path.expandvars("%APPDATA%")
    elif sys.platform == "linux":
        path_scripts = os.path.expandvars("$HOME")
    elif sys.platform == "darwin":
        path_scripts = os.path.expandvars("$HOME/Library/Preferences")

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
        path_scripts, '{}00-scripts'.format(version_nr), 'packages'
    )

    if not os.path.exists(path_scripts):
        logger.warning('Creating: {}'.format(path_scripts))
        os.makedirs(path_scripts)

    def recursive_copy_dir(src, dst):
        logger.info('Syncing {} > {}'.format(src, dst))

        for filename in os.listdir(src):
            path_src = os.path.join(src, filename)
            path_dst = os.path.join(dst, filename)

            if os.path.isdir(path_src):
                recursive_copy_dir(path_src, path_dst)
            else:
                # Compare files
                if os.path.islink(path_src):
                    # Ignore
                    continue
                remove = False
                copy = False
                if os.path.exists(path_dst):
                    remove = True
                    # Compare date and size
                    size_source = os.path.getsize(path_src)
                    size_destination = os.path.getsize(path_dst)
                    if size_destination != size_source:
                        logger.warning('Size differs on: {}'.format(path_dst))
                        copy = True
                    else:
                        modtime_source = os.path.getmtime(path_src)
                        modtime_destination = os.path.getmtime(path_dst)
                        if modtime_destination != modtime_source:
                            logger.warning(
                                'Modification date differs on: {}'.format(
                                    path_dst
                                )
                            )
                            copy = True
                else:
                    copy = True
                if copy:
                    if remove:
                        logger.warning('Removing: {}'.format(path_dst))
                        os.remove(path_dst)
                    elif not os.path.exists(os.path.dirname(path_dst)):
                        logger.warning(
                            'Creating: {}'.format(os.path.dirname(path_dst))
                        )
                        os.makedirs(os.path.dirname(path_dst))
                    logger.warning(
                        'Copying {} > {}'.format(path_src, path_dst)
                    )
                    shutil.copy(path_src, path_dst)
                    # Set modification time
                    os.utime(
                        path_dst,
                        (
                            os.path.getmtime(path_src),
                            os.path.getmtime(path_src),
                        ),
                    )

    path_src = os.path.join(
        connect_plugin_path, 'resource', 'bootstrap', 'ftrack'
    )

    recursive_copy_dir(path_src, os.path.join(path_scripts, 'ftrack'))


def check_port(port, host='localhost'):
    """
    Check if a port is free to use or not.

    Parameters:
    port (int): The port number to check.
    host (str): The host IP address or hostname. Default is 'localhost'.

    Returns:
    bool: True if the port is free, False otherwise.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(2)  # Timeout in case the socket server does not respond

    try:
        sock.connect((host, port))
        sock.close()
        return False
    except (socket.timeout, ConnectionRefusedError, OSError):
        return True


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

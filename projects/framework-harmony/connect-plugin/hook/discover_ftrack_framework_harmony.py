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


def build_harmony_plugin_loader(framework_extensions_paths, script_folder):
    if not script_folder:
        script_folder = get_temp_path()
        os.makedirs(script_folder)

    script_path = os.path.join(script_folder, "TB_sceneOpened.js")

    bootstrap_folder = os.path.join(
        connect_plugin_path, "resource", "bootstrap-test"
    )

    with open(script_path, "w") as f:
        f.write(
            """
/**
 * Harmony ftrack integration
 * 
 * Main JS entry point
 */
"use strict";

try {
        """
        )

        utils_path = os.path.join(bootstrap_folder, "utils.js").replace(
            '\\', '/'
        )
        f.write(
            f"""
    MessageLog.trace("[ftrack] Including utilities");
    include("{utils_path}");
        """
        )

        # Collect extensions

        registry_instance = registry.Registry()
        registry_instance.scan_extensions(
            paths=framework_extensions_paths, extension_types=['js_functions']
        )

        logger.debug(
            f'Extensions found: {len(registry_instance.js_functions or [])}'
        )
        for js_functions in registry_instance.js_functions or []:
            f.write(
                f"""
    MessageLog.trace("[ftrack] Including extension: {js_functions['name']}");
    include("{js_functions['path']}");
            """
            )

        bootstrap_path = os.path.join(
            bootstrap_folder, "bootstrap.js"
        ).replace('\\', '/')
        f.write(
            f"""
    MessageLog.trace("[ftrack] Including bootstrap");
    include("{bootstrap_path}");
        """
        )

        f.write(
            """

} catch (err) {
    MessageLog.trace("[ftrack] FAILED to include resources: "+err);       
}

function TB_sceneOpened()
{
  MessageLog.trace("[ftrack] Bootstrapped");
  bootstrapIntegration();
}
        """
        )

    return script_folder


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

    # Create a Harmony plugin loader script
    script_path = build_harmony_plugin_loader(
        event['data']['application']['environment_variables'][
            'FTRACK_FRAMEWORK_EXTENSIONS_PATH'
        ].split(os.pathsep),
        os.environ.get('TOONBOOM_GLOBAL_SCRIPT_LOCATION'),
    )

    launch_data['integration']['env'][
        'TOONBOOM_GLOBAL_SCRIPT_LOCATION.set'
    ] = script_path

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

# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack
import platform
import os
import sys
import ftrack_api
import logging
import functools
import uuid
import subprocess

from ftrack_connect.util import get_connect_plugin_version

# The name of the integration, should match name in launcher.
NAME = 'framework-photoshop'


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


def on_launch_integration(session, event):
    '''Handle application launch and add environment to *event*.'''

    launch_data = {'integration': event['data']['integration']}

    discover_data = on_discover_integration(session, event)
    for key in discover_data['integration']:
        launch_data['integration'][key] = discover_data['integration'][key]

    photoshop_version = event['data']['application']['version'].version[0]

    logger.info(
        'Assuming CEP plugin has been properly installed prior to launch, Photoshop'
        'is set to launch in Rosetta mode on Silicon Mac'
    )

    if not launch_data['integration'].get('env'):
        launch_data['integration']['env'] = {}

    launch_data['integration']['env'][
        'PYTHONPATH.prepend'
    ] = os.path.pathsep.join([python_dependencies])
    launch_data['integration']['env'][
        'FTRACK_REMOTE_INTEGRATION_SESSION_ID'
    ] = str(uuid.uuid4())
    launch_data['integration']['env']['FTRACK_PHOTOSHOP_VERSION'] = str(
        photoshop_version
    )

    if sys.platform == 'darwin':
        # Check if running on apple silicon (arm64)
        if subprocess.check_output("arch").decode('utf-8').find('i386') == -1:
            logger.warning(
                'Running on non Intel hardware(Apple Silicon), will require PS '
                'to be launched in Rosetta mode!'
            )
            launch_data['integration']['env']['FTRACK_LAUNCH_ARCH'] = 'x86_64'

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
        'data.application.identifier=photoshop*'
        ' and data.application.version >= 2014',
        handle_discovery_event,
        priority=40,
    )

    handle_launch_event = functools.partial(on_launch_integration, session)

    session.event_hub.subscribe(
        'topic=ftrack.connect.application.launch and '
        'data.application.identifier=photoshop*'
        ' and data.application.version >= 2014',
        handle_launch_event,
        priority=40,
    )

    logger.info(
        'Registered {} integration v{} discovery and launch.'.format(
            NAME, __version__
        )
    )

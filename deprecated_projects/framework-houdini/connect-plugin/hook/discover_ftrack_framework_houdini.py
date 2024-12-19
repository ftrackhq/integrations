# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import logging
import os
import functools
import shutil

import ftrack_api

from ftrack_utils.version import get_connect_plugin_version
from ftrack_utils.paths import get_temp_path

# The name of the integration, should match name in launcher.
NAME = 'framework-houdini'


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

    integration_version = event['data']['application']['version'].version[0]
    logger.info('Launching integration v{}'.format(integration_version))

    if not launch_data['integration'].get('env'):
        launch_data['integration']['env'] = {}

    ftrack_menu_xml_file_folder = get_temp_path(is_directory=True)
    logger.info(
        'Creating menu temp folder to {}'.format(ftrack_menu_xml_file_folder)
    )

    bootstrap_path = os.path.join(connect_plugin_path, 'resource', 'bootstrap')
    logger.info('Adding {} to PYTHONPATH'.format(bootstrap_path))

    current_houdini_path = os.environ.get('HOUDINI_PATH')

    houdini_path_append = (
        os.path.pathsep.join(
            ['&', bootstrap_path, ftrack_menu_xml_file_folder]
        )
        if current_houdini_path and not current_houdini_path.endswith('&')
        else os.path.pathsep.join(
            [bootstrap_path, ftrack_menu_xml_file_folder]
        )
    )

    launch_data['integration']['env'][
        'PYTHONPATH.prepend'
    ] = os.path.pathsep.join([python_dependencies, bootstrap_path])
    launch_data['integration']['env'][
        'HOUDINI_PATH.append'
    ] = os.path.pathsep.join([houdini_path_append, '&'])
    launch_data['integration']['env']['FTRACK_HOUDINI_VERSION'] = str(
        integration_version
    )
    launch_data['integration']['env'][
        'FTRACK_HOUDINI_XML_MENU_FILE'
    ] = ftrack_menu_xml_file_folder

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
        'data.application.identifier=houdini*'
        ' and data.application.version >= 19',
        handle_discovery_event,
        priority=40,
    )

    handle_launch_event = functools.partial(on_launch_integration, session)

    session.event_hub.subscribe(
        'topic=ftrack.connect.application.launch and '
        'data.application.identifier=houdini*'
        ' and data.application.version >= 19',
        handle_launch_event,
        priority=40,
    )

    logger.info(
        'Registered {} integration v{} discovery and launch.'.format(
            NAME, __version__
        )
    )

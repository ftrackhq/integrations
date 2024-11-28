# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import functools
import os
import logging

import ftrack_api
from ftrack_utils.version import get_connect_plugin_version

NAME = 'ftrack-nuke-studio'
''' The name of the integration, should match name in bootstrap and launcher '''

logger = logging.getLogger(__name__)

cwd = os.path.dirname(__file__)
connect_plugin_path = os.path.abspath(os.path.join(cwd, '..'))

# Read version number from __version__.py
__version__ = get_connect_plugin_version(connect_plugin_path)

python_dependencies = os.path.abspath(
    os.path.join(connect_plugin_path, 'dependencies')
)


def on_discover_nuke_studio_integration(session, event):
    data = {
        'integration': {
            'name': NAME,
            'version': __version__,
        }
    }

    return data


def on_launch_nuke_studio_integration(session, event):
    ns_base_data = on_discover_nuke_studio_integration(session, event)

    ftrack_nuke_studio_path = os.path.join(
        connect_plugin_path, 'resource', 'plugin'
    )
    application_hooks_path = os.path.join(
        connect_plugin_path, 'resource', 'application_hook'
    )

    entity = event['data']['context']['selection'][0]
    project = session.get('Project', entity['entityId'])

    ns_base_data['integration']['env'] = {
        'PYTHONPATH.prepend': python_dependencies,
        'FTRACK_EVENT_PLUGIN_PATH.prepend': application_hooks_path,
        'HIERO_PLUGIN_PATH.prepend': ftrack_nuke_studio_path,
        'FTRACK_CONTEXTID.set': project['id'],
        'QT_PREFERRED_BINDING.set': os.pathsep.join(['PySide2', 'PySide']),
    }

    return ns_base_data


def get_version_information(event):
    '''Return version information for ftrack connect installer.'''
    return [dict(name=NAME, version=__version__)]


def register(session):
    '''Register hooks for ftrack connect legacy plugins.'''

    '''Register plugin. Called when used as an plugin.'''
    # Validate that session is an instance of ftrack_api.Session. If not,
    # assume that register is being called from an old or incompatible API and
    # return without doing anything.
    if not isinstance(session, ftrack_api.session.Session):
        return

    handle_discovery_event = functools.partial(
        on_discover_nuke_studio_integration, session
    )

    session.event_hub.subscribe(
        'topic=ftrack.connect.application.discover'
        ' and (data.application.identifier=nuke-studio* or data.application.identifier=hiero*)'
        ' and data.application.version >= 13',
        handle_discovery_event,
        priority=20,
    )

    handle_launch_event = functools.partial(
        on_launch_nuke_studio_integration, session
    )

    session.event_hub.subscribe(
        'topic=ftrack.connect.application.launch'
        ' and (data.application.identifier=nuke-studio* or data.application.identifier=hiero*)'
        ' and data.application.version >= 13',
        handle_launch_event,
        priority=20,
    )

    # Enable Nuke studio info in Connect about dialog
    session.event_hub.subscribe(
        'topic=ftrack.connect.plugin.debug-information',
        get_version_information,
        priority=20,
    )

    logger.info(
        'Registered {} integration v{} discovery and launch.'.format(
            NAME, __version__
        )
    )

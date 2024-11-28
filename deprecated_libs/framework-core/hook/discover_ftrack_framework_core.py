# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import os
import sys
import ftrack_api
import logging
import functools

NAME = 'framework-core'

logger = logging.getLogger('{}.hook'.format(NAME.replace('-', '_')))


plugin_base_dir = os.path.normpath(
    os.path.join(os.path.abspath(os.path.dirname(__file__)), '..')
)

python_dependencies = os.path.join(plugin_base_dir, 'dependencies')
sys.path.append(python_dependencies)


def on_discover_ftrack_framework_core(session, event):
    from ftrack_framework_core import __version__ as integration_version

    data = {
        'integration': {
            'name': 'ftrack-{}'.format(NAME),
            'version': integration_version,
        }
    }

    return data


def on_launch_ftrack_framework_core(session, event):
    '''Handle application launch and add environment to *event*.'''

    core_base_data = on_discover_ftrack_framework_core(session, event)

    core_plugins_path = os.path.join(
        plugin_base_dir, 'resource', 'plugins', 'python'
    )

    core_bootstrap_path = os.path.join(
        plugin_base_dir, 'resource', 'bootstrap'
    )

    core_bootstrap_plugin_path = os.path.join(core_bootstrap_path, 'plugins')

    core_tool_configs_path = os.path.join(
        plugin_base_dir, 'resource', 'tool_configs'
    )

    # TODO: fix this as are all in different paths now
    core_base_data['integration']['env'] = {
        'PYTHONPATH.prepend': python_dependencies,
        'FTRACK_EVENT_PLUGIN_PATH.prepend': os.path.pathsep.join(
            [core_plugins_path, core_tool_configs_path]
        ),
        'FTRACK_TOOL_CONFIG_PATH.prepend': core_tool_configs_path,
        #'FTRACK_SCHEMA_PATH.prepend': core_schemas_path,
    }

    return core_base_data


def register(session):
    '''Subscribe to application launch events on *registry*.'''
    if not isinstance(session, ftrack_api.session.Session):
        return

    handle_discovery_event = functools.partial(
        on_discover_ftrack_framework_core, session
    )

    session.event_hub.subscribe(
        'topic=ftrack.connect.application.discover '
        'and data.application.identifier=*',
        handle_discovery_event,
        priority=20,
    )

    handle_launch_event = functools.partial(
        on_launch_ftrack_framework_core, session
    )

    session.event_hub.subscribe(
        'topic=ftrack.connect.application.launch '
        'and data.application.identifier=*',
        handle_launch_event,
        priority=20,
    )

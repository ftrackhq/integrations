# :coding: utf-8
# :copyright: Copyright (c) 2016 ftrack

import os
import ftrack_api
import ftrack_connect.application
import logging

logger = logging.getLogger('ftrack_connect_pipeline_nuke.listen_nuke_launch')

plugin_base_dir = os.path.normpath(
    os.path.join(
        os.path.abspath(
            os.path.dirname(__file__)
        ),
        '..'
    )
)

nuke_connect_plugins_path = os.path.join(
    plugin_base_dir, 'resource', 'plug_ins'
)

nuke_script_path = os.path.join(
    plugin_base_dir, 'resource', 'scripts'
)

application_hook = os.path.join(
    plugin_base_dir, 'resource', 'application_hook'
)

python_dependencies = os.path.join(
    plugin_base_dir, 'dependencies'
)


def on_application_launch(event):
    '''Handle application launch and add environment to *event*.'''

    logger.debug('Adding nuke pipeline environments.')

    # Add dependencies in pythonpath
    ftrack_connect.application.appendPath(
        python_dependencies,
        'PYTHONPATH',
        event['data']['options']['env']
    )

    # nuke scripts
    ftrack_connect.application.appendPath(
        nuke_script_path,
        'PYTHONPATH',
        event['data']['options']['env']
    )

    ftrack_connect.application.appendPath(
        nuke_script_path,
        'NUKE_PATH',
        event['data']['options']['env']
    )

    # Pipeline plugins
    ftrack_connect.application.appendPath(
        application_hook,
        'FTRACK_EVENT_PLUGIN_PATH',
        event['data']['options']['env']
    )


def register(session):
    '''Subscribe to application launch events on *registry*.'''
    if not isinstance(session, ftrack_api.session.Session):
        return

    session.event_hub.subscribe(
        'topic=ftrack.connect.application.launch and data.application.identifier=nuke*',
        on_application_launch
    )

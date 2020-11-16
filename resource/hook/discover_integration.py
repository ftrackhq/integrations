# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

import os
import re
import getpass
import sys
import pprint
import logging
import functools
import ftrack_api


def on_discover_nuke_studio_integration(session, event):
    cwd = os.path.dirname(__file__)
    sources = os.path.abspath(os.path.join(cwd, '..', 'dependencies'))
    ftrack_connect_nuke_studio_path = os.path.join(cwd, '..',  'resource')
    application_hooks_path = os.path.abspath(os.path.join(cwd, '..', 'application_hook'))
    sys.path.insert(0,sources)

    import ftrack_connect_nuke_studio
    
    entity = event['data']['context']['selection'][0]
    project = session.get('Project', entity['entityId'])


    data = {
        'integration': {
            "name": 'ftrack-connect-nuke-studio',
            'version': ftrack_connect_nuke_studio.__version__
        },
        'env': {
            'PYTHONPATH.prepend': sources,
            'FTRACK_EVENT_PLUGIN_PATH': application_hooks_path,
            'HIERO_PLUGIN_PATH': ftrack_connect_nuke_studio_path,
            'FTRACK_CONTEXTID.set': project['id'],
            'QT_PREFERRED_BINDING.set':  os.pathsep.join(['PySide2', 'PySide']),
        }
    }

    return data

def register(session, **kw):
    '''Register hooks for ftrack connect legacy plugins.'''

    '''Register plugin. Called when used as an plugin.'''
    # Validate that session is an instance of ftrack_api.Session. If not,
    # assume that register is being called from an old or incompatible API and
    # return without doing anything.
    if not isinstance(session, ftrack_api.session.Session):
        return

    handle_event = functools.partial(
        on_discover_nuke_studio_integration,
        session
    )

    session.event_hub.subscribe(
        'topic=ftrack.connect.application.launch'
        ' and data.application.identifier=nuke-studio*',
        handle_event
    )
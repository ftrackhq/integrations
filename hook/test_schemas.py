# :coding: utf-8
# :copyright: Copyright (c) 2016 ftrack

import os
import ftrack_api

import logging

logger = logging.getLogger('ftrack_connect_pipeline.test_schemas')


plugin_base_dir = os.path.normpath(
    os.path.join(
        os.path.abspath(
            os.path.dirname(__file__)
        ),
        '..'
    )
)

application_hook = os.path.join(
    plugin_base_dir, 'resource', 'application_hook'
)

python_dependencies = os.path.join(
    plugin_base_dir, 'dependencies'
)

def prependPath(path, key, environment):
    '''Prepend *path* to *key* in *environment*.'''
    try:
        environment[key] = (
            os.pathsep.join([
                path, environment[key]
            ])
        )
    except KeyError:
        environment[key] = path

    return environment

def appendPath(path, key, environment):
    '''Append *path* to *key* in *environment*.'''
    try:
        environment[key] = (
            os.pathsep.join([
                environment[key], path
            ])
        )
    except KeyError:
        environment[key] = path

    return environment

def on_discover_pipeline(event):
    '''Handle application launch and add environment to *event*.'''

    # Add pipeline dependencies to pythonpath.
    prependPath(
        python_dependencies,
        'PYTHONPATH',
        event['data']['options']['env']
    )
    print 'python_dependencies :{}'.format(python_dependencies)
    print 'preappend path PYTHONPATH :{}'.format(event['data']['options']['env'])
    # Add base plugins to events path.
    appendPath(
        application_hook,
        'FTRACK_EVENT_PLUGIN_PATH',
        event['data']['options']['env']
    )
    print 'application_hook :{}'.format(application_hook)
    print 'append path FTRACK_EVENT_PLUGIN_PATH :{}'.format(event['data']['options']['env'])


def register(session):
    '''Subscribe to application launch events on *registry*.'''
    if not isinstance(session, ftrack_api.session.Session):
        return

    print 'discovering :{}'.format('ftrack.pipeline.discover')
    logger.info('discovering :{}'.format('ftrack.pipeline.discover'))
    session.event_hub.subscribe(
        'topic=ftrack.connect.application.launch',
        on_discover_pipeline
    )

def initStandalone():
    session = ftrack_api.Session(server_url='https://lluiscasals.ftrackapp.com', api_key='YjMyMmUzOTItYmJhYi00YTVjLThjYjUtMDVmZWI0ZTRiMTk1OjpiYzM2ZDEzYy1kZGE2LTRlMWMtOTIxMC1iOThmMjU0MTBiOWI', api_user='lluis.casals@ftrack.com')
    register(session)

if __name__ == '__main__':
    initStandalone()
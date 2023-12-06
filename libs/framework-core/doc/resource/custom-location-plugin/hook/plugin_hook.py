import os
import sys
import logging

import ftrack_api


LOCATION_DIRECTORY = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', 'location')
)

sys.path.append(LOCATION_DIRECTORY)

logger = logging.getLogger(
    'com.ftrack.integrations.tutorial.custom-location-plugin.hook.plugin_hook'
)


def prependPath(path, key, environment):
    '''Prepend *path* to *key* in *environment*.'''
    try:
        environment[key] = os.pathsep.join([path, environment[key]])
    except KeyError:
        environment[key] = path

    return environment


def appendPath(path, key, environment):
    '''Append *path* to *key* in *environment*.'''
    try:
        environment[key] = os.pathsep.join([environment[key], path])
    except KeyError:
        environment[key] = path


def modify_application_launch(event):
    '''Modify the application environment to include  our location plugin.'''
    logger.info('Preparing application launch, event: {}.'.format(event))

    environment = event['data']['options']['env']

    appendPath(LOCATION_DIRECTORY, 'FTRACK_EVENT_PLUGIN_PATH', environment)
    appendPath(LOCATION_DIRECTORY, 'PYTHONPATH', environment)
    logger.info(
        'Connect plugin modified launch hook to register location plugin.'
    )


def register(api_object, **kw):
    '''Register plugin to api_object.'''

    # Validate that api_object is an instance of ftrack_api.Session. If not,
    # assume that register is being called from an incompatible API
    # and return without doing anything.
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return

    logger.info('ftrack custom directory plugin discovered.')

    import custom_location_plugin

    custom_location_plugin.register(api_object)

    # Location will be available from within the Connect dcc applications.
    api_object.event_hub.subscribe(
        'topic=ftrack.connect.application.launch', modify_application_launch
    )

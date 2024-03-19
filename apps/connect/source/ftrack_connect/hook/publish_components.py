# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import functools
import json
import os.path
import logging

import platformdirs
import ftrack_api.session


logger = logging.getLogger('ftrack_connect.publish-components')


def publish_components(event, session=None):
    '''Handle *event* and publish components.

    The event data should contain components_config which is a file path to a
    JSON config file located in the ftrack-connect/data folder. The config file
    should contain a list of components with their data ready to be published.

    '''
    try:
        components_config = event['data'].get('components_config')
        components_config = os.path.realpath(components_config)

        prefix = platformdirs.user_data_dir(
            os.path.join('ftrack-connect', 'data'), 'ftrack'
        )

        # Ensure that config file is in the data folder to avoid situations
        # where it could have been written by someone else.
        if not components_config.startswith(prefix):
            raise ValueError(
                u'Components config {0!r} should be in connect data folder {1!r}.'.format(
                    components_config, prefix
                )
            )

        with open(components_config) as data:
            components = json.load(data)

        logger.info('Publishing components: {0!r}'.format(components))

        for component in components:
            component_data = component.copy()
            path = component_data.pop('path')
            location = component_data.pop('location', 'auto')
            session.create_component(
                path, data=component_data, location=location
            )

        session.commit()

    except Exception as error:
        logger.exception('Failed to create components.')
        error_result = {
            'exception': type(error).__name__,
            'content': str(error),
        }
    else:
        error_result = None

    return {'success': error_result is None, 'error_result': error_result}


def subscribe(session):
    '''Subscribe to events.'''
    topic = 'ftrack.connect.publish-components'
    logger.info('Subscribing to event topic: {0!r}'.format(topic))
    session.event_hub.subscribe(
        u'topic="{0}" and source.user.username="{1}"'.format(
            topic, session.api_user
        ),
        functools.partial(publish_components, session=session),
    )


def register(session, **kw):
    '''Register plugin. Called when used as an plugin.'''
    # Validate that session is an instance of ftrack_api.Session. If not,
    # assume that register is being called from an old or incompatible API and
    # return without doing anything.
    if not isinstance(session, ftrack_api.session.Session):
        logger.debug(
            'Not subscribing plugin as passed argument {0!r} is not an '
            'ftrack_api.Session instance.'.format(session)
        )
        return

    subscribe(session)
    logger.debug('Plugin registered')


if __name__ == '__main__':
    '''Set up event listener manually, used for development.'''
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger('ftrack_api').setLevel(logging.INFO)
    logger.info('Starting as standalone script')
    _session = ftrack_api.Session()
    subscribe(_session)
    _session.event_hub.wait()

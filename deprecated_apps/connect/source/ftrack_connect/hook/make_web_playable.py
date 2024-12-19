# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack


import functools
import os.path
import logging

import ftrack_api.session

logger = logging.getLogger('ftrack.connect.publish.make-web-playable')


def callback(event, session):
    '''Default make-web-playable hook.

    The hook callback accepts an *event*.

    event['data'] should contain:

        * versionId - The id of the version to make reviewable.
        * path - The path to the file to use as the component.

    Will raise :py:exc:`ValueError` if the provided path is not an accessible
    file and :py:exc:`ftrack.FTrackError` if cloud storage is full or not
    enabled.

    '''
    versionId = event['data']['versionId']
    path = event['data']['path']

    version = session.get('AssetVersion', versionId)

    # Validate that the path is an accessible file.
    if not os.path.isfile(path):
        raise ValueError('"{0}" is not a valid filepath.'.format(path))

    # version.encode_media uploads file to cloud storage and triggers
    # encoding of the file to appropirate formats(mp4 and webm).
    version.encode_media(path)
    session.commit()
    logger.info('make-reviewable hook completed.')


def subscribe(session):
    '''Subscribe to events.'''
    topic = 'ftrack.connect.publish.make-web-playable'
    logger.info('Subscribing to event topic: {0!r}'.format(topic))
    session.event_hub.subscribe(
        u'topic="{0}" and source.user.username="{1}"'.format(
            topic, session.api_user
        ),
        functools.partial(callback, session=session),
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

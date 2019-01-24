# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import os
import functools
import logging

import ftrack_api
from ftrack_connect_pipeline import constants

logger = logging.getLogger(__name__)


def set_context(session, data=None, options=None):
    logger.debug('Calling set_context with options: {}'.format(options))
    os.environ['FTRACK_CONTEXT_ID'] = options['context_id']
    os.environ['FTRACK_TASKID'] = options['context_id']
    return options


def register_collector(session, event):
    return set_context(session, **event['data'])


def register(api_object, **kw):
    '''Register plugin to api_object.'''

    # Validate that api_object is an instance of ftrack_api.Session. If not,
    # assume that _register_assets is being called from an incompatible API
    # and return without doing anything.
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return

    topic = constants.CONTEXT_PLUGIN_TOPIC.format('context.publish')
    logger.info('discovering :{}'.format(topic))

    event_handler = functools.partial(
        register_collector, api_object
    )
    api_object.event_hub.subscribe(
        'topic={}'.format(topic),
        event_handler
    )

import os
import functools
import logging

import ftrack_api
from ftrack_connect_framework import constants

logger = logging.getLogger(__name__)


def collect_from_set(session, data=None, options=None):
    logger.debug('Calling collect from set with options: {}'.format(options))

    import maya.cmds as cmd
    import maya

    def call(set_name):
        return cmd.sets(set_name, q=True)

    set_name = options['set_name']
    return maya.utils.executeInMainThreadWithResult(call, set_name)


def register_collector(session, event):
    logger.info('registering collet from set collector...')
    return collect_from_set(session, **event['data'])


def register(api_object, **kw):
    '''Register plugin to api_object.'''

    # Validate that api_object is an instance of ftrack_api.Session. If not,
    # assume that register_assets is being called from an incompatible API
    # and return without doing anything.
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return

    topic = constants.COLLECTORS_PLUGIN_TOPIC.format('from_set.maya')
    logger.info('discovering :{}'.format(topic))

    event_handler = functools.partial(
        register_collector, api_object
    )
    api_object.event_hub.subscribe(
        'topic={}'.format(topic),
        event_handler
    )

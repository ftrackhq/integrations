import os
import functools
import logging

import ftrack_api
from ftrack_connect_framework import constants

logger = logging.getLogger(__name__)


def collect_homefiles(session, data=None, options=None):
    extension = options['extension']
    logger.debug('Calling collect homefiles with options: extension {}'.format(extension))
    homefolder = os.path.expandvars('$HOME')
    return [os.path.join(homefolder, f) for f in os.listdir(homefolder) if f.endswith(extension)]


def register_collector(session, event):
    return collect_homefiles(session, **event['data'])


def register(api_object, **kw):
    '''Register plugin to api_object.'''

    # Validate that api_object is an instance of ftrack_api.Session. If not,
    # assume that register_assets is being called from an incompatible API
    # and return without doing anything.
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return

    topic = constants.COLLECTORS_PLUGIN_TOPIC.format('homefiles')
    logger.info('discovering :{}'.format(topic))

    event_handler = functools.partial(
        register_collector, api_object
    )
    api_object.event_hub.subscribe(
        'topic={}'.format(topic),
        event_handler
    )

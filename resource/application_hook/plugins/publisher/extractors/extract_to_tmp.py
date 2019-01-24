# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import shutil
import tempfile
import functools
import logging

import ftrack_api
from ftrack_connect_pipeline import constants

logger = logging.getLogger(__name__)


def extract_to_tmp(session, data=None, options=None):
    logger.debug('Calling extractor options: data {}'.format(data))

    result = []
    for item in data:
        new_file_path = tempfile.NamedTemporaryFile(delete=False).name
        shutil.copy(item, new_file_path)
        result.append((item, new_file_path))

    return result


def register_extractor(session, event):
    return extract_to_tmp(session, **event['data'])


def register(api_object, **kw):
    '''Register plugin to api_object.'''

    # Validate that api_object is an instance of ftrack_api.Session. If not,
    # assume that _register_assets is being called from an incompatible API
    # and return without doing anything.
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return

    topic = constants.EXTRACTORS_PLUGIN_TOPIC.format('to_tmp')
    logger.info('discovering :{}'.format(topic))

    event_handler = functools.partial(
        register_extractor, api_object
    )
    api_object.event_hub.subscribe(
        'topic={}'.format(topic),
        event_handler
    )

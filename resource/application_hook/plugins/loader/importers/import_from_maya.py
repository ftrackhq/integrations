import os
import tempfile
import functools
import logging

import ftrack_api
from ftrack_connect_pipeline import constants

logger = logging.getLogger(__name__)


def import_maya(session, data=None, options=None):
    logger.info('CALLING IMPORT with: {} {} {}'.format(session, data, options))

    import maya.cmds as cmd
    import maya

    def call(component_path):
        logger.debug('Calling importer options: data {}'.format(data))
        cmd.file(component_path, i=True)
        return True

    component_path = options['component_list']
    return maya.utils.executeInMainThreadWithResult(call, component_path)


def register_importer(session, event):
    return import_maya(session, **event['data'])


def register(api_object, **kw):
    '''Register plugin to api_object.'''

    # Validate that api_object is an instance of ftrack_api.Session. If not,
    # assume that register_assets is being called from an incompatible API
    # and return without doing anything.
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return

    topic = constants.IMPORTERS_PLUGIN_TOPIC.format('maya')
    logger.info('discovering :{}'.format(topic))

    event_handler = functools.partial(
        register_importer, api_object
    )
    api_object.event_hub.subscribe(
        'topic={}'.format(topic),
        event_handler
    )

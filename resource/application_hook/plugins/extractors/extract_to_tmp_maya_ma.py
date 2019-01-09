import os
import tempfile
import functools
import logging

import ftrack_api
from ftrack_connect_pipeline import constants

logger = logging.getLogger(__name__)


def extract_to_tmp(session, data=None, options=None):
    import maya.cmds as cmd
    import maya

    def call(component_name):
        new_file_path = tempfile.NamedTemporaryFile(delete=False).name
        logger.debug('Calling extractor options: data {}'.format(data))
        cmd.select(data, r=True)
        cmd.file(rename=new_file_path)
        cmd.file(save=True, type='mayaAscii')
        return (component_name, new_file_path)

    component_name = options['component_name']
    return maya.utils.executeInMainThreadWithResult(call, component_name)



def register_extractor(session, event):
    return extract_to_tmp(session, **event['data'])


def register(api_object, **kw):
    '''Register plugin to api_object.'''

    # Validate that api_object is an instance of ftrack_api.Session. If not,
    # assume that register_assets is being called from an incompatible API
    # and return without doing anything.
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return

    topic = constants.EXTRACTORS_PLUGIN_TOPIC.format('to_tmp.maya.ma')
    logger.info('discovering :{}'.format(topic))

    event_handler = functools.partial(
        register_extractor, api_object
    )
    api_object.event_hub.subscribe(
        'topic={}'.format(topic),
        event_handler
    )

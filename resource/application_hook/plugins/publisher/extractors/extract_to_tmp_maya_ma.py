# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import tempfile
import functools
import logging

import ftrack_api
from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline_maya.constants import HOST

logger = logging.getLogger('ftrack_connect_pipeline_maya.plugin')


def extract_to_tmp(session, data=None, options=None):
    import maya.cmds as cmd
    import maya

    def call(component_name):
        new_file_path = tempfile.NamedTemporaryFile(delete=False, suffix='.ma').name
        logger.debug('Calling extractor options: data {}'.format(data))
        cmd.select(data, r=True)
        cmd.file(rename=new_file_path)
        cmd.file(save=True, type='mayaAscii')
        return (component_name, new_file_path)

    component_name = options['component_name']
    return maya.utils.executeInMainThreadWithResult(call, component_name)



def register_extractor(session, event):
    return extract_to_tmp(session, **event['data']['settings'])


def register(api_object, **kw):
    '''Register plugin to api_object.'''

    # Validate that api_object is an instance of ftrack_api.Session. If not,
    # assume that _register_assets is being called from an incompatible API
    # and return without doing anything.
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return

    # topic = constants.EXTRACTORS_PLUGIN_TOPIC.format('mayaascii')
    # logger.info('discovering :{}'.format(topic))

    event_handler = functools.partial(
        register_extractor, api_object
    )
    # api_object.event_hub.subscribe(
    #     'topic={} and data.pipeline.host={} and data.pipeline.type=plugin'.format(topic, HOST),
    #     event_handler
    # )

    api_object.event_hub.subscribe(
        'topic={} and '
        'data.pipeline.host={} and '
        'data.pipeline.plugin_type={} and '
        'data.pipeline.plugin_name={} and '
        'data.pipeline.type=plugin'.format(
            constants.PIPELINE_REGISTER_TOPIC,
            HOST,
            constants.IMPORTERS,
            'mayaascii'
        ),
        event_handler
    )
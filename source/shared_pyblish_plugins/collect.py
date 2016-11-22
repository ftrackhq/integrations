# :coding: utf-8
# :copyright: Copyright (c) 2016 ftrack

import logging

import pyblish.api
import ftrack_connect_pipeline.util

logger = logging.getLogger(__file__)


class FtrackPublishCollector(pyblish.api.ContextPlugin):
    '''Prepare ftrack publish.'''

    order = pyblish.api.CollectorOrder

    def process(self, context):
        '''Process *context* and add ftrack entity.'''
        ftrack_entity = ftrack_connect_pipeline.util.get_ftrack_entity()
        context.data['ftrack_entity'] = ftrack_entity
        logger.debug('Collected ftrack entity {0}.'.format(ftrack_entity))


pyblish.api.register_plugin(FtrackPublishCollector)


class CollectNukeScript(pyblish.api.ContextPlugin):
    '''Collect nuke write nodes from scene.'''

    order = pyblish.api.CollectorOrder

    def process(self, context):
        '''Process *context* and add nuke write node instances.'''
        self.log.debug('Started collecting scene script.')

        instance = context.create_instance(
            'Script', family='ftrack.nuke.script'
        )
        instance.data['publish'] = True
        instance.data['ftrack_components'] = []

        self.log.debug(
            'Collected Script instance {0!r}.'.format(
                instance
            )
        )


pyblish.api.register_plugin(FtrackPublishCollector)
pyblish.api.register_plugin(CollectNukeScript)

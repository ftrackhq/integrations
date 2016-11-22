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

# :coding: utf-8
# :copyright: Copyright (c) 2016 ftrack

import pyblish.api


class FtrackEntityCollector(pyblish.api.ContextPlugin):
    '''Prepare ftrack publish.'''

    order = pyblish.api.CollectorOrder

    def process(self, context):
        '''Process *context* and add ftrack entity.'''
        import ftrack_connect_pipeline.util
        ftrack_entity = ftrack_connect_pipeline.util.get_ftrack_entity()
        context.data['ftrack_entity'] = ftrack_entity
        self.log.debug('Collected ftrack entity {0}.'.format(ftrack_entity))


pyblish.api.register_plugin(FtrackEntityCollector)

import os

import pyblish.api
import ftrack_api


class FtrackPublishCollector(pyblish.api.ContextPlugin):
    '''Prepare ftrack publish.'''

    order = pyblish.api.CollectorOrder

    def process(self, context):
        '''Process *context* and add ftrack entity.'''
        session = ftrack_api.Session()
        ftrack_entity = session.get(
            'Context', os.environ['FTRACK_CONTEXT_ID']
        )
        context.data['ftrack_entity'] = ftrack_entity

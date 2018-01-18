import os
import hiero
import logging
import ftrack_api

class FtrackBase(object):
    '''
    wrap ftrack functionalities and methods
    '''
    def __init__(self, *args, **kwargs):
        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )
        self.logger.setLevel(logging.DEBUG)
        self.session = ftrack_api.Session()

    @property
    def hiero_version_touple(self):
        return (
            hiero.core.env['VersionMajor'],
            hiero.core.env['VersionMinor'],
            hiero.core.env['VersionRelease'].split('v')[-1]
        )

    @property
    def schema(self):
        # default project schema should be defined as part of the preset property ?
        result = self.session.query('ProjectSchema where name is "Film Pipeline"').first()
        self.logger.info('Project schema: %s' % result)
        return result

    @property
    def task_type(self):
        # default task type be defined as part of the preset property ?
        result =  self.schema.get_types('Task')
        self.logger.info('task_type: %s' % result)
        return result[0]

    @property
    def task_status(self):
        # default task status be defined as part of the preset property ?
        result =  self.schema.get_statuses('Task', self.task_type['id'])
        self.logger.info('task_status: %s' % result)
        return result[0]

    @property
    def shot_status(self):
        # default shot status be defined as part of the preset property ?
        result =  self.schema.get_statuses('Shot')
        self.logger.info('shot_status: %s' % result)
        return result[0]

    @property
    def ftrack_location(self):
        result = self.session.pick_location()    
        self.logger.info('location: %s' % result)
        return result

    def resolve_ftrack_project(self, task):
        return task.projectName()

    def resolve_ftrack_sequence(self, task):
        trackItem = task._item
        return trackItem.name().split('_')[0]

    def resolve_ftrack_shot(self, task):
        trackItem = task._item
        return trackItem.name().split('_')[1]        
    
    def resolve_ftrack_task(self, task):
        # TODO: here we should really parse the task tags and use the ftrack task tag to define ?
        # let's stick to something basic for now
        return 'Compositing'

    def resolve_ftrack_component(self, task):
        # TODO: Check whether there's a better way to get this out !
        preset_name =  vars(task)['_preset'].name()
        return preset_name

    def resolve_ftrack_version(self, task):
        return "0" # here we can check if there's any tag with an id to check against, if not we can return 0 as first version        


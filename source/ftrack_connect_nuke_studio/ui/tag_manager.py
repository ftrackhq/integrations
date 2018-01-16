# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

import logging

import hiero.core

from ftrack_connect.session import (
    get_shared_session
)

class TagManager(object):
    '''Creates all the custom tags wrapping the ftrack's entities.'''

    def __init__(self, *args, **kwargs):
        ''' Initialize and create the needed Bin and Tags.'''
        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

        self.session = get_shared_session()

        self.logger.debug('Creating Ftrack tags')
        self.project = hiero.core.project('Tag Presets')
        self.project.setEditable(True)
        self.ftrack_bin_main = hiero.core.Bin('ftrack')
        self.ftrack_bin_task = hiero.core.Bin('Task')
        self.ftrack_bin_context = hiero.core.Bin('Context')

        self._createBin()
        self._setTasksTags()

    def _createBin(self):
        '''Create the all the required Bins.'''
        tagsbin = self.project.tagsBin()
        tagsbin.addItem(self.ftrack_bin_main)
        self.ftrack_bin_main.addItem(self.ftrack_bin_task)
        self.ftrack_bin_main.addItem(self.ftrack_bin_context)

    def _setTasksTags(self):
        '''Create task tags from ftrack tasks.'''
        self.logger.debug('Creating Ftrack task tags')

        types = [
            ('Type', self.ftrack_bin_task, 'task'), 
            ('ObjectType', self.ftrack_bin_context, 'context')
        ]
        for ftype, fn, spec in types:
            task_type_tags = []
            for task_type in self.session.query(ftype):
                task_type_id = task_type.get('id')
                task_type_name = task_type.get('name')

                ftag = hiero.core.Tag(task_type_name)
                ftag.setIcon(':ftrack/image/integration/task')

                meta = ftag.metadata()
                meta.setValue('type', 'ftrack')
                meta.setValue('ftrack.type', spec)
                meta.setValue('ftrack.id', task_type_id)
                meta.setValue('ftrack.name', task_type_name)
                meta.setValue('tag.value', task_type_name)
                task_type_tags.append((task_type_name, ftag))

            task_type_tags = sorted(
                task_type_tags, key=lambda tag_tuple: tag_tuple[0].lower()
            )

            self.logger.debug(
                u'Added task type tags: {0}'.format(
                    task_type_tags
                )
            )

            for _, tag in task_type_tags:
                fn.addItem(tag)

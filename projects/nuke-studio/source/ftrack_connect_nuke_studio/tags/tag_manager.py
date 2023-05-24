# :coding: utf-8
# :copyright: Copyright (c) 2018 ftrack

import logging

import hiero.core

from ftrack_connect_nuke_studio.base import FtrackBase

class TagManager(FtrackBase):
    '''Creates all the custom tags wrapping the ftrack's entities.'''

    def __init__(self, *args, **kwargs):
        ''' Initialize and create the needed Bin and Tags.'''
        super(TagManager, self).__init__()

        self.logger.debug('Creating Ftrack tags')
        self.project = hiero.core.project('Tag Presets')
        self.project.setEditable(True)
        self.ftrack_bin_main = hiero.core.Bin('ftrack')
        self.ftrack_bin_task = hiero.core.Bin('Task')

        self._createBin()
        self._setTasksTags()

    def _createBin(self):
        '''Create the all the required Bins.'''
        tagsbin = self.project.tagsBin()
        tagsbin.addItem(self.ftrack_bin_main)
        self.ftrack_bin_main.addItem(self.ftrack_bin_task)

    def _setTasksTags(self):
        '''Create task tags from ftrack tasks.'''
        self.logger.debug('Creating Ftrack task tags')

        task_type_tags = []
        for task_type in self.session.query('Type'):
            task_type_id = task_type.get('id')
            task_type_name = task_type.get('name')

            ftag = hiero.core.Tag(task_type_name)
            ftag.setIcon(':ftrack/image/integration/task')

            meta = ftag.metadata()
            meta.setValue('type', 'ftrack')
            meta.setValue('ftrack.type', 'task')
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
            self.ftrack_bin_task.addItem(tag)

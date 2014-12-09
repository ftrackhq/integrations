# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

import os
import hiero.core
import ftrack
import FnAssetAPI.logging


class FTags(object):
    ''' Creates all the custom tags wrappping the ftrack's entities.
    '''
    def __init__(self, *args, **kwargs):
        ''' Initialize and create the needed Bin and Tags
        '''
        self.icons = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'icons', '%s.png')
        FnAssetAPI.logging.debug('Creating Ftrack tags')
        self.project = hiero.core.project('Tag Presets')
        self.ftrack_bin_main = hiero.core.Bin('fTrack')
        self.ftrack_bin_context = hiero.core.Bin('Context')
        self.ftrack_bin_task = hiero.core.Bin('Task')

        self._createBin()
        self._setTasksTags()
        self._setContextTags()

    def _createBin(self):
        ''' Create the all the required Bins.
        '''
        tagsbin = self.project.tagsBin()
        tagsbin.addItem(self.ftrack_bin_main)
        self.ftrack_bin_main.addItem(self.ftrack_bin_context)
        self.ftrack_bin_main.addItem(self.ftrack_bin_task)

    def _setTasksTags(self):
        ''' Create task tags from ftrack tasks.
        '''
        FnAssetAPI.logging.debug('Creating Ftrack task tags')

        task_types = ftrack.getTaskTypes()

        for task_type in task_types:
            ftag = hiero.core.Tag(task_type.getName())
            ftag.setIcon(self.icons % 'task')

            meta = ftag.metadata()
            meta.setValue('type', 'ftrack')
            meta.setValue('ftrack.type', 'task')
            meta.setValue('ftrack.id', task_type.getId())
            meta.setValue('ftrack.name', task_type.getName())
            meta.setValue('tag.value', task_type.getName())
            self.ftrack_bin_task.addItem(ftag)

    def _setContextTags(self):
        ''' Create context tags from the common ftrack tasks.
        '''
        FnAssetAPI.logging.debug('Creating Ftrack context tags')

        context_tags = [
            ('project', 'show', None),
            ('episode','episode', '(\w+.)?EP(\d+)'), 
            ('sequence','sequence', '(\w+.)?SQ(\d+)'), 
            ('shot','shot', '(\w+.)?SH(\d+)')
        ]

        # context tags
        for context_tag in context_tags:
            # explode the tag touples
            tag_name, tag_id, tag_re = context_tag
            
            ftag = hiero.core.Tag(context_tag[0])
            ftag.setIcon(self.icons % tag_id)
            meta = ftag.metadata()
            meta.setValue('type', 'ftrack')
            meta.setValue('ftrack.type', tag_id)
            meta.setValue('tag.value', None) # public data
            meta.setValue('tag.re', tag_re) # public data
            meta.setValue('ftrack.id', tag_id)
            meta.setValue('ftrack.name', tag_name)
            
            self.ftrack_bin_context.addItem(ftag)
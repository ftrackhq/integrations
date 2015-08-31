# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

import logging

import hiero.core
import ftrack

from ftrack_connect.ui import resource

# Default context tags.
DEFAULT_CONTEXT_TAGS = [
    ('project', 'show', None),
    ('episode', 'episode', '(\w+.)?EP(\d+)'),
    ('sequence', 'sequence', '(\w+.)?SQ(\d+)'),
    ('shot', 'shot', '(\w+.)?SH(\d+)')

]


class TagManager(object):
    '''Creates all the custom tags wrapping the ftrack's entities.'''

    def __init__(self, *args, **kwargs):
        ''' Initialize and create the needed Bin and Tags.'''
        logging.debug('Creating Ftrack tags')
        self.project = hiero.core.project('Tag Presets')
        self.project.setEditable(True)
        self.ftrack_bin_main = hiero.core.Bin('ftrack')
        self.ftrack_bin_context = hiero.core.Bin('Context')
        self.ftrack_bin_task = hiero.core.Bin('Task')

        self._createBin()
        self._setTasksTags()
        self._setContextTags()

    def _createBin(self):
        '''Create the all the required Bins.'''
        tagsbin = self.project.tagsBin()
        tagsbin.addItem(self.ftrack_bin_main)
        self.ftrack_bin_main.addItem(self.ftrack_bin_context)
        self.ftrack_bin_main.addItem(self.ftrack_bin_task)

    def _setTasksTags(self):
        '''Create task tags from ftrack tasks.'''
        logging.debug('Creating Ftrack task tags')

        task_types = ftrack.getTaskTypes()

        task_type_tags = []
        for task_type in task_types:
            ftag = hiero.core.Tag(task_type.getName())
            ftag.setIcon(':ftrack/image/integration/task')

            meta = ftag.metadata()
            meta.setValue('type', 'ftrack')
            meta.setValue('ftrack.type', 'task')
            meta.setValue('ftrack.id', task_type.getId())
            meta.setValue('ftrack.name', task_type.getName())
            meta.setValue('tag.value', task_type.getName())
            task_type_tags.append((task_type.getName(), ftag))

        task_type_tags = sorted(
            task_type_tags, key=lambda tag_tuple: tag_tuple[0].lower()
        )

        for _, tag in task_type_tags:
            self.ftrack_bin_task.addItem(tag)

    def _setContextTags(self):
        '''Create context tags from the common ftrack tasks.'''
        logging.debug('Creating Ftrack context tags')

        result = ftrack.EVENT_HUB.publish(
            ftrack.Event(
                topic='ftrack.connect.nuke-studio.get-context-tags'
            ),
            synchronous=True
        )

        context_tags = []
        if not result:
            context_tags = DEFAULT_CONTEXT_TAGS
        else:

            for tags in result:
                context_tags += tags

        for context_tag in context_tags:
            # explode the tag touples
            tag_name, tag_id, tag_re = context_tag

            ftag = hiero.core.Tag(context_tag[0])

            icon = tag_id
            if icon == 'sequence':
                icon = 'folder'

            if icon == 'show':
                icon = 'home'

            logging.info(icon)
            ftag.setIcon(':ftrack/image/integration/{0}'.format(icon))

            meta = ftag.metadata()
            meta.setValue('type', 'ftrack')
            meta.setValue('ftrack.type', tag_id)
            meta.setValue('tag.value', None)  # Public data
            meta.setValue('tag.re', tag_re)  # Public data
            meta.setValue('ftrack.id', tag_id)
            meta.setValue('ftrack.name', tag_name)

            self.ftrack_bin_context.addItem(ftag)

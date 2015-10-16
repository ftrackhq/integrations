# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

import logging
import re

import hiero.core
import ftrack

from ftrack_connect.ui import resource


# Default context tags that are used when no hook discovered.
DEFAULT_CONTEXT_TAGS = [
    ('project', 'show', None),
    ('episode', 'episode', 'EP(?P<value>\d+)|(?P<value>.+)'),
    ('sequence', 'sequence', 'SQ(?P<value>\d+)|(?P<value>.+)'),
    ('shot', 'shot', 'SH(?P<value>\d+)|(?P<value>.+)')
]


def update_tag_value_from_name(track_item):
    '''Update meta on ftrack tags on *track_item*.

    Uses the tag.re field to extract the context from the name,
    and set it back to the applied tag.

    '''
    logger = logging.getLogger('{0}.update_tag_value_from_name'.format(
        __name__
    ))
    name = track_item.name()
    tags = track_item.tags()

    for tag in tags:
        tag_name = tag.name()
        meta = tag.metadata()

        # Filter out any non ftrack tag
        if not meta.hasKey('type') or meta.value('type') != 'ftrack':
            logger.debug(
                '{0} is not a valid track tag type'.format(tag_name)
            )
            continue

        # Handle a tag with a regular expression.
        if meta.hasKey('tag.re'):
            expression = meta.value('tag.re')
            if not expression:
                # If the regular expression is empty skip it.
                logger.debug(
                    'Skipping {0!r} tag with no expression defined.'
                    .format(tag_name)
                )
                continue

            # Python does not support multiple groups of the same name even when
            # part of a OR expression so manually split expression for now.
            # Note: This logic could be improved to avoid false positives.
            expressions = expression.split('|')
            for expression in expressions:
                logger.debug(
                    'Testing {0!r} tag {1!r} expression against name {2!r}.'
                    .format(tag_name, expression, name)
                )
                match = re.search(expression, name)
                if match:
                    value = match.groupdict().get('value')
                    if not value:
                        logger.debug('Expression matched, but missing "value".')
                        # No match.
                        continue

                    logger.debug('Expression matched.')
                    logger.debug(
                        'Setting {0} to {1} on {2}'.format(
                            tag_name, value, name
                        )
                    )
                    meta.setValue('tag.value', value)
                    break

                else:
                    logger.debug('Expression did not match.')


class TagManager(object):
    '''Creates all the custom tags wrapping the ftrack's entities.'''

    def __init__(self, *args, **kwargs):
        ''' Initialize and create the needed Bin and Tags.'''
        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )
        self.logger.debug('Creating Ftrack tags')
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
        self.logger.debug('Creating Ftrack task tags')

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

        self.logger.debug(
            u'Added task type tags: {0}'.format(
                task_type_tags
            )
        )

        for _, tag in task_type_tags:
            self.ftrack_bin_task.addItem(tag)

    def _setContextTags(self):
        '''Create context tags from the common ftrack tasks.'''
        self.logger.debug('Creating Ftrack context tags')

        result = ftrack.EVENT_HUB.publish(
            ftrack.Event(
                topic='ftrack.connect.nuke-studio.get-context-tags'
            ),
            synchronous=True
        )

        context_tags = []
        if not result:
            self.logger.debug(
                'Retrieved 0 tags form hook. Using default tags'
            )
            context_tags = DEFAULT_CONTEXT_TAGS
        else:

            for tags in result:
                context_tags += tags

        self.logger.debug(
            u'Added context tags: {0}'.format(
                context_tags
            )
        )

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

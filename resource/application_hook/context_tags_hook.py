# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import logging

import ftrack


class ContextTags(object):
    '''Return context tags for Nuke Studio.'''

    def __init__(self, *args, **kwargs):
        '''Initialise context tags hook.'''
        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

        super(ContextTags, self).__init__(*args, **kwargs)

    def launch(self, event):
        '''Return context tags.

        Should be list with tags using the format:

            ('tag_id', 'ftrack_type_id', 'regexp')

        '''

        self.logger.debug('Loading context tags from hook.')

        return [
            ('project', 'show', None),
            ('episode', 'episode', '(\w+.)?EP(\d+)'),
            ('sequence', 'sequence', '(\w+.)?SQ(\d+)'),
            ('shot', 'shot', '(\w+.)?SH(\d+)')
        ]

    def register(self):
        '''Register hook.'''
        ftrack.EVENT_HUB.subscribe(
            'topic=ftrack.connect.nuke-studio.get-context-tags',
            self.launch
        )


def register(registry, **kw):
    '''Register hooks for context tags.'''

    # Validate that registry is instance of ftrack.Registry, if not
    # return early since the register method probably is called
    # from the new API.
    if not isinstance(registry, ftrack.Registry):
        return

    plugin = ContextTags()
    plugin.register()

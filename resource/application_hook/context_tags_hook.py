# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

import FnAssetAPI.logging
import ftrack


class ContextTags(object):
    '''Return context tags for Nuke Studio.'''

    def launch(self, event):
        '''Return context tags.

        Should be list with tags using the format:

            ('tag_id', 'ftrack_type_id', 'regexp')

        '''

        FnAssetAPI.logging.debug('Loading context tags from hook.')

        return [
            ('project', 'show', None),
            ('episode', 'episode', '(\w+.)?EP(\d+)'),
            ('sequence', 'sequence', '(\w+.)?SEQ(\d+)'),
            ('shot', 'shot', '(\w+.)?SHO(\d+)')
        ]

    def register(self):
        '''Register processor'''
        ftrack.EVENT_HUB.subscribe(
            'topic=ftrack.connect.nuke-studio.get-context-tags',
            self.launch
        )


def register(registry, **kw):
    '''Register hooks thumbnail processor.'''
    plugin = ContextTags()
    plugin.register()

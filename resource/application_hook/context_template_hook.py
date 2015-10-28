# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import logging

import ftrack


class ContextTemplates(object):
    '''Return context templates for Nuke Studio.'''

    def __init__(self, *args, **kwargs):
        '''Initialise context templates hook.'''
        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

        super(ContextTemplates, self).__init__(*args, **kwargs)

    def launch(self, event):
        '''Return context templates.'''
        # Define tag regular expressions.
        return [{
            'name': 'Classic, sequence and shot)',
            'description': (
                'Template matching sequences and shots separated by'
                ' underscore. Eg. "SQ001_SH010" will be matched as '
                'Sequence with name SQ001 and a shot named SH010.'
            ),
            'expression': 'SQ{Sequence:.+}_SH{Shot:.+}'
        }, {
            'name': 'Classic, shot only',
            'description': (
                'Template matching entire clip name or digits after "SH". Eg.'
                '"SH001" will match 001 while "Shot_010" will use entire name.'
            ),
            'expression': 'SH{Shot:.+}'
        }, {
            'name': 'Full name, shot only',
            'description': (
                'Template matching entire clip name.'
            ),
            'expression': '{Shot:.+}'
        }]

    def register(self):
        '''Register hook.'''
        ftrack.EVENT_HUB.subscribe(
            'topic=ftrack.connect.nuke-studio.get-context-templates',
            self.launch
        )


def register(registry, **kw):
    '''Register hook for context templates.'''

    # Validate that registry is instance of ftrack.Registry, if not
    # return early since the register method probably is called
    # from the new API.
    if not isinstance(registry, ftrack.Registry):
        return

    plugin = ContextTemplates()
    plugin.register()

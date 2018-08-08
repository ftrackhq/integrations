# :coding: utf-8
# :copyright: Copyright (c) 2018 ftrack

import logging
import ftrack_api


class ContextTemplates(object):
    '''Return context templates for Nuke Studio.'''

    def __init__(self, session, *args, **kwargs):
        '''Initialise context templates hook.'''
        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

        self.session = session

        super(ContextTemplates, self).__init__(*args, **kwargs)

    def launch(self, event):
        '''Return context templates.'''
        # Define tag regular expressions.
        return [{
            'name': 'Basic, sequence and shot',
            'description': (
                'Match Sequence and Shot by underscores naming. '
                'Example: SQ001_SH010 will be matched as Sequence with name '
                'SQ001 and a shot named SH010.'
            ),
            'expression': '{Sequence:.+}_{Shot:.+}'
        },
        {
            'name': 'Classic, sequence and shot',
            'description': (
                'Match SQ or SH and any subsequent numbers. '
                'Example: SQ001_SH010 will be matched as Sequence with name '
                '001 and a shot named 010.'
            ),
            'expression': '{_:SQ|sq}{Sequence:\d+}{_:.+(SH|sh)}{Shot:\d+}'
        },{
            'name': 'Classic, shot only',
            'description': (
                'Match SH and any subsequent digits. '
                'Example: vfx_SH001 will match 001.'
            ),
            'expression': '{_:SH|sh}{Shot:\d+}'
        }, {
            'name': 'Full name, shot only',
            'description': (
                'Match entire clip name. '
                'Example: vfx_SH001 will match vfx_SH001.'
            ),
            'expression': '{Shot:.+}'
        }]

    def register(self):
        '''Register hook.'''
        self.session.event_hub.subscribe(
            'topic=ftrack.connect.nuke-studio-beta.get-context-templates',
            self.launch
        )


def register(session, **kw):
    '''Register plugin. Called when used as an plugin.'''
    # Validate that session is an instance of ftrack_api.Session. If not,
    # assume that register is being called from an old or incompatible API and
    # return without doing anything.
    if not isinstance(session, ftrack_api.session.Session):
        return

    plugin = ContextTemplates(
        session
    )

    plugin.register()
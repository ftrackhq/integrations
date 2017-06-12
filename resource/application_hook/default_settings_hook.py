# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import ftrack_api


class DefaultExportSettings(object):
    '''Return default values for export settings.'''

    def __init__(self, session, *args, **kwargs):
        super(DefaultExportSettings, self).__init__(
            *args, **kwargs
        )

        self.session = session

    def get(self, event):
        '''Return default settings.

        The `data` dictionary of the *event* should contain
        nuke studio project called `nuke_studio_project`.

        '''
        nuke_studio_project = event['data']['nuke_studio_project']

        return {
            'resolution': nuke_studio_project.outputFormat(),
            'framerate': str(nuke_studio_project.framerate())
        }

    def register(self):

        '''Register hook.'''
        self.session.event_hub.subscribe(
            'topic=ftrack.connect.nuke-studio.get-default-settings',
            self.get
        )


def register(session, **kw):
    '''Register plugin. Called when used as an plugin.'''
    # Validate that session is an instance of ftrack_api.Session. If not,
    # assume that register is being called from an old or incompatible API and
    # return without doing anything.
    if not isinstance(session, ftrack_api.session.Session):
        return

    plugin = DefaultExportSettings(
        session
    )

    plugin.register()
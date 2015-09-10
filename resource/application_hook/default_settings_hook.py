# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import ftrack


class DefaultExportSettings(object):
    '''Return default values for export settings.'''

    def get(self, event):
        '''Return default settings.

        The `data` dictionary of the *event* should contain
        nuke studio project called `nuke_studio_ project`.

        '''
        nuke_studio_project = event['data']['nuke_studio_project']

        return {
            'resolution': nuke_studio_project.outputFormat(),
            'framerate': str(nuke_studio_project.framerate())
        }

    def register(self):
        '''Register hook.'''
        ftrack.EVENT_HUB.subscribe(
            'topic=ftrack.connect.nuke-studio.get-default-settings',
            self.get
        )


def register(registry, **kw):
    '''Register hooks for default fps setting.'''

    # Validate that registry is instance of ftrack.Registry, if not
    # return early since the register method probably is called
    # from the new API.
    if not isinstance(registry, ftrack.Registry):
        return

    plugin = DefaultExportSettings()
    plugin.register()

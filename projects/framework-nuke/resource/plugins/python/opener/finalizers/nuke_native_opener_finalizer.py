# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

import ftrack_api

from ftrack_connect_pipeline_nuke import plugin
from ftrack_connect_pipeline_nuke import utils as nuke_utils


class NukeNativeOpenerFinalizerPlugin(plugin.NukeOpenerFinalizerPlugin):
    '''Plugin for finalizing the Nuke open process'''

    plugin_name = 'nuke_native_opener_finalizer'

    def run(self, context_data=None, data=None, options=None):
        '''Save opened Nuke script to temp'''

        result = {}

        self.logger.debug('Saving Nuke on open')
        save_path, message = nuke_utils.save_file(
            context_data['context_id'], self.session
        )
        if save_path:
            result['save_path'] = save_path
        else:
            result = False
        self.logger.debug('Initialising Nuke on open')
        nuke_utils.init_nuke(session=self.session)

        return (result, {'message': message})


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = NukeNativeOpenerFinalizerPlugin(api_object)
    plugin.register()
